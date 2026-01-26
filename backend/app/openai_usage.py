from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
from typing import Any

import requests

from .config import settings
from .llm_usage import UsageSnapshot


@dataclass(frozen=True)
class UsageWindow:
    start_date: date
    end_date: date


def _usage_window() -> UsageWindow:
    today = date.today()
    return UsageWindow(start_date=today.replace(day=1), end_date=today)


def _sum_tokens(records: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    prompt_total = 0
    completion_total = 0
    total_total = 0
    matched_records = 0
    for record in records:
        prompt_tokens = (
            record.get("prompt_tokens")
            or record.get("input_tokens")
            or record.get("n_context_tokens_total")
            or 0
        )
        completion_tokens = (
            record.get("completion_tokens")
            or record.get("output_tokens")
            or record.get("n_generated_tokens_total")
            or 0
        )
        total_tokens = record.get("total_tokens") or record.get("n_tokens_total") or 0
        if prompt_tokens or completion_tokens or total_tokens:
            matched_records += 1
        prompt_total += int(prompt_tokens or 0)
        completion_total += int(completion_tokens or 0)
        total_total += int(total_tokens or 0)
    return prompt_total, completion_total, total_total, matched_records


def fetch_openai_usage(api_key: str | None) -> UsageSnapshot | None:
    if not api_key:
        return None
    window = _usage_window()
    try:
        response = requests.get(
            settings.openai_usage_endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            params={
                "start_date": window.start_date.isoformat(),
                "end_date": window.end_date.isoformat(),
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logging.warning("OpenAI 사용량 조회 실패", exc_info=exc)
        return None
    except ValueError as exc:
        logging.warning("OpenAI 사용량 응답 파싱 실패", exc_info=exc)
        return None

    data = payload.get("data")
    if data is None:
        logging.warning("OpenAI 사용량 응답에 data 필드가 없습니다.")
        return None
    if not isinstance(data, list):
        logging.warning("OpenAI 사용량 data 형식이 올바르지 않습니다.")
        return None

    prompt_tokens, completion_tokens, total_tokens, matched = _sum_tokens(data)
    if matched == 0 and data:
        logging.warning("OpenAI 사용량 응답에서 토큰 정보를 찾지 못했습니다.")
        return None

    if total_tokens == 0:
        total_tokens = prompt_tokens + completion_tokens

    return UsageSnapshot(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        updated_at=datetime.utcnow(),
    )
