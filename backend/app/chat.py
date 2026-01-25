from datetime import datetime
from pathlib import Path
from typing import List

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


def _parse_chat_file(file_path: Path) -> List[schemas.ChatHistoryEntry]:
    entries: List[schemas.ChatHistoryEntry] = []
    if not file_path.exists():
        return entries
    for line in file_path.read_text(encoding="utf-8").splitlines():
        content = line.strip()
        if not content:
            continue
        if content.startswith("나: "):
            entries.append(schemas.ChatHistoryEntry(role="me", content=content[3:]))
        elif content.startswith("GPT: "):
            entries.append(schemas.ChatHistoryEntry(role="gpt", content=content[5:]))
        elif content.startswith("출처: ") and entries and entries[-1].role == "gpt":
            entries[-1].content = f"{entries[-1].content}\n{content}"
        elif entries:
            entries[-1].content = f"{entries[-1].content}\n{content}"
    return entries


def _list_chat_dates(user_id: str) -> List[str]:
    user_dir = RECORD_DIR / user_id
    if not user_dir.exists():
        return []
    dates = []
    for file_path in user_dir.glob(f"{user_id}-*.txt"):
        name = file_path.stem
        date_str = name.replace(f"{user_id}-", "", 1)
        if date_str:
            dates.append(date_str)
    return sorted(dates, reverse=True)


def _current_date_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


@router.post("/ask", response_model=schemas.ChatResponse)
def ask_chat(
    payload: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        answer, reference = generate_chat_answer(payload.message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="ChatGPT 응답을 불러오지 못했습니다.") from exc
    date_str = _current_date_str()
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


@router.get("/history", response_model=schemas.ChatHistoryDatesResponse)
def get_chat_history_dates(
    current_user: models.User = Depends(get_current_user),
):
    return schemas.ChatHistoryDatesResponse(
        dates=_list_chat_dates(current_user.user_id),
        today=_current_date_str(),
    )


@router.get("/history/{date_str}", response_model=schemas.ChatHistoryResponse)
def get_chat_history(
    date_str: str,
    current_user: models.User = Depends(get_current_user),
):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다.") from exc
    user_dir = RECORD_DIR / current_user.user_id
    file_path = user_dir / f"{current_user.user_id}-{date_str}.txt"
    today = _current_date_str()
    if not file_path.exists():
        if date_str == today:
            return schemas.ChatHistoryResponse(date=date_str, entries=[], is_today=True)
        raise HTTPException(status_code=404, detail="대화 기록이 없습니다.")
    entries = _parse_chat_file(file_path)
    return schemas.ChatHistoryResponse(date=date_str, entries=entries, is_today=date_str == today)


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
