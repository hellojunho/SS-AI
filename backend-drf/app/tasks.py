from __future__ import annotations

import re
import subprocess
import sys
import time
import json
from pathlib import Path

from celery import shared_task
from django.core.serializers.json import DjangoJSONEncoder

from .errors import AppError
from .models import BackgroundJob, User
from .quiz_logic import generate_quiz_for_user, quiz_to_response, run_quiz_job

DOCS_ROOT = Path(__file__).resolve().parents[1] / "ai" / "docs"
DOCS_WEB_URLS = DOCS_ROOT / "web" / "urls.txt"
DOCS_FOLDERS = {
    ".csv": "csv",
    ".txt": "txt",
    ".pdf": "pdf",
    ".md": "md",
}
URL_COMMENT_RE = re.compile(r"^\s*#")


def _update_job(job_id: str, **updates) -> None:
    BackgroundJob.objects.filter(job_id=job_id).update(**updates)


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


def _simulate_progress(job_id: str, start: int, end: int, message: str, steps: int = 8) -> None:
    _update_job(job_id, status="running", progress=start, message=message)
    if steps <= 0:
        _update_job(job_id, status="running", progress=end, message=message)
        return
    increment = max(1, (end - start) // steps)
    current = start
    while current < end:
        time.sleep(0.35)
        current = min(end, current + increment)
        _update_job(job_id, status="running", progress=current, message=message)


@shared_task(name="app.tasks.run_admin_generate_quiz")
def run_admin_generate_quiz(job_id: str, target_user_id: str, admin_user_id: int) -> None:
    _update_job(job_id, status="running", progress=0)
    try:
        admin_user = User.objects.filter(id=admin_user_id).first()
        target_user = User.objects.filter(user_id=target_user_id).first()
        if not target_user:
            raise AppError(404, "사용자를 찾을 수 없습니다.")

        def report(progress: int) -> None:
            _update_job(job_id, progress=max(0, min(100, progress)))

        quiz = generate_quiz_for_user(target_user, progress_callback=report)
        response = quiz_to_response(quiz, current_user=admin_user)
        result = {**response, "source_user_id": target_user.user_id}
        result = json.loads(json.dumps(result, cls=DjangoJSONEncoder))
        _update_job(job_id, status="completed", progress=100, result=result, error="")
    except AppError as exc:
        _update_job(job_id, status="failed", progress=100, error=exc.detail)
    except Exception as exc:
        _update_job(job_id, status="failed", progress=100, error=str(exc))


@shared_task(name="app.tasks.run_admin_generate_all")
def run_admin_generate_all(job_id: str) -> None:
    _update_job(job_id, status="running", progress=0)
    created = 0
    failed: list[dict[str, str]] = []
    try:
        users = list(User.objects.all())
        total = len(users)
        for index, user in enumerate(users):
            try:
                generate_quiz_for_user(user)
                created += 1
            except AppError as exc:
                failed.append({"user_id": user.user_id, "reason": exc.detail})
            except Exception as exc:
                failed.append({"user_id": user.user_id, "reason": str(exc)})
            progress = int(((index + 1) / max(total, 1)) * 100)
            _update_job(job_id, progress=progress)

        _update_job(job_id, status="completed", progress=100, result={"created": created, "failed": failed}, error="")
    except Exception as exc:
        _update_job(job_id, status="failed", progress=100, error=str(exc))


@shared_task(name="app.tasks.run_docs_learning_job")
def run_docs_learning_job(job_id: str) -> None:
    try:
        _ensure_docs_dirs()
        urls = _get_urls()
        has_docs = _has_supported_files()
        if not has_docs and not urls:
            _update_job(job_id, status="failed", progress=100, message="학습할 문서가 없습니다.", error="학습할 문서가 없습니다.")
            return

        _simulate_progress(job_id, 0, 20, "문서/URL 수집 중", steps=6)
        _simulate_progress(job_id, 20, 45, "문서 정제 및 청킹 중", steps=8)
        _simulate_progress(job_id, 45, 80, "임베딩 생성 및 인덱스 구성 중", steps=10)

        command = [sys.executable, "ai/ingest.py", "--input", str(DOCS_ROOT), "--output-dir", "ai/index"]
        for url in urls:
            command.extend(["--url", url])
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )

        _simulate_progress(job_id, 80, 100, "인덱스 저장 중", steps=6)
        _update_job(job_id, status="completed", progress=100, message="학습 완료", error="")
    except Exception as exc:
        _update_job(job_id, status="failed", progress=100, message=f"학습 실패: {exc}", error=str(exc))


@shared_task(name="app.tasks.run_periodic_quiz_job")
def run_periodic_quiz_job() -> None:
    run_quiz_job()
