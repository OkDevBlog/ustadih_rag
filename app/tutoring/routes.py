
"""Tutoring endpoints for RAG-based question answering and tutoring sessions."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid

from app.db.session import SessionLocal
from app.db.models import TutoringSession, User, StudyMaterial
from app.schemas import (
    TutoringSessionStart,
    TutoringSessionQuestion,
    TutoringSessionResponse,
    TutoringSessionDetailResponse,
    RAGAnswer,
    HealthResponse
)
from app.rag.pipeline import get_rag_pipeline
from app.core.security import verify_token

router = APIRouter()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = None, db: Session = Depends(get_db)) -> User:
    """
    Verify token and get current user.
    This is a simplified implementation - enhance with actual JWT validation.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    # In production, implement proper JWT verification
    # For now, token is treated as user_id
    user = db.query(User).filter(User.id == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/ping", response_model=HealthResponse)
def ping():
    """Health check endpoint."""
    return {"status": "ok", "message": "Tutoring service is running"}


@router.post("/sessions/start", response_model=TutoringSessionResponse)
def start_tutoring_session(
    session_data: TutoringSessionStart,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Start a new tutoring session.
    
    Args:
        session_data: Session initialization data
        user_id: Current user ID (from auth token)
        db: Database session
        
    Returns:
        Created tutoring session
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create new tutoring session
    session_id = f"ts_{uuid.uuid4().hex[:12]}"
    tutoring_session = TutoringSession(
        id=session_id,
        user_id=user_id,
        topic=session_data.topic,
        subject=session_data.subject,
        grade=session_data.grade,
        title=session_data.title or f"Tutoring: {session_data.topic}",
        messages=[],
        materials_used=[]
    )
    
    db.add(tutoring_session)
    db.commit()
    db.refresh(tutoring_session)
    
    return tutoring_session


@router.post("/sessions/{session_id}/ask", response_model=RAGAnswer)
def ask_question(
    session_id: str,
    question_data: TutoringSessionQuestion,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Ask a question in an active tutoring session using RAG.
    
    Args:
        session_id: ID of the tutoring session
        question_data: Question and context
        user_id: Current user ID
        db: Database session
        
    Returns:
        RAG-augmented answer with sources
    """
    # Verify session exists and belongs to user
    session = db.query(TutoringSession).filter(
        TutoringSession.id == session_id,
        TutoringSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutoring session not found"
        )
    
    # Get RAG pipeline
    pipeline = get_rag_pipeline()
    
    # Generate answer using RAG
    subject = question_data.subject or session.subject
    topic = question_data.topic or session.topic
    
    # Prefer Markdown query if provided
    used_query = question_data.message_markdown if getattr(question_data, "message_markdown", None) else question_data.message

    rag_result = pipeline.answer_question(
        query=used_query,
        subject=subject,
        user_id=user_id
    )
    
    # Update session with new messages
    messages = session.messages or []
    user_msg = {"role": "user", "content": question_data.message, "timestamp": datetime.utcnow().isoformat()}
    if getattr(question_data, "message_markdown", None):
        user_msg["content_markdown"] = question_data.message_markdown

    assistant_msg = {"role": "assistant", "content": rag_result.get("answer"), "timestamp": datetime.utcnow().isoformat()}
    if rag_result.get("answer_markdown"):
        assistant_msg["content_markdown"] = rag_result.get("answer_markdown")

    messages.append(user_msg)
    messages.append(assistant_msg)
    
    # Track materials used
    materials_used = session.materials_used or []
    for source in rag_result.get("sources", []):
        if source["id"] not in materials_used:
            materials_used.append(source["id"])
    
    session.messages = messages
    session.materials_used = materials_used
    db.commit()
    
    return RAGAnswer(
        query=used_query,
        answer=rag_result.get("answer"),
        answer_markdown=rag_result.get("answer_markdown"),
        sources=rag_result.get("sources", [])
    )


@router.get("/sessions/{session_id}", response_model=TutoringSessionDetailResponse)
def get_tutoring_session(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get tutoring session details.
    
    Args:
        session_id: ID of the tutoring session
        user_id: Current user ID
        db: Database session
        
    Returns:
        Detailed tutoring session
    """
    session = db.query(TutoringSession).filter(
        TutoringSession.id == session_id,
        TutoringSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutoring session not found"
        )
    
    return session


@router.get("/sessions", response_model=List[TutoringSessionResponse])
def list_tutoring_sessions(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all tutoring sessions for a user.
    
    Args:
        user_id: Current user ID
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session
        
    Returns:
        List of tutoring sessions
    """
    sessions = db.query(TutoringSession).filter(
        TutoringSession.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    return sessions


@router.post("/sessions/{session_id}/rate")
def rate_session(
    session_id: str,
    rating: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Rate a tutoring session.
    
    Args:
        session_id: ID of the tutoring session
        rating: Rating 1-5
        user_id: Current user ID
        db: Database session
        
    Returns:
        Updated session
    """
    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    session = db.query(TutoringSession).filter(
        TutoringSession.id == session_id,
        TutoringSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutoring session not found"
        )
    
    session.rating = rating
    db.commit()
    db.refresh(session)
    
    return session


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a tutoring session.
    
    Args:
        session_id: ID of the tutoring session
        user_id: Current user ID
        db: Database session
        
    Returns:
        Success message
    """
    session = db.query(TutoringSession).filter(
        TutoringSession.id == session_id,
        TutoringSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutoring session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}
