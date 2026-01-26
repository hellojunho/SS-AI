from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock


@dataclass
class UsageSnapshot:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    updated_at: datetime | None


_lock = Lock()
_snapshot = UsageSnapshot(prompt_tokens=0, completion_tokens=0, total_tokens=0, updated_at=None)


def record_usage(prompt_tokens: int, completion_tokens: int, total_tokens: int | None = None) -> None:
    safe_prompt = max(prompt_tokens, 0)
    safe_completion = max(completion_tokens, 0)
    safe_total = max(total_tokens if total_tokens is not None else safe_prompt + safe_completion, 0)
    with _lock:
        _snapshot.prompt_tokens += safe_prompt
        _snapshot.completion_tokens += safe_completion
        _snapshot.total_tokens += safe_total
        _snapshot.updated_at = datetime.utcnow()


def get_usage_snapshot() -> UsageSnapshot:
    with _lock:
        return UsageSnapshot(
            prompt_tokens=_snapshot.prompt_tokens,
            completion_tokens=_snapshot.completion_tokens,
            total_tokens=_snapshot.total_tokens,
            updated_at=_snapshot.updated_at,
        )
