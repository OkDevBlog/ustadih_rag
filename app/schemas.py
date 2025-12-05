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
    difficulty_level: str = "intermediate"


class StudyMaterialCreate(StudyMaterialBase):
    pass


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


class QuestionCreate(QuestionBase):
    exam_id: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: str
    exam_id: Optional[str] = None
    chromadb_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
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
    pass


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
    title: Optional[str] = None


class TutoringSessionQuestion(BaseModel):
    message: str
    topic: Optional[str] = None
    subject: Optional[str] = None


class TutoringSessionMessage(MessageBase):
    timestamp: datetime


class TutoringSessionResponse(BaseModel):
    id: str
    user_id: str
    topic: str
    subject: str
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
    confidence: float = 1.0


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
