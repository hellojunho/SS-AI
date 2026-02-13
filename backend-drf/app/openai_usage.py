from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import Any

import requests
from django.conf import settings

from .llm_usage import UsageSnapshot


@dataclass(frozen=True)
class UsageWindow:
    start_date: date
    end_date: date


def _usage_window() -> UsageWindow:
    today = date.today()
    if today.year >= 2026:
        today = date(2025, 1, 26)
    end_date = today - timedelta(days=3)
    start_date = end_date.replace(day=1)
    return UsageWindow(start_date=start_date, end_date=end_date)


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

    all_records = []
    current_date = window.start_date
    days_queried = 0

    try:
        while current_date <= window.end_date:
            response = requests.get(
                settings.OPENAI_USAGE_ENDPOINT,
                headers={"Authorization": f"Bearer {api_key}"},
                params={"date": current_date.isoformat()},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            if days_queried == 0:
                logging.info("OpenAI API response sample (%s): %s", current_date, payload)
            data = payload.get("data")
            if data and isinstance(data, list):
                all_records.extend(data)
            current_date += timedelta(days=1)
            days_queried += 1
    except requests.RequestException as exc:
        error_detail = ""
        if getattr(exc, "response", None) is not None:
            try:
                error_detail = f" - Response: {exc.response.text}"
            except Exception:
                error_detail = ""
        logging.warning("OpenAI usage fetch failed (%s)%s", current_date, error_detail, exc_info=exc)
        return None
    except ValueError as exc:
        logging.warning("OpenAI usage parse failed", exc_info=exc)
        return None

    if not all_records:
        logging.warning(
            "OpenAI usage data missing (%s ~ %s, queried %s days)",
            window.start_date,
            window.end_date,
            days_queried,
        )
        return None

    prompt_tokens, completion_tokens, total_tokens, matched = _sum_tokens(all_records)
    if matched == 0 and all_records:
        logging.warning("OpenAI usage response has no token metrics")
        return None

    if total_tokens == 0:
        total_tokens = prompt_tokens + completion_tokens

    return UsageSnapshot(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        updated_at=datetime.utcnow(),
    )
