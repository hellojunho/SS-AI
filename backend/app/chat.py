from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import get_current_user
from .db import get_db
from .services import generate_chat_answer, summarize_chat

router = APIRouter(prefix="/chat", tags=["chat"])

BASE_DIR = Path(__file__).resolve().parents[1]
RECORD_DIR = BASE_DIR / "chat" / "record"
SUMMARY_DIR = BASE_DIR / "chat" / "summation"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@router.post("/ask", response_model=schemas.ChatResponse)
def ask_chat(
    payload: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answer, reference = generate_chat_answer(payload.message)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    user_dir = RECORD_DIR / current_user.user_id
    _ensure_dir(user_dir)
    file_path = user_dir / f"{current_user.user_id}-{date_str}.txt"
    with file_path.open("a", encoding="utf-8") as file:
        file.write(f"나: {payload.message}\n")
        file.write(f"GPT: {answer}\n")
        if reference:
            file.write(f"출처: {reference}\n")
        file.write("\n")
    record = models.ChatRecord(user_id=current_user.id, file_path=str(file_path))
    db.add(record)
    db.commit()
    return schemas.ChatResponse(answer=answer, reference=reference, file_path=str(file_path))


@router.post("/summarize", response_model=schemas.SummaryResponse)
def summarize_day(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    date = datetime.utcnow()
    date_str = date.strftime("%Y-%m-%d")
    user_record_dir = RECORD_DIR / current_user.user_id
    record_file = user_record_dir / f"{current_user.user_id}-{date_str}.txt"
    if not record_file.exists():
        raise HTTPException(status_code=404, detail="대화 기록이 없습니다.")
    content = record_file.read_text(encoding="utf-8")
    summary = summarize_chat(content, date)
    user_summary_dir = SUMMARY_DIR / current_user.user_id
    _ensure_dir(user_summary_dir)
    summary_file = user_summary_dir / f"{current_user.user_id}-{date_str}_sum.txt"
    summary_file.write_text(summary, encoding="utf-8")
    summary_record = models.ChatSummary(
        user_id=current_user.id, file_path=str(summary_file), summary_date=date
    )
    db.add(summary_record)
    db.commit()
    return schemas.SummaryResponse(file_path=str(summary_file), summary=summary)
