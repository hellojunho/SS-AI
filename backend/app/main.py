from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .auth import router as auth_router
from .chat import router as chat_router
from .db import Base, engine
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


@app.get("/")
def root():
    return {"status": "ok"}
