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
        connection.execute(
            text("ALTER TABLE quiz_questions ADD COLUMN choices TEXT NOT NULL DEFAULT '[]'")
        )


@app.on_event("startup")
async def startup() -> None:
    for attempt in range(1, settings.database_connect_max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_quiz_choices_column()
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
