from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

MAX_PASSWORD_BYTES = 1024


def _validate_password_length(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError("Password must be 1024 bytes or fewer.")
    return password


class UserCreate(BaseModel):
    user_id: str
    user_name: str
    password: str
    email: EmailStr

    _password_length = field_validator("password")(_validate_password_length)


class UserLogin(BaseModel):
    user_id: str
    password: str

    _password_length = field_validator("password")(_validate_password_length)


class UserOut(BaseModel):
    id: int
    user_id: str
    user_name: str
    email: EmailStr
    role: str
    created_at: datetime
    last_logined: datetime | None
    is_active: bool
    deactivated_at: datetime | None

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


class ChatHistoryEntry(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    date: str
    entries: list[ChatHistoryEntry]
    is_today: bool


class ChatHistoryDatesResponse(BaseModel):
    dates: list[str]
    today: str


class SummaryResponse(BaseModel):
    file_path: str
    summary: str


class QuizResponse(BaseModel):
    id: int
    title: str
    link: str
    question: str
    choices: list[str]
    correct: str
    wrong: list[str]
    explanation: str
    reference: str
    created_at: datetime | None = None
    has_correct_attempt: bool = False
    has_wrong_attempt: bool = False
    answer_history: list[str] = []
    tried_at: datetime | None = None
    solved_at: datetime | None = None
    current_index: int | None = None
    total_count: int | None = None

    class Config:
        from_attributes = True


class QuizQuestionOut(BaseModel):
    id: int
    quiz_id: int
    question: str
    choices: list[str]
    correct: str
    wrong: list[str]
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


class QuizResultSummary(BaseModel):
    total_count: int
    correct_count: int
    wrong_count: int
    accuracy_rate: float


class WrongNoteQuestion(BaseModel):
    quiz_id: int
    question_id: int
    question: str
    choices: list[str]
    correct: str
    wrong: list[str]
    explanation: str
    reference: str
    link: str


class AdminQuizGenerateRequest(BaseModel):
    user_id: str


class AdminQuizResponse(QuizResponse):
    source_user_id: str


class AdminQuizJobResponse(BaseModel):
    job_id: str


class AdminQuizJobStatus(BaseModel):
    status: str
    progress: int
    result: dict | None = None
    error: str | None = None


class AdminUserUpdate(BaseModel):
    user_name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    password: str | None = None

    _password_length = field_validator("password")(_validate_password_length)


class AdminUserCreate(BaseModel):
    user_id: str
    user_name: str
    password: str
    email: EmailStr
    role: str = "general"

    _password_length = field_validator("password")(_validate_password_length)


class AdminQuizUpdate(BaseModel):
    title: str | None = None
    link: str | None = None
    question: str | None = None
    choices: list[str] | None = None
    correct: str | None = None
    wrong: list[str] | None = None
    explanation: str | None = None
    reference: str | None = None


class AdminTrafficStats(BaseModel):
    period: str
    signups: int
    logins: int
    withdrawals: int
