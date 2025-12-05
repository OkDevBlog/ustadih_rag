
"""Exam management endpoints for creating, taking, and grading exams."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import uuid
import json

from app.db.session import SessionLocal
from app.db.models import Exam, Question, ExamAttempt, User
from app.schemas import (
    ExamCreate,
    ExamResponse,
    ExamDetailResponse,
    QuestionCreate,
    QuestionResponse,
    ExamAttemptResponse,
    ExamAttemptStart,
    ExamAttemptSubmit,
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
    return {"status": "ok", "message": "Exams service is running"}


@router.post("/", response_model=ExamResponse)
def create_exam(
    exam_data: ExamCreate,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a new exam (admin only).
    
    Args:
        exam_data: Exam creation data
        user_id: Current user ID (should be admin)
        db: Database session
        
    Returns:
        Created exam
    """
    exam_id = f"exam_{uuid.uuid4().hex[:12]}"
    exam = Exam(
        id=exam_id,
        title=exam_data.title,
        description=exam_data.description,
        subject=exam_data.subject,
        grade_level=exam_data.grade_level,
        total_time_minutes=exam_data.total_time_minutes,
        passing_score=exam_data.passing_score,
        instructions=exam_data.instructions
    )
    
    db.add(exam)
    db.commit()
    db.refresh(exam)
    
    return exam


@router.get("/", response_model=List[ExamResponse])
def list_exams(
    subject: str = None,
    grade_level: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List available exams with optional filters.
    
    Args:
        subject: Filter by subject
        grade_level: Filter by grade level
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        
    Returns:
        List of exams
    """
    query = db.query(Exam)
    
    if subject:
        query = query.filter(Exam.subject == subject)
    if grade_level:
        query = query.filter(Exam.grade_level == grade_level)
    
    exams = query.offset(skip).limit(limit).all()
    return exams


@router.get("/{exam_id}", response_model=ExamDetailResponse)
def get_exam(
    exam_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed exam information with questions.
    
    Args:
        exam_id: Exam ID
        db: Database session
        
    Returns:
        Detailed exam with questions
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    return exam


@router.post("/{exam_id}/questions", response_model=QuestionResponse)
def add_question_to_exam(
    exam_id: str,
    question_data: QuestionCreate,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Add a question to an exam.
    
    Args:
        exam_id: Exam ID
        question_data: Question data
        user_id: Current user ID (should be admin)
        db: Database session
        
    Returns:
        Created question
    """
    # Verify exam exists
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    question_id = f"q_{uuid.uuid4().hex[:12]}"
    question = Question(
        id=question_id,
        exam_id=exam_id,
        question_text=question_data.question_text,
        answer_text=question_data.answer_text,
        question_type=question_data.question_type,
        topic=question_data.topic,
        subject=question_data.subject,
        difficulty_level=question_data.difficulty_level,
        options=question_data.options,
        correct_option=question_data.correct_option
    )
    
    db.add(question)
    
    # Update exam question count
    exam.total_questions += 1
    
    db.commit()
    db.refresh(question)
    
    return question


@router.get("/{exam_id}/questions", response_model=List[QuestionResponse])
def get_exam_questions(
    exam_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all questions for an exam.
    
    Args:
        exam_id: Exam ID
        db: Database session
        
    Returns:
        List of questions
    """
    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    return questions


@router.post("/{exam_id}/attempts/start", response_model=ExamAttemptResponse)
def start_exam_attempt(
    exam_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Start a new exam attempt.
    
    Args:
        exam_id: Exam ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Created exam attempt
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify exam exists
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    attempt_id = f"att_{uuid.uuid4().hex[:12]}"
    attempt = ExamAttempt(
        id=attempt_id,
        user_id=user_id,
        exam_id=exam_id,
        answers={},
        is_completed=False
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    return attempt


@router.post("/{exam_id}/attempts/{attempt_id}/submit", response_model=ExamAttemptResponse)
def submit_exam(
    exam_id: str,
    attempt_id: str,
    submission: ExamAttemptSubmit,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Submit exam answers and calculate score.
    
    Args:
        exam_id: Exam ID
        attempt_id: Exam attempt ID
        submission: Answers submission
        user_id: Current user ID
        db: Database session
        
    Returns:
        Graded exam attempt with score
    """
    # Verify attempt exists and belongs to user
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.user_id == user_id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found"
        )
    
    # Get all questions for the exam
    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    
    # Calculate score
    correct_count = 0
    for question in questions:
        submitted_answer = submission.answers.get(question.id, "")
        
        # Check if answer is correct
        if question.question_type == "multiple_choice":
            if submitted_answer.upper() == question.correct_option:
                correct_count += 1
        else:
            # For short answer/essay, do basic string matching
            if submitted_answer.lower() == question.answer_text.lower():
                correct_count += 1
    
    # Calculate percentage score
    total_questions = len(questions) if questions else 1
    score = (correct_count / total_questions) * 100
    
    # Update attempt
    attempt.answers = submission.answers
    attempt.is_completed = True
    attempt.score = score
    attempt.submitted_at = datetime.utcnow()
    
    # Calculate time taken
    if attempt.started_at:
        duration = datetime.utcnow() - attempt.started_at
        attempt.time_taken_seconds = int(duration.total_seconds())
    
    db.commit()
    db.refresh(attempt)
    
    return attempt


@router.get("/{exam_id}/attempts/{attempt_id}", response_model=ExamAttemptResponse)
def get_exam_attempt(
    exam_id: str,
    attempt_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get exam attempt details and results.
    
    Args:
        exam_id: Exam ID
        attempt_id: Exam attempt ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        Exam attempt with results
    """
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.user_id == user_id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found"
        )
    
    return attempt


@router.get("/user/{user_id}/attempts", response_model=List[ExamAttemptResponse])
def get_user_exam_attempts(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get all exam attempts for a user.
    
    Args:
        user_id: User ID
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        
    Returns:
        List of exam attempts
    """
    attempts = db.query(ExamAttempt).filter(
        ExamAttempt.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    return attempts


@router.post("/{exam_id}/attempts/{attempt_id}/retake")
def retake_exam(
    exam_id: str,
    attempt_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a new attempt for retaking an exam.
    
    Args:
        exam_id: Exam ID
        attempt_id: Previous exam attempt ID
        user_id: Current user ID
        db: Database session
        
    Returns:
        New exam attempt
    """
    # Verify previous attempt exists
    previous_attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id,
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.user_id == user_id
    ).first()
    
    if not previous_attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found"
        )
    
    # Create new attempt
    new_attempt_id = f"att_{uuid.uuid4().hex[:12]}"
    new_attempt = ExamAttempt(
        id=new_attempt_id,
        user_id=user_id,
        exam_id=exam_id,
        answers={},
        is_completed=False
    )
    
    db.add(new_attempt)
    db.commit()
    db.refresh(new_attempt)
    
    return new_attempt
