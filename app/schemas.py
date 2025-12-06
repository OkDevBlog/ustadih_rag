"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== User Schemas ====================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Study Material Schemas ====================

class StudyMaterialBase(BaseModel):
    title: str
    content: str
    topic: str
    subject: str
    grade: Optional[str] = None
    difficulty_level: str = "intermediate"


class StudyMaterialCreate(StudyMaterialBase):
    pass


class StudyMaterialUpload(BaseModel):
    title: str
    content_markdown: str = Field(..., description="Markdown content to be parsed and stored")
    topic: str
    subject: str
    grade: Optional[str] = None
    difficulty_level: Optional[str] = "intermediate"
    material_id: Optional[str] = None


class StudyMaterialResponse(StudyMaterialBase):
    id: str
    chromadb_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Question Schemas ====================

class QuestionBase(BaseModel):
    question_text: str
    answer_text: str
    topic: str
    subject: str
    question_type: str = "multiple_choice"
    difficulty_level: str = "intermediate"
    options: Optional[List[Dict[str, str]]] = None
    correct_option: Optional[str] = None

    # Optional Markdown variants
    question_markdown: Optional[str] = None
    answer_markdown: Optional[str] = None


class QuestionCreate(QuestionBase):
    exam_id: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: str
    exam_id: Optional[str] = None
    chromadb_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    question_markdown: Optional[str] = None
    answer_markdown: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== Exam Schemas ====================

class ExamBase(BaseModel):
    title: str
    subject: str
    grade_level: str
    description: Optional[str] = None
    total_time_minutes: int = 60
    passing_score: float = 60.0
    instructions: Optional[str] = None


class ExamCreate(ExamBase):
    ministry_question_ids: Optional[List[str]] = None  # List of ministry question IDs to include


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    total_time_minutes: Optional[int] = None
    passing_score: Optional[float] = None


class ExamResponse(ExamBase):
    id: str
    total_questions: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExamDetailResponse(ExamResponse):
    questions: List[QuestionResponse] = []


# ==================== Exam Attempt Schemas ====================

class ExamAttemptStart(BaseModel):
    exam_id: str


class ExamAttemptSubmit(BaseModel):
    exam_id: str
    answers: Dict[str, str]  # {"question_id": "answer_text"}


class ExamAttemptResponse(BaseModel):
    id: str
    user_id: str
    exam_id: str
    score: float
    total_score: float
    is_completed: bool
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


# ==================== Tutoring Session Schemas ====================

class MessageBase(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class TutoringSessionStart(BaseModel):
    topic: str
    subject: str
    grade: Optional[str] = None
    title: Optional[str] = None


class TutoringSessionQuestion(BaseModel):
    message: str
    message_markdown: Optional[str] = None
    topic: Optional[str] = None
    subject: Optional[str] = None


class TutoringSessionMessage(MessageBase):
    timestamp: datetime


class TutoringSessionResponse(BaseModel):
    id: str
    user_id: str
    topic: str
    subject: str
    grade: Optional[str] = None
    title: Optional[str] = None
    messages: List[Dict[str, Any]] = []
    materials_used: List[str] = []
    duration_seconds: Optional[int] = None
    rating: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TutoringSessionDetailResponse(TutoringSessionResponse):
    session_summary: Optional[str] = None


# ==================== RAG Response Schemas ====================

class RAGSource(BaseModel):
    type: str
    id: str
    title: Optional[str] = None


class RAGAnswer(BaseModel):
    query: str
    answer: str
    sources: List[RAGSource] = []
    answer_markdown: Optional[str] = None
    confidence: float = 1.0


# ==================== Ministry Questions Schemas ====================

class MinistryQuestionBase(BaseModel):
    subject: str  # e.g., "Math", "English", "Chemistry"
    grade: str  # e.g., "10", "11", "12"
    year: int  # e.g., 2023, 2024
    session: str  # "first" (دور أول) or "second" (دور ثاني)
    question_text: str
    answer_key: str  # النموذج الإجابة
    question_type: str = "multiple_choice"  # multiple_choice, short_answer, essay
    options: Optional[List[Dict[str, str]]] = None  # [{"id": "A", "text": "..."}, ...]
    correct_option: Optional[str] = None  # "A", "B", "C", "D"
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced
    # Optional Markdown variants
    question_markdown: Optional[str] = None
    answer_key_markdown: Optional[str] = None


class MinistryQuestionCreate(MinistryQuestionBase):
    pass


class MinistryQuestionResponse(MinistryQuestionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    question_markdown: Optional[str] = None
    answer_key_markdown: Optional[str] = None
    
    class Config:
        from_attributes = True


class MinistryQuestionFilter(BaseModel):
    subject: Optional[str] = None
    grade: Optional[str] = None
    year: Optional[int] = None
    session: Optional[str] = None
    difficulty_level: Optional[str] = None


# ==================== Ministry Exam Attempt Schemas ====================

class MinistryExamAttemptStart(BaseModel):
    exam_id: str
    user_id: str


class MinistryExamAnswer(BaseModel):
    ministry_question_id: str
    answer: str


class MinistryExamAttemptSubmit(BaseModel):
    exam_id: str
    user_id: str
    answers: List[MinistryExamAnswer]  # List of question_id: answer pairs


class MinistryExamAttemptResponse(BaseModel):
    id: str
    user_id: str
    exam_id: str
    answers: Dict[str, str]  # {question_id: user_answer}
    scores: Dict[str, float]  # {question_id: score}
    ai_feedback: Dict[str, Dict[str, Any]] = {}  # {question_id: {score: float, feedback: str, confidence: float}}
    total_score: float
    max_score: float
    is_completed: bool
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


# ==================== Auth Schemas ====================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ==================== Health Check ====================

class HealthResponse(BaseModel):
    status: str
    message: str
