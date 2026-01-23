from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import models
from .auth import router as auth_router
from .chat import router as chat_router
from .db import Base, engine
from .logging_utils import log_error
from .quiz import router as quiz_router

app = FastAPI(title="SS-AI Sports Science")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(quiz_router)


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
