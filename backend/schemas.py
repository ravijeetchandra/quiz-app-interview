from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import uuid


# Auth
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Quiz config
class QuizConfig(BaseModel):
    domain: str
    mcq_count: int = Field(default=10, ge=1, le=20)
    has_long_questions: bool = False
    passing_percentage: float = Field(default=70.0, ge=0, le=100)


class QuizStart(BaseModel):
    domain: str
    mcq_count: int = Field(default=10, ge=1, le=20)
    has_long_questions: bool = False
    passing_percentage: float = Field(default=70.0, ge=0, le=100)


# Quiz response
class QuestionOut(BaseModel):
    id: uuid.UUID
    question_type: str
    question_text: str
    options: Optional[str]
    order: int
    time_limit_seconds: int

    model_config = {"from_attributes": True}


class QuizSessionOut(BaseModel):
    id: uuid.UUID
    domain: str
    document_name: str
    mcq_count: int
    has_long_questions: bool
    passing_percentage: float
    questions: List[QuestionOut]
    started_at: datetime

    model_config = {"from_attributes": True}


# Answer submission
class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    selected_answer: Optional[str] = None
    time_taken: float = 0.0
    timed_out: bool = False


class QuizSubmit(BaseModel):
    answers: List[AnswerSubmit]


# Results
class AnswerResult(BaseModel):
    question_id: uuid.UUID
    question_text: str
    question_type: str
    your_answer: Optional[str]
    correct_answer: str
    is_correct: Optional[bool]
    score: Optional[float]
    time_taken: float
    timed_out: bool
    strengths: Optional[str]
    weaknesses: Optional[str]
    model_answer: Optional[str]


class SectionResult(BaseModel):
    section_name: str
    score: float
    possible: float
    percentage: float


class QuizResultOut(BaseModel):
    session_id: uuid.UUID
    domain: str
    document_name: str
    total_score: float
    total_possible: float
    percentage: float
    passed: bool
    passing_percentage: float
    answer_results: List[AnswerResult]
    section_results: List[SectionResult]
    completed_at: Optional[datetime]


class QuizHistoryItem(BaseModel):
    id: uuid.UUID
    domain: str
    document_name: str
    mcq_count: int
    has_long_questions: bool
    percentage: float
    passed: bool
    started_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class UserDashboard(BaseModel):
    total_quizzes: int
    average_score: float
    best_score: float
    quizzes_by_domain: List[dict]
    recent_quizzes: List[QuizHistoryItem]
    score_trend: List[dict]
