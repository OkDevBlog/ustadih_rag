
"""User management endpoints for profile, progress tracking, and preferences."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.session import SessionLocal
from app.db.models import User, ExamAttempt, TutoringSession, Exam
from app.schemas import (
    UserResponse,
    UserUpdate,
    ExamAttemptResponse,
    TutoringSessionResponse,
    HealthResponse
)

router = APIRouter()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ping", response_model=HealthResponse)
def ping():
    """Health check endpoint."""
    return {"status": "ok", "message": "Users service is running"}


@router.get("/{user_id}", response_model=UserResponse)
def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user profile information.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        User profile data
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user_profile(
    user_id: str,
    update_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user profile information.
    
    Args:
        user_id: User ID
        update_data: Updated user data
        db: Database session
        
    Returns:
        Updated user profile
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if update_data.full_name:
        user.full_name = update_data.full_name
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/{user_id}/learning-progress")
def get_learning_progress(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user's learning progress and statistics.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Learning progress statistics
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get exam statistics
    exam_attempts = db.query(ExamAttempt).filter(
        ExamAttempt.user_id == user_id,
        ExamAttempt.is_completed == True
    ).all()
    
    tutoring_sessions = db.query(TutoringSession).filter(
        TutoringSession.user_id == user_id
    ).all()
    
    # Calculate statistics
    total_exams_taken = len(exam_attempts)
    avg_exam_score = 0
    exams_passed = 0
    
    if exam_attempts:
        scores = [att.score for att in exam_attempts]
        avg_exam_score = sum(scores) / len(scores)
        exams_passed = sum(1 for att in exam_attempts if att.score >= 60)
    
    # Calculate average session rating
    session_ratings = [s.rating for s in tutoring_sessions if s.rating]
    avg_session_rating = sum(session_ratings) / len(session_ratings) if session_ratings else 0
    
    # Group exams by subject
    exams_by_subject = {}
    for attempt in exam_attempts:
        subject = attempt.exam.subject
        if subject not in exams_by_subject:
            exams_by_subject[subject] = {
                "total": 0,
                "passed": 0,
                "average_score": 0
            }
        exams_by_subject[subject]["total"] += 1
        if attempt.score >= 60:
            exams_by_subject[subject]["passed"] += 1
    
    # Calculate average by subject
    for subject in exams_by_subject:
        subject_attempts = [a for a in exam_attempts if a.exam.subject == subject]
        if subject_attempts:
            avg = sum(a.score for a in subject_attempts) / len(subject_attempts)
            exams_by_subject[subject]["average_score"] = avg
    
    return {
        "user_id": user_id,
        "total_exams_taken": total_exams_taken,
        "exams_passed": exams_passed,
        "average_exam_score": round(avg_exam_score, 2),
        "total_tutoring_sessions": len(tutoring_sessions),
        "average_session_rating": round(avg_session_rating, 2),
        "exams_by_subject": exams_by_subject,
        "last_activity": max(
            (max((a.submitted_at or a.started_at for a in exam_attempts), default=None) or datetime.min),
            (max((s.updated_at for s in tutoring_sessions), default=None) or datetime.min)
        ).isoformat() if (exam_attempts or tutoring_sessions) else None
    }


@router.get("/{user_id}/exam-history", response_model=List[ExamAttemptResponse])
def get_exam_history(
    user_id: str,
    subject: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get user's exam history.
    
    Args:
        user_id: User ID
        subject: Optional filter by subject
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        
    Returns:
        List of exam attempts
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    query = db.query(ExamAttempt).filter(ExamAttempt.user_id == user_id)
    
    if subject:
        query = query.join(ExamAttempt.exam).filter(Exam.subject == subject)
    
    attempts = query.order_by(ExamAttempt.submitted_at.desc()).offset(skip).limit(limit).all()
    
    return attempts


@router.get("/{user_id}/tutoring-history", response_model=List[TutoringSessionResponse])
def get_tutoring_history(
    user_id: str,
    subject: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get user's tutoring history.
    
    Args:
        user_id: User ID
        subject: Optional filter by subject
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        
    Returns:
        List of tutoring sessions
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    query = db.query(TutoringSession).filter(TutoringSession.user_id == user_id)
    
    if subject:
        query = query.filter(TutoringSession.subject == subject)
    
    sessions = query.order_by(TutoringSession.updated_at.desc()).offset(skip).limit(limit).all()
    
    return sessions


@router.delete("/{user_id}")
def delete_user_account(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete user account and associated data.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Success message
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user (cascade will handle related data)
    db.delete(user)
    db.commit()
    
    return {"message": "User account deleted successfully"}
