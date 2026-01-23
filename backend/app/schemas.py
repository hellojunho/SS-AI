from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    user_id: str
    user_name: str
    password: str
    email: EmailStr


class UserLogin(BaseModel):
    user_id: str
    password: str


class UserOut(BaseModel):
    id: int
    user_id: str
    user_name: str
    email: EmailStr
    created_at: datetime
    last_logined: datetime | None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    reference: str
    file_path: str


class SummaryResponse(BaseModel):
    file_path: str
    summary: str


class QuizResponse(BaseModel):
    id: int
    title: str
    question: str
    correct: str
    wrong: str
    explanation: str
    reference: str
    has_correct_attempt: bool = False
    has_wrong_attempt: bool = False
    answer_history: list[str] = []
    tried_at: datetime | None = None
    solved_at: datetime | None = None

    class Config:
        from_attributes = True


class QuizQuestionOut(BaseModel):
    id: int
    quiz_id: int
    question: str
    correct: str
    wrong: str
    explanation: str
    reference: str
    created_at: datetime

    class Config:
        from_attributes = True


class QuizAnswerCreate(BaseModel):
    answer: str


class QuizAnswerResponse(BaseModel):
    quiz_id: int
    question_id: int
    answer: str
    is_correct: bool
    is_wrong: bool
    has_correct_attempt: bool
    has_wrong_attempt: bool
    answer_history: list[str]
    tried_at: datetime | None
    solved_at: datetime | None

    class Config:
        from_attributes = True
