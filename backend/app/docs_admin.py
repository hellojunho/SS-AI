from __future__ import annotations

import asyncio
import re
import subprocess
import sys
from pathlib import Path
from threading import Lock
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, HttpUrl

from .auth import require_admin


class WebDocumentPayload(BaseModel):
    url: HttpUrl


class LearnStatus(BaseModel):
    status: str
    progress: int
    message: str


DOCS_ROOT = Path(__file__).resolve().parents[1] / "ai" / "docs"
DOCS_WEB_URLS = DOCS_ROOT / "web" / "urls.txt"
DOCS_FOLDERS = {
    ".csv": "csv",
    ".txt": "txt",
    ".pdf": "pdf",
    ".md": "md",
}
URL_COMMENT_RE = re.compile(r"^\s*#")

_learn_lock = Lock()
_learn_status: LearnStatus = LearnStatus(status="idle", progress=0, message="대기 중")

router = APIRouter(prefix="/admin/docs", tags=["admin-docs"])


def _ensure_docs_dirs() -> None:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in DOCS_FOLDERS.values():
        (DOCS_ROOT / folder).mkdir(parents=True, exist_ok=True)
    (DOCS_ROOT / "web").mkdir(parents=True, exist_ok=True)
    DOCS_WEB_URLS.touch(exist_ok=True)


def _get_urls() -> list[str]:
    if not DOCS_WEB_URLS.exists():
        return []
    urls: list[str] = []
    for line in DOCS_WEB_URLS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or URL_COMMENT_RE.match(line):
            continue
        urls.append(line.strip())
    return urls


def _has_supported_files() -> bool:
    for file_path in DOCS_ROOT.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in DOCS_FOLDERS:
            return True
    return False


def _update_learn_status(status: str, progress: int, message: str) -> None:
    with _learn_lock:
        _learn_status.status = status
        _learn_status.progress = progress
        _learn_status.message = message


def _current_status() -> LearnStatus:
    with _learn_lock:
        return LearnStatus(**_learn_status.model_dump())


async def _run_ingest(paths: Iterable[Path], urls: Iterable[str]) -> None:
    command = [sys.executable, "ai/ingest.py"]
    for path in paths:
        command.extend(["--input", str(path)])
    for url in urls:
        command.extend(["--url", url])
    command.extend(["--output-dir", "ai/index"])

    await asyncio.to_thread(
        subprocess.run,
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )


async def _simulate_progress(start: int, end: int, message: str, steps: int = 8) -> None:
    _update_learn_status("running", start, message)
    if steps <= 0:
        _update_learn_status("running", end, message)
        return
    increment = max(1, (end - start) // steps)
    current = start
    while current < end:
        await asyncio.sleep(0.35)
        current = min(end, current + increment)
        _update_learn_status("running", current, message)


async def _run_learning_job() -> None:
    try:
        _ensure_docs_dirs()
        paths = [DOCS_ROOT]
        urls = _get_urls()
        has_docs = _has_supported_files()
        if not has_docs and not urls:
            _update_learn_status("failed", 100, "학습할 문서가 없습니다.")
            return

        ingest_task = asyncio.create_task(_run_ingest(paths, urls))
        await _simulate_progress(0, 20, "문서/URL 수집 중", steps=6)
        await _simulate_progress(20, 45, "문서 정제 및 청킹 중", steps=8)
        await _simulate_progress(45, 80, "임베딩 생성 및 인덱스 구성 중", steps=10)
        await ingest_task
        await _simulate_progress(80, 100, "인덱스 저장 중", steps=6)
        _update_learn_status("completed", 100, "학습 완료")
    except Exception as exc:  # noqa: BLE001 - 운영 환경에서 실패 메시지 전달 필요
        _update_learn_status("failed", 100, f"학습 실패: {exc}")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user=Depends(require_admin),
):
    _ensure_docs_dirs()
    suffix = Path(file.filename or "").suffix.lower()
    target_folder = DOCS_FOLDERS.get(suffix)
    if not target_folder:
        raise HTTPException(status_code=400, detail="지원하지 않는 확장자입니다.")
    destination = DOCS_ROOT / target_folder / (file.filename or f"upload{suffix}")
    content = await file.read()
    destination.write_bytes(content)
    return {"filename": destination.name, "stored_in": str(destination)}


@router.post("/web", status_code=status.HTTP_201_CREATED)
async def upload_web_document(
    payload: WebDocumentPayload,
    current_user=Depends(require_admin),
):
    _ensure_docs_dirs()
    url = str(payload.url)
    with DOCS_WEB_URLS.open("a", encoding="utf-8") as file:
        file.write(f"{url}\n")
    return {"stored_url": url}


@router.post("/learn", status_code=status.HTTP_202_ACCEPTED)
async def start_learning(
    background_tasks: BackgroundTasks,
    current_user=Depends(require_admin),
):
    status_snapshot = _current_status()
    if status_snapshot.status == "running":
        raise HTTPException(status_code=409, detail="학습이 이미 진행 중입니다.")
    _update_learn_status("running", 0, "학습을 준비하고 있습니다.")
    background_tasks.add_task(_run_learning_job)
    return {"message": "학습을 시작했습니다."}


@router.get("/learn/status", response_model=LearnStatus)
async def get_learning_status(current_user=Depends(require_admin)):
    return _current_status()
