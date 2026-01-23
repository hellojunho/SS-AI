from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path

from fastapi import Request

from . import models
from .db import SessionLocal
from .security import decode_access_token

BASE_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE_DIR / "logs"


def _extract_user_identifier(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except ValueError:
        return None
    user_pk = payload.get("sub")
    if not user_pk:
        return None
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == int(user_pk)).first()
        return user.user_id if user else None
    finally:
        db.close()


def log_error(request: Request, exc: Exception, status_code: int | None = None) -> Path:
    date_folder = datetime.utcnow().strftime("%Y-%m-%d")
    timestamp = datetime.utcnow().strftime("%H%M%S")
    user_identifier = _extract_user_identifier(request) or "general"
    log_dir = LOGS_DIR / date_folder
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{user_identifier}_{timestamp}.log"
    trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"timestamp: {datetime.utcnow().isoformat()}\n")
        file.write(f"method: {request.method}\n")
        file.write(f"path: {request.url.path}\n")
        if status_code is not None:
            file.write(f"status_code: {status_code}\n")
        file.write(f"error_type: {type(exc).__name__}\n")
        file.write(f"error_message: {exc}\n")
        file.write("traceback:\n")
        file.write(trace)
        file.write("\n")
    return log_path
