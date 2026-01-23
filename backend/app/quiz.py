import json
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


def _quiz_to_response(
    quiz: models.Quiz,
    current_user: models.User | None = None,
    db: Session | None = None,
) -> schemas.QuizResponse:
    if not quiz.questions:
        raise HTTPException(status_code=404, detail="퀴즈 문항을 찾을 수 없습니다.")
    question = quiz.questions[0]
    answer_history: list[str] = []
    has_correct_attempt = False
    has_wrong_attempt = False
    if current_user and db:
        answers = (
            db.query(models.QuizAnswer)
            .filter(
                models.QuizAnswer.quiz_question_id == question.id,
                models.QuizAnswer.user_id == current_user.id,
            )
            .order_by(models.QuizAnswer.created_at.asc())
            .all()
        )
        answer_history = [answer.answer_text for answer in answers]
        has_correct_attempt = any(answer.is_correct for answer in answers)
        has_wrong_attempt = any(answer.is_wrong for answer in answers)
    return schemas.QuizResponse(
        id=quiz.id,
        title=quiz.title,
        question=question.question,
        correct=question.correct,
        wrong=question.wrong,
        explanation=question.explanation,
        reference=question.reference,
        has_correct_attempt=has_correct_attempt,
        has_wrong_attempt=has_wrong_attempt,
        answer_history=answer_history,
        tried_at=quiz.tried_at,
        solved_at=quiz.solved_at,
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
    return _quiz_to_response(quiz, current_user=current_user, db=db)


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
    return _quiz_to_response(quiz, current_user=current_user, db=db)


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
    return _quiz_to_response(quiz, current_user=current_user, db=db)


@router.post("/{quiz_id}/answer", response_model=schemas.QuizAnswerResponse)
def submit_quiz_answer(
    quiz_id: int,
    payload: schemas.QuizAnswerCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")
    if not quiz.questions:
        raise HTTPException(status_code=404, detail="퀴즈 문항을 찾을 수 없습니다.")
    question = quiz.questions[0]
    normalized_answer = payload.answer.strip()
    is_correct = normalized_answer == question.correct.strip()
    is_wrong = not is_correct
    answer_record = models.QuizAnswer(
        quiz_question_id=question.id,
        user_id=current_user.id,
        answer_text=normalized_answer,
        is_correct=is_correct,
        is_wrong=is_wrong,
    )
    db.add(answer_record)
    now = datetime.utcnow()
    quiz.tried_at = now
    if is_correct:
        quiz.solved_at = now
    if is_wrong:
        wrong_record = (
            db.query(models.WrongQuestion)
            .filter(
                models.WrongQuestion.quiz_question_id == question.id,
                models.WrongQuestion.solver_user_id == current_user.id,
            )
            .first()
        )
        if wrong_record:
            try:
                history = json.loads(wrong_record.user_answers)
            except json.JSONDecodeError:
                history = []
            history.append(normalized_answer)
            wrong_record.user_answers = json.dumps(history, ensure_ascii=False)
            wrong_record.last_solved_at = now
        else:
            wrong_record = models.WrongQuestion(
                quiz_question_id=question.id,
                question_creator_id=quiz.user_id,
                solver_user_id=current_user.id,
                correct_answer=question.correct,
                wrong_answer=question.wrong,
                reference_link=question.reference,
                user_answers=json.dumps([normalized_answer], ensure_ascii=False),
                last_solved_at=now,
            )
            db.add(wrong_record)
    db.commit()
    answer_history = (
        db.query(models.QuizAnswer)
        .filter(
            models.QuizAnswer.quiz_question_id == question.id,
            models.QuizAnswer.user_id == current_user.id,
        )
        .order_by(models.QuizAnswer.created_at.asc())
        .all()
    )
    history_values = [answer.answer_text for answer in answer_history]
    has_correct_attempt = any(answer.is_correct for answer in answer_history)
    has_wrong_attempt = any(answer.is_wrong for answer in answer_history)
    return schemas.QuizAnswerResponse(
        quiz_id=quiz.id,
        question_id=question.id,
        answer=normalized_answer,
        is_correct=is_correct,
        is_wrong=is_wrong,
        has_correct_attempt=has_correct_attempt,
        has_wrong_attempt=has_wrong_attempt,
        answer_history=history_values,
        tried_at=quiz.tried_at,
        solved_at=quiz.solved_at,
    )
