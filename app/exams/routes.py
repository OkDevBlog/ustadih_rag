
"""Exam management endpoints for creating, taking, and grading exams."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
import json

from app.db.session import SessionLocal
from app.db.models import Exam, Question, ExamAttempt, User, MinistryExamAttempt
from app.db.session import engine
from sqlalchemy import inspect, text
from app.schemas import (
    ExamCreate,
    ExamResponse,
    ExamDetailResponse,
    QuestionCreate,
    QuestionResponse,
    ExamAttemptResponse,
    ExamAttemptStart,
    ExamAttemptSubmit,
    HealthResponse,
    MinistryQuestionCreate,
    MinistryQuestionResponse,
    MinistryQuestionFilter,
    MinistryExamAttemptSubmit,
    MinistryExamAttemptResponse
)
from app.db.models import MinistryQuestion
from app.rag.pipeline import get_rag_pipeline

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
    Optionally link ministry questions if ministry_question_ids provided.
    
    Args:
        exam_data: Exam creation data (can include ministry_question_ids)
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
    
    # Add ministry questions if provided
    if exam_data.ministry_question_ids:
        ministry_questions = db.query(MinistryQuestion).filter(
            MinistryQuestion.id.in_(exam_data.ministry_question_ids)
        ).all()
        
        if ministry_questions:
            exam.ministry_questions = ministry_questions
            exam.total_questions = len(ministry_questions)
    
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
    
    # Prefer Markdown fields if provided
    q_text = question_data.question_markdown if getattr(question_data, "question_markdown", None) else question_data.question_text
    a_text = question_data.answer_markdown if getattr(question_data, "answer_markdown", None) else question_data.answer_text

    question_id = f"q_{uuid.uuid4().hex[:12]}"
    question = Question(
        id=question_id,
        exam_id=exam_id,
        question_text=q_text,
        answer_text=a_text,
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

    # Attach transient markdown attributes for response (if any)
    try:
        question.question_markdown = question_data.question_markdown if getattr(question_data, "question_markdown", None) else None
        question.answer_markdown = question_data.answer_markdown if getattr(question_data, "answer_markdown", None) else None
    except Exception:
        pass
    
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


# ==================== Ministry Questions Endpoints ====================

@router.post("/ministry-questions/", response_model=MinistryQuestionResponse, status_code=status.HTTP_201_CREATED)
def add_ministry_question(
    question_data: MinistryQuestionCreate,
    user_id: str = None,  # Optional for now, can be used for tracking who added it
    db: Session = Depends(get_db)
):
    """
    Add a ministry question to the database.
    
    Args:
        question_data: Ministry question data including subject, grade, year, session
        user_id: Current user ID (optional)
        db: Database session
        
    Returns:
        Created ministry question
    """
    question_id = f"mq_{uuid.uuid4().hex[:12]}"
    
    mq_text = question_data.question_markdown if getattr(question_data, "question_markdown", None) else question_data.question_text
    ak_text = question_data.answer_key_markdown if getattr(question_data, "answer_key_markdown", None) else question_data.answer_key

    ministry_question = MinistryQuestion(
        id=question_id,
        subject=question_data.subject,
        grade=question_data.grade,
        year=question_data.year,
        session=question_data.session,
        question_text=mq_text,
        answer_key=ak_text,
        question_type=question_data.question_type,
        options=question_data.options,
        correct_option=question_data.correct_option,
        difficulty_level=question_data.difficulty_level
    )
    
    db.add(ministry_question)
    db.commit()
    db.refresh(ministry_question)

    try:
        ministry_question.question_markdown = question_data.question_markdown if getattr(question_data, "question_markdown", None) else None
        ministry_question.answer_key_markdown = question_data.answer_key_markdown if getattr(question_data, "answer_key_markdown", None) else None
    except Exception:
        pass
    
    return ministry_question


@router.get("/ministry-questions/", response_model=List[MinistryQuestionResponse])
def list_ministry_questions(
    subject: str = None,
    grade: str = None,
    year: int = None,
    session: str = None,
    difficulty_level: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Retrieve ministry questions with optional filters.
    
    Args:
        subject: Filter by subject (e.g., "Math", "English")
        grade: Filter by grade (e.g., "10", "11", "12")
        year: Filter by year (e.g., 2023, 2024)
        session: Filter by session ("first" or "second")
        difficulty_level: Filter by difficulty level
        skip: Pagination offset
        limit: Pagination limit
        db: Database session
        
    Returns:
        List of ministry questions matching filters
    """
    query = db.query(MinistryQuestion)
    
    if subject:
        query = query.filter(MinistryQuestion.subject == subject)
    if grade:
        query = query.filter(MinistryQuestion.grade == grade)
    if year:
        query = query.filter(MinistryQuestion.year == year)
    if session:
        query = query.filter(MinistryQuestion.session == session)
    if difficulty_level:
        query = query.filter(MinistryQuestion.difficulty_level == difficulty_level)
    
    questions = query.offset(skip).limit(limit).all()
    return questions


@router.get("/ministry-questions/{question_id}", response_model=MinistryQuestionResponse)
def get_ministry_question(
    question_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific ministry question by ID.
    
    Args:
        question_id: Ministry question ID
        db: Database session
        
    Returns:
        Ministry question details
    """
    question = db.query(MinistryQuestion).filter(MinistryQuestion.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ministry question not found"
        )
    
    return question


@router.delete("/ministry-questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ministry_question(
    question_id: str,
    user_id: str = None,  # Optional, for admin-only access in future
    db: Session = Depends(get_db)
):
    """
    Delete a ministry question.
    
    Args:
        question_id: Ministry question ID
        user_id: Current user ID (optional, for future admin checks)
        db: Database session
    """
    question = db.query(MinistryQuestion).filter(MinistryQuestion.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ministry question not found"
        )
    
    db.delete(question)
    db.commit()
    
    return None


# ==================== Exam Creation from Ministry Questions ====================

class CreateExamFromMinistryRequest(BaseModel):
    """Request model for creating exam from ministry questions."""
    title: str
    description: Optional[str] = None
    total_time_minutes: int = 60
    passing_score: float = 60.0
    instructions: Optional[str] = None
    ministry_question_ids: List[str]  # List of ministry question IDs to include


@router.post("/from-ministry-questions", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam_from_ministry_questions(
    request_data: CreateExamFromMinistryRequest,
    user_id: str = None,  # Optional for now
    db: Session = Depends(get_db)
):
    """
    Create a new exam using selected ministry questions.
    
    Args:
        request_data: Contains exam details and list of ministry_question_ids
        user_id: Current user ID (optional)
        db: Database session
        
    Returns:
        Created exam with linked ministry questions
    """
    # Verify all ministry questions exist
    ministry_questions = db.query(MinistryQuestion).filter(
        MinistryQuestion.id.in_(request_data.ministry_question_ids)
    ).all()
    
    if not ministry_questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ministry questions found with provided IDs"
        )
    
    if len(ministry_questions) != len(request_data.ministry_question_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some ministry question IDs do not exist"
        )
    
    # Determine subject and grade from first question (they should be consistent)
    first_question = ministry_questions[0]
    exam_id = f"exam_{uuid.uuid4().hex[:12]}"
    
    exam = Exam(
        id=exam_id,
        title=request_data.title,
        description=request_data.description,
        subject=first_question.subject,
        grade_level=first_question.grade,
        total_questions=len(ministry_questions),
        total_time_minutes=request_data.total_time_minutes,
        passing_score=request_data.passing_score,
        instructions=request_data.instructions,
        ministry_questions=ministry_questions
    )
    
    db.add(exam)
    db.commit()
    db.refresh(exam)
    
    return exam


@router.get("/from-ministry/{exam_id}/questions", response_model=List[MinistryQuestionResponse])
def get_exam_ministry_questions(
    exam_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all ministry questions linked to an exam.
    
    Args:
        exam_id: Exam ID
        db: Database session
        
    Returns:
        List of ministry questions in the exam
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    return exam.ministry_questions


# ==================== Ministry Exam Answering ====================

@router.post("/ministry/{exam_id}/start", response_model=MinistryExamAttemptResponse, status_code=status.HTTP_201_CREATED)
def start_ministry_exam_attempt(
    exam_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Start a new attempt on a ministry exam.
    
    Args:
        exam_id: Exam ID
        user_id: User ID
        db: Database session
        
    Returns:
        New exam attempt with empty answers
    """
    try:
        # Verify exam exists
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found"
            )

        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Ensure DB has ai_feedback column for ministry_exam_attempts
        try:
            inspector = inspect(engine)
            cols = [c['name'] for c in inspector.get_columns('ministry_exam_attempts')]
            if 'ai_feedback' not in cols:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("ALTER TABLE ministry_exam_attempts ADD COLUMN ai_feedback JSON DEFAULT '{}'"))
                    print('Added missing column ai_feedback to ministry_exam_attempts')
                except Exception as e:
                    print(f'Warning: failed to add ai_feedback column: {e}')
        except Exception:
            # If inspection fails, continue and rely on models (may raise later)
            pass

        # Create new attempt
        attempt_id = f"mea_{uuid.uuid4().hex[:12]}"
        attempt = MinistryExamAttempt(
            id=attempt_id,
            user_id=user_id,
            exam_id=exam_id,
            answers={},
            scores={},
            max_score=len(exam.ministry_questions) * 1.0 if exam.ministry_questions else 100.0
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return attempt
    except HTTPException:
        # Re-raise HTTPExceptions so FastAPI can handle them normally
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Error in start_ministry_exam_attempt: {e}\n{tb}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ministry/{exam_id}/submit", response_model=MinistryExamAttemptResponse)
def submit_ministry_exam_answers(
    exam_id: str,
    attempt_data: MinistryExamAttemptSubmit,
    db: Session = Depends(get_db)
):
    """
    Submit answers for a ministry exam and get scored results.
    Automatically grades multiple choice questions and tracks answers.
    
    Args:
        exam_id: Exam ID
        attempt_data: Contains user_id and list of answers
        db: Database session
        
    Returns:
        Updated attempt with scores and total score
    """
    # Get the attempt
    attempt = db.query(MinistryExamAttempt).filter(
        MinistryExamAttempt.exam_id == exam_id,
        MinistryExamAttempt.user_id == attempt_data.user_id,
        MinistryExamAttempt.is_completed == False
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active exam attempt not found"
        )
    
    # Get the exam and its questions
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or not exam.ministry_questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam or questions not found"
        )
    
    # Create a map of question IDs to questions for quick lookup
    questions_map = {q.id: q for q in exam.ministry_questions}
    
    # Process answers and calculate scores
    total_score = 0.0
    scores_dict = {}
    answers_dict = {}
    
    for answer_item in attempt_data.answers:
        question_id = answer_item.ministry_question_id
        user_answer = answer_item.answer
        
        if question_id not in questions_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {question_id} not in this exam"
            )
        
        question = questions_map[question_id]
        answers_dict[question_id] = user_answer
        
        # Score the answer
        score = 0.0
        if question.question_type == "multiple_choice":
            # Auto-grade multiple choice
            if user_answer.upper() == question.correct_option.upper():
                score = 1.0
        else:
            # For short answer and essay, use the pipeline.grade_answer helper
            score = 0.0
            try:
                pipeline = get_rag_pipeline()
                grade_result = pipeline.grade_answer(
                    question_text=question.question_text,
                    model_answer=question.answer_key,
                    student_answer=user_answer,
                    subject=getattr(question, 'subject', None),
                    max_score=1.0,
                )

                # grade_result includes: score, feedback, confidence, raw
                score = float(grade_result.get('score', 0.0))

                if 'ai_tmp_feedback' not in locals():
                    ai_tmp_feedback = {}
                ai_tmp_feedback[question_id] = {
                    "score": score,
                    "feedback": grade_result.get('feedback', ""),
                    "confidence": grade_result.get('confidence', 0.0),
                    "raw": grade_result.get('raw', "")
                }
            except Exception:
                # On error, keep score 0.0 and continue
                score = 0.0
        
        scores_dict[question_id] = score
        total_score += score
    
    # Update attempt
    attempt.answers = answers_dict
    attempt.scores = scores_dict
    attempt.total_score = total_score
    attempt.is_completed = True
    attempt.submitted_at = datetime.utcnow()
    # Attach AI feedback if generated
    if 'ai_tmp_feedback' in locals():
        attempt.ai_feedback = ai_tmp_feedback
    
    # Calculate time taken if needed
    if attempt.started_at:
        time_delta = datetime.utcnow() - attempt.started_at
        attempt.time_taken_seconds = int(time_delta.total_seconds())
    
    db.commit()
    db.refresh(attempt)
    
    return attempt


@router.get("/ministry/{exam_id}/attempts", response_model=List[MinistryExamAttemptResponse])
def get_ministry_exam_attempts(
    exam_id: str,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get exam attempts for a ministry exam.
    Optionally filter by specific user.
    
    Args:
        exam_id: Exam ID
        user_id: Optional user ID to filter attempts
        db: Database session
        
    Returns:
        List of exam attempts
    """
    query = db.query(MinistryExamAttempt).filter(MinistryExamAttempt.exam_id == exam_id)
    
    if user_id:
        query = query.filter(MinistryExamAttempt.user_id == user_id)
    
    attempts = query.all()
    return attempts


@router.get("/ministry/{exam_id}/attempts/{attempt_id}", response_model=MinistryExamAttemptResponse)
def get_ministry_exam_attempt(
    exam_id: str,
    attempt_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific exam attempt with detailed results.
    
    Args:
        exam_id: Exam ID
        attempt_id: Attempt ID
        db: Database session
        
    Returns:
        Exam attempt with answers and scores
    """
    attempt = db.query(MinistryExamAttempt).filter(
        MinistryExamAttempt.id == attempt_id,
        MinistryExamAttempt.exam_id == exam_id
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam attempt not found"
        )
    
    return attempt