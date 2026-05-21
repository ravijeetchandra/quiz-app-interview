import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

try:
    from sqlalchemy.dialects.postgresql import UUID as UUIDType
    UUID_COLUMN = UUIDType(as_uuid=True)
except ImportError:
    from sqlalchemy.types import Uuid as UUIDType
    UUID_COLUMN = UUIDType()


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID_COLUMN, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    quiz_sessions = relationship("QuizSession", back_populates="user", cascade="all, delete-orphan")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(UUID_COLUMN, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID_COLUMN, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    domain = Column(String(100), nullable=False)
    document_name = Column(String(255), nullable=False)
    mcq_count = Column(Integer, nullable=False)
    has_long_questions = Column(Boolean, default=False)
    passing_percentage = Column(Float, default=70.0)
    total_score = Column(Float, nullable=True)
    total_possible = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    section_results = Column(Text, nullable=True)
    is_guest = Column(Boolean, default=False)
    guest_session_id = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="quiz_sessions")
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")
    results = relationship("QuizResult", back_populates="session", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID_COLUMN, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID_COLUMN, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(String(10), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    time_limit_seconds = Column(Integer, nullable=False)

    session = relationship("QuizSession", back_populates="questions")
    answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(UUID_COLUMN, primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID_COLUMN, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID_COLUMN, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    selected_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)
    time_taken = Column(Float, nullable=True)
    timed_out = Column(Boolean, default=False)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    model_answer = Column(Text, nullable=True)

    question = relationship("Question", back_populates="answers")
    session = relationship("QuizSession")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(UUID_COLUMN, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID_COLUMN, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    section_name = Column(String(255), nullable=False)
    score = Column(Float, nullable=False)
    possible = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)

    session = relationship("QuizSession", back_populates="results")
