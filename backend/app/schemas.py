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
    token_type: str = "bearer"


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
