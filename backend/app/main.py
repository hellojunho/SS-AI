import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from . import models
from .auth import router as auth_router
from .chat import router as chat_router
from .config import settings
from .db import Base, engine
from .logging_utils import log_error
from .quiz import router as quiz_router
from .security import hash_password

app = FastAPI(title="SS-AI Sports Science")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(quiz_router)

def _ensure_quiz_choices_column() -> None:
    inspector = inspect(engine)
    if "quiz_questions" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("quiz_questions")}
    if "choices" in columns:
        return
    with engine.begin() as connection:
        # Add column without a TEXT default (MySQL doesn't allow defaults for TEXT/JSON)
        connection.execute(text("ALTER TABLE quiz_questions ADD COLUMN choices TEXT"))
        # Initialize existing rows with an empty array representation
        connection.execute(text("UPDATE quiz_questions SET choices = '[]' WHERE choices IS NULL"))
        # Make the column NOT NULL now that values are initialized
        connection.execute(text("ALTER TABLE quiz_questions MODIFY COLUMN choices TEXT NOT NULL"))


def _ensure_users_role_column() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" in columns:
        return
    with engine.begin() as connection:
        # VARCHAR can have a default in MySQL, so add it with default and NOT NULL
        connection.execute(
            text("ALTER TABLE users ADD COLUMN `role` VARCHAR(20) NOT NULL DEFAULT 'general'")
        )


def _ensure_admin_user() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    with engine.begin() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM users WHERE user_id = :uid LIMIT 1"),
            {"uid": "admin"},
        ).first()
        if exists:
            return
        # Create admin user with hashed password 'admin'
        pw_hash = hash_password("admin")
        connection.execute(
            text(
                "INSERT INTO users (user_id, user_name, password_hash, email, role, created_at, token) VALUES (:user_id, :user_name, :password_hash, :email, :role, NOW(), :token)"
            ),
            {
                "user_id": "admin",
                "user_name": "admin",
                "password_hash": pw_hash,
                "email": "admin@example.com",
                "role": "admin",
                "token": 0,
            },
        )


@app.on_event("startup")
async def startup() -> None:
    for attempt in range(1, settings.database_connect_max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_quiz_choices_column()
            _ensure_users_role_column()
            _ensure_admin_user()
            return
        except Exception:
            if attempt == settings.database_connect_max_retries:
                raise
            await asyncio.sleep(settings.database_connect_retry_seconds)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    log_error(request, exc, status_code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log_error(request, exc, status_code=500)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/")
def root():
    return {"status": "ok"}
