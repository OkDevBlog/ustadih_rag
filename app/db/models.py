from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    google_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exam_attempts = relationship("ExamAttempt", back_populates="user", cascade="all, delete-orphan")
    tutoring_sessions = relationship("TutoringSession", back_populates="user", cascade="all, delete-orphan")


class StudyMaterial(Base):
    __tablename__ = "study_materials"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    topic = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False, index=True)
    difficulty_level = Column(String, default="intermediate")  # beginner, intermediate, advanced
    chromadb_id = Column(String, nullable=True)  # Reference to ChromaDB embedding
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True, index=True)
    exam_id = Column(String, ForeignKey("exams.id"), nullable=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    question_type = Column(String, default="multiple_choice")  # multiple_choice, short_answer, essay
    topic = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False, index=True)
    difficulty_level = Column(String, default="intermediate")
    options = Column(JSON, nullable=True)  # For multiple choice: [{"id": "A", "text": "..."}, ...]
    correct_option = Column(String, nullable=True)  # For multiple choice
    chromadb_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exam = relationship("Exam", back_populates="questions")


class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    subject = Column(String, nullable=False, index=True)
    grade_level = Column(String, nullable=False)  # e.g., "Grade 10", "Secondary"
    total_questions = Column(Integer, default=0)
    total_time_minutes = Column(Integer, default=60)
    passing_score = Column(Float, default=60.0)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    exam_id = Column(String, ForeignKey("exams.id"), nullable=False, index=True)
    score = Column(Float, default=0.0)
    total_score = Column(Float, default=100.0)
    answers = Column(JSON, nullable=True)  # {"question_id": "answer_text", ...}
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="exam_attempts")
    exam = relationship("Exam", back_populates="attempts")


class TutoringSession(Base):
    __tablename__ = "tutoring_sessions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    messages = Column(JSON, default=list)  # [{"role": "user/assistant", "content": "...", "timestamp": "..."}, ...]
    materials_used = Column(JSON, default=list)  # ["material_id_1", "material_id_2", ...]
    session_summary = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tutoring_sessions")
