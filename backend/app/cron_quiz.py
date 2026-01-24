import json
from datetime import datetime
from pathlib import Path

from . import models
from .db import SessionLocal
from .services import generate_quiz, summarize_chat

BASE_DIR = Path(__file__).resolve().parents[1]
RECORD_DIR = BASE_DIR / "chat" / "record"
SUMMARY_DIR = BASE_DIR / "chat" / "summation"


def _latest_record_file(user_id: str) -> Path | None:
    user_dir = RECORD_DIR / user_id
    if not user_dir.exists():
        return None
    record_files = list(user_dir.glob(f"{user_id}-*.txt"))
    if not record_files:
        return None
    return max(record_files, key=lambda path: path.stat().st_mtime)


def run_quiz_job() -> None:
    if not RECORD_DIR.exists():
        return
    db = SessionLocal()
    try:
        for user_dir in RECORD_DIR.iterdir():
            if not user_dir.is_dir():
                continue
            user_id = user_dir.name
            user = db.query(models.User).filter(models.User.user_id == user_id).first()
            if not user:
                continue
            record_file = _latest_record_file(user_id)
            if not record_file:
                continue
            record_mtime = datetime.utcfromtimestamp(record_file.stat().st_mtime)
            latest_summary = (
                db.query(models.ChatSummary)
                .filter(models.ChatSummary.user_id == user.id)
                .order_by(models.ChatSummary.summary_date.desc())
                .first()
            )
            if latest_summary and latest_summary.summary_date >= record_mtime:
                continue
            content = record_file.read_text(encoding="utf-8")
            if not content.strip():
                continue
            summary_date = datetime.utcnow()
            summary = summarize_chat(content, summary_date)
            user_summary_dir = SUMMARY_DIR / user_id
            user_summary_dir.mkdir(parents=True, exist_ok=True)
            summary_file = (
                user_summary_dir
                / f"{user_id}-{summary_date.strftime('%Y-%m-%d-%H%M')}_sum.txt"
            )
            summary_file.write_text(summary, encoding="utf-8")
            summary_record = models.ChatSummary(
                user_id=user.id, file_path=str(summary_file), summary_date=summary_date
            )
            db.add(summary_record)
            quiz_payload = generate_quiz(summary)
            choices = quiz_payload.get("choices", [])
            if not isinstance(choices, list):
                choices = []
            quiz = models.Quiz(user_id=user.id, title="")
            question = models.QuizQuestion(
                question=quiz_payload.get("question", ""),
                choices=json.dumps(choices, ensure_ascii=False),
                correct=quiz_payload.get("correct", ""),
                wrong=json.dumps(quiz_payload.get("wrong", []), ensure_ascii=False),
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
    finally:
        db.close()


if __name__ == "__main__":
    run_quiz_job()
