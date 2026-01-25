import json
import random
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import get_current_user, require_admin
from .db import get_db
from .services import generate_quiz, summarize_chat

router = APIRouter(prefix="/quiz", tags=["quiz"])

BASE_DIR = Path(__file__).resolve().parents[1]
SUMMARY_DIR = BASE_DIR / "chat" / "summation"
RECORD_DIR = BASE_DIR / "chat" / "record"


def _latest_record_file(user_id: str) -> Path | None:
    user_dir = RECORD_DIR / user_id
    if not user_dir.exists():
        return None
    record_files = list(user_dir.glob(f"{user_id}-*.txt"))
    if not record_files:
        return None
    return max(record_files, key=lambda path: path.stat().st_mtime)


def _parse_choices(raw_choices: str) -> list[str]:
    try:
        parsed = json.loads(raw_choices)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


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
        link=quiz.link or "",
        question=question.question,
        choices=_parse_choices(question.choices),
        correct=question.correct,
        wrong=_parse_choices(question.wrong),
        explanation=question.explanation,
        reference=question.reference,
        has_correct_attempt=has_correct_attempt,
        has_wrong_attempt=has_wrong_attempt,
        answer_history=answer_history,
        tried_at=quiz.tried_at,
        solved_at=quiz.solved_at,
    )


def _get_existing_question_texts(db: Session) -> list[str]:
    questions = db.query(models.QuizQuestion.question).all()
    normalized_questions: list[str] = []
    for (question_text,) in questions:
        normalized = _normalize_question_text(question_text or "")
        if normalized:
            normalized_questions.append(normalized)
    return normalized_questions


def _generate_quiz_for_user(target_user: models.User, db: Session) -> models.Quiz:
    record_file = _latest_record_file(target_user.user_id)
    if not record_file or not record_file.exists():
        raise HTTPException(status_code=404, detail="대화 기록이 없습니다.")
    content = record_file.read_text(encoding="utf-8")
    summary_date = datetime.utcnow()
    summary = summarize_chat(content, summary_date)

    existing_questions = _get_existing_question_texts(db)
    attempts = 5
    duplicate_attempts = 0
    invalid_attempts = 0
    quiz_payloads: list[dict[str, object]] = []
    for _ in range(attempts):
        candidate_payloads = generate_quiz(summary)
        for candidate_payload in candidate_payloads:
            if len(quiz_payloads) >= 5:
                break
            question_text = str(candidate_payload.get("question", "") or "")
            normalized_question = _normalize_question_text(question_text)
            if not normalized_question:
                invalid_attempts += 1
                continue
            if any(
                _is_similar_question(existing, normalized_question)
                for existing in existing_questions
            ):
                duplicate_attempts += 1
                continue
            quiz_payloads.append(candidate_payload)
            existing_questions.append(normalized_question)
        if len(quiz_payloads) >= 3:
            break

    if not quiz_payloads:
        if duplicate_attempts and duplicate_attempts + invalid_attempts == attempts:
            raise HTTPException(status_code=409, detail="유사한 문제가 이미 있습니다.")
        raise HTTPException(status_code=500, detail="퀴즈 생성에 실패했습니다.")

    user_summary_dir = SUMMARY_DIR / target_user.user_id
    user_summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = (
        user_summary_dir
        / f"{target_user.user_id}-{summary_date.strftime('%Y-%m-%d-%H%M')}_sum.txt"
    )
    summary_file.write_text(summary, encoding="utf-8")
    summary_record = models.ChatSummary(
        user_id=target_user.id, file_path=str(summary_file), summary_date=summary_date
    )
    db.add(summary_record)

    created_quizzes: list[models.Quiz] = []
    for quiz_payload in quiz_payloads:
        choices = quiz_payload.get("choices", [])
        if not isinstance(choices, list):
            choices = []
        quiz = models.Quiz(
            user_id=target_user.id,
            title="",
            link=str(quiz_payload.get("link", "") or ""),
        )
        question = models.QuizQuestion(
            question=str(quiz_payload.get("question", "") or ""),
            choices=json.dumps(choices, ensure_ascii=False),
            correct=str(quiz_payload.get("correct", "") or ""),
            wrong=json.dumps(quiz_payload.get("wrong", []), ensure_ascii=False),
            explanation=str(quiz_payload.get("explanation", "") or ""),
            reference=str(quiz_payload.get("reference", "") or ""),
            quiz=quiz,
        )
        db.add(quiz)
        db.add(question)
        db.flush()
        quiz.title = f"quiz{quiz.id}"
        if question.correct:
            db.add(
                models.QuizCorrect(
                    quiz_id=quiz.id,
                    quiz_question_id=question.id,
                    answer_text=question.correct,
                )
            )
        wrong_list = quiz_payload.get("wrong", [])
        if isinstance(wrong_list, list):
            for wrong_answer in wrong_list:
                if not wrong_answer:
                    continue
                db.add(
                    models.QuizWrong(
                        quiz_id=quiz.id,
                        quiz_question_id=question.id,
                        answer_text=str(wrong_answer),
                    )
                )
        created_quizzes.append(quiz)
    db.commit()
    for quiz in created_quizzes:
        db.refresh(quiz)
    return created_quizzes[0]


def _shuffle_question_choices(question: models.QuizQuestion) -> bool:
    choices = _parse_choices(question.choices)
    if not choices:
        return False
    random.shuffle(choices)
    question.choices = json.dumps(choices, ensure_ascii=False)
    return True


def _delete_quiz_records(quiz: models.Quiz, db: Session) -> None:
    question_ids = [q.id for q in quiz.questions] if quiz.questions else []
    if question_ids:
        try:
            db.query(models.WrongQuestion).filter(
                models.WrongQuestion.quiz_question_id.in_(question_ids)
            ).delete(synchronize_session=False)
        except Exception:
            pass
    db.delete(quiz)


def _normalize_question_text(text: str) -> str:
    if not text:
        return ""
    stripped = re.sub(r"```json\s*([\s\S]*?)```", r"\1", text, flags=re.IGNORECASE)
    stripped = re.sub(r"```([\s\S]*?)```", r"\1", stripped)
    stripped = stripped.lower()
    stripped = re.sub(r"[^\w\s가-힣]", " ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped


def _is_similar_question(base_text: str, candidate_text: str) -> bool:
    if not base_text or not candidate_text:
        return False
    if base_text == candidate_text:
        return True
    if base_text in candidate_text or candidate_text in base_text:
        shorter = base_text if len(base_text) <= len(candidate_text) else candidate_text
        if len(shorter) >= 12:
            return True
    similarity = SequenceMatcher(None, base_text, candidate_text).ratio()
    return similarity >= 0.9


@router.post("/generate", response_model=schemas.QuizResponse)
def generate_quiz_from_summary(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    quiz = _generate_quiz_for_user(current_user, db)
    return _quiz_to_response(quiz, current_user=current_user, db=db)


@router.post("/admin/generate", response_model=schemas.AdminQuizResponse)
def admin_generate_quiz(
    payload: schemas.AdminQuizGenerateRequest,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target_user = (
        db.query(models.User).filter(models.User.user_id == payload.user_id).first()
    )
    if not target_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    quiz = _generate_quiz_for_user(target_user, db)
    response = _quiz_to_response(quiz, current_user=current_user, db=db)
    return schemas.AdminQuizResponse(**response.model_dump(), source_user_id=target_user.user_id)


@router.post("/admin/generate-all")
def admin_generate_all(
    current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)
):
    users = db.query(models.User).all()
    created = 0
    failed: list[dict[str, str]] = []
    for user in users:
        try:
            _generate_quiz_for_user(user, db)
            created += 1
        except HTTPException as exc:
            # skip users without records or other expected errors
            failed.append({"user_id": user.user_id, "reason": str(exc.detail)})
        except Exception as exc:
            failed.append({"user_id": user.user_id, "reason": str(exc)})
    return {"created": created, "failed": failed}


@router.get("/admin/list", response_model=list[schemas.AdminQuizResponse])
def admin_list_quizzes(
    current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)
):
    quizzes = db.query(models.Quiz).order_by(models.Quiz.created_at.desc()).all()
    results: list[schemas.AdminQuizResponse] = []
    for quiz in quizzes:
        try:
            resp = _quiz_to_response(quiz)
            source_user_id = ""
            if hasattr(quiz, "user") and quiz.user is not None:
                source_user_id = quiz.user.user_id
            results.append(schemas.AdminQuizResponse(**resp.model_dump(), source_user_id=source_user_id))
        except HTTPException:
            # skip quizzes that can't be converted
            continue
    return results


@router.delete("/admin/{quiz_id}")
def admin_delete_quiz(
    quiz_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")
    _delete_quiz_records(quiz, db)
    db.commit()
    return {"deleted": quiz_id}


@router.post("/admin/{quiz_id}/mix", response_model=schemas.AdminQuizResponse)
def admin_mix_quiz_choices(
    quiz_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")
    if not quiz.questions:
        raise HTTPException(status_code=404, detail="퀴즈 문항을 찾을 수 없습니다.")
    question = quiz.questions[0]
    if not _shuffle_question_choices(question):
        raise HTTPException(status_code=400, detail="섞을 선택지가 없습니다.")
    db.commit()
    db.refresh(quiz)
    response = _quiz_to_response(quiz, current_user=current_user, db=db)
    source_user_id = quiz.user.user_id if quiz.user else ""
    return schemas.AdminQuizResponse(**response.model_dump(), source_user_id=source_user_id)


@router.post("/admin/mix-all")
def admin_mix_all_quiz_choices(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    quizzes = db.query(models.Quiz).all()
    mixed = 0
    for quiz in quizzes:
        if not quiz.questions:
            continue
        question = quiz.questions[0]
        if _shuffle_question_choices(question):
            mixed += 1
    db.commit()
    return {"mixed": mixed}


@router.post("/admin/dedupe")
def admin_dedupe_quizzes(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    quizzes = db.query(models.Quiz).order_by(models.Quiz.created_at.asc()).all()
    kept_questions: list[str] = []
    removed_ids: list[int] = []
    for quiz in quizzes:
        if not quiz.questions:
            continue
        question_text = _normalize_question_text(quiz.questions[0].question)
        if not question_text:
            continue
        is_duplicate = any(
            _is_similar_question(existing, question_text) for existing in kept_questions
        )
        if is_duplicate:
            removed_ids.append(quiz.id)
            _delete_quiz_records(quiz, db)
            continue
        kept_questions.append(question_text)
    db.commit()
    return {"removed": len(removed_ids), "removed_ids": removed_ids, "kept": len(kept_questions)}


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


@router.get("/all/first", response_model=schemas.QuizResponse)
def first_quiz_all(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(models.Quiz).order_by(models.Quiz.created_at.asc()).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")
    return _quiz_to_response(quiz, current_user=current_user, db=db)


@router.get("/all/latest", response_model=schemas.QuizResponse)
def latest_quiz_all(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = db.query(models.Quiz).order_by(models.Quiz.created_at.desc()).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")
    return _quiz_to_response(quiz, current_user=current_user, db=db)


@router.get("/next", response_model=schemas.QuizResponse)
def next_quiz(
    current_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(models.Quiz)
        .filter(models.Quiz.user_id == current_user.id, models.Quiz.id > current_id)
        .order_by(models.Quiz.id.asc())
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="다음 퀴즈가 없습니다.")
    return _quiz_to_response(quiz, current_user=current_user, db=db)


@router.get("/all/next", response_model=schemas.QuizResponse)
def next_quiz_all(
    current_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(models.Quiz)
        .filter(models.Quiz.id > current_id)
        .order_by(models.Quiz.id.asc())
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="다음 퀴즈가 없습니다.")
    return _quiz_to_response(quiz, current_user=current_user, db=db)


@router.get("/prev", response_model=schemas.QuizResponse)
def prev_quiz(
    current_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(models.Quiz)
        .filter(models.Quiz.user_id == current_user.id, models.Quiz.id < current_id)
        .order_by(models.Quiz.id.desc())
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="이전 퀴즈가 없습니다.")
    return _quiz_to_response(quiz, current_user=current_user, db=db)


@router.get("/all/prev", response_model=schemas.QuizResponse)
def prev_quiz_all(
    current_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(models.Quiz)
        .filter(models.Quiz.id < current_id)
        .order_by(models.Quiz.id.desc())
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="이전 퀴즈가 없습니다.")
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
