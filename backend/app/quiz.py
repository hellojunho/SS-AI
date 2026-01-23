from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import get_current_user
from .db import get_db
from .services import generate_quiz

router = APIRouter(prefix="/quiz", tags=["quiz"])

BASE_DIR = Path(__file__).resolve().parents[1]
SUMMARY_DIR = BASE_DIR / "chat" / "summation"


def _quiz_to_response(quiz: models.Quiz) -> schemas.QuizResponse:
    if not quiz.questions:
        raise HTTPException(status_code=404, detail="퀴즈 문항을 찾을 수 없습니다.")
    question = quiz.questions[0]
    return schemas.QuizResponse(
        id=quiz.id,
        title=quiz.title,
        question=question.question,
        correct=question.correct,
        wrong=question.wrong,
        explanation=question.explanation,
        reference=question.reference,
    )


@router.post("/generate", response_model=schemas.QuizResponse)
def generate_quiz_from_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    summary_file = SUMMARY_DIR / current_user.user_id / f"{current_user.user_id}-{date_str}_sum.txt"
    if not summary_file.exists():
        raise HTTPException(status_code=404, detail="요약 파일이 없습니다.")
    summary = summary_file.read_text(encoding="utf-8")
    quiz_payload = generate_quiz(summary)
    quiz = models.Quiz(user_id=current_user.id, title="")
    question = models.QuizQuestion(
        question=quiz_payload.get("question", ""),
        correct=quiz_payload.get("correct", ""),
        wrong=quiz_payload.get("wrong", ""),
        explanation=quiz_payload.get("explanation", ""),
        reference=quiz_payload.get("reference", ""),
        quiz=quiz,
    )
    db.add(quiz)
    db.add(question)
    db.commit()
    db.refresh(quiz)
    quiz.title = f"quiz{quiz.id}"
    db.commit()
    db.refresh(quiz)
    return _quiz_to_response(quiz)


@router.get("/latest", response_model=schemas.QuizResponse)
def latest_quiz(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(models.Quiz)
        .filter(models.Quiz.user_id == current_user.id)
        .order_by(models.Quiz.created_at.desc())
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")
    return _quiz_to_response(quiz)


@router.get("/{quiz_id}", response_model=schemas.QuizResponse)
def get_quiz(
    quiz_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(models.Quiz).filter(
        models.Quiz.id == quiz_id, models.Quiz.user_id == current_user.id
    ).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")
    return _quiz_to_response(quiz)
