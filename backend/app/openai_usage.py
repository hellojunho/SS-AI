from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
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
    # OpenAI Usage API는 2-3일 지연이 있고, 현재 날짜는 2025년이어야 함
    # 2026년 날짜를 사용하면 400 에러 발생
    if today.year >= 2026:
        # 시스템 시간이 잘못된 경우 안전한 기본값 사용
        today = date(2025, 1, 26)
    # OpenAI API 데이터 지연을 고려하여 3일 전까지의 데이터 조회
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
    
    # OpenAI Usage API는 date 범위가 아닌 단일 날짜를 요구함
    # 여러 날짜의 데이터를 합산해야 함
    all_records = []
    current_date = window.start_date
    days_queried = 0
    
    try:
        while current_date <= window.end_date:
            response = requests.get(
                settings.openai_usage_endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
                params={"date": current_date.isoformat()},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            
            # 첫 번째 날짜의 응답 구조 확인
            if days_queried == 0:
                logging.info(f"OpenAI API 응답 샘플 (날짜: {current_date}): {payload}")
            
            data = payload.get("data")
            if data and isinstance(data, list):
                all_records.extend(data)
            
            current_date += timedelta(days=1)
            days_queried += 1
            
    except requests.RequestException as exc:
        # 에러 응답 본문 로깅
        error_detail = ""
        if hasattr(exc, 'response') and exc.response is not None:
            try:
                error_detail = f" - Response: {exc.response.text}"
            except:
                pass
        logging.warning(f"OpenAI 사용량 조회 실패 (date: {current_date}){error_detail}", exc_info=exc)
        return None
    except ValueError as exc:
        logging.warning("OpenAI 사용량 응답 파싱 실패", exc_info=exc)
        return None

    if not all_records:
        logging.warning(f"OpenAI 사용량 응답에서 데이터를 찾지 못했습니다. (조회 기간: {window.start_date} ~ {window.end_date}, 조회 일수: {days_queried}일)")
        return None

    prompt_tokens, completion_tokens, total_tokens, matched = _sum_tokens(all_records)
    if matched == 0 and all_records:
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
