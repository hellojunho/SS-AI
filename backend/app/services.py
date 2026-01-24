from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from openai import APIStatusError, OpenAI, RateLimitError

from .config import settings

BASE_DIR = Path(__file__).resolve().parents[1]
ISSUE_LOG_DIR = BASE_DIR / "logs" / "issues"


def _client() -> OpenAI:
    api_key = settings.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


def _log_issue(
    issue_type: str,
    *,
    messages: list[dict[str, str]] | None = None,
    response: str | None = None,
    error: Exception | None = None,
    metadata: dict[str, Any] | None = None,
) -> Path:
    ISSUE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    issue_id = uuid4().hex
    log_path = ISSUE_LOG_DIR / f"{timestamp}_{issue_type}_{issue_id}.log"
    with log_path.open("w", encoding="utf-8") as file:
        file.write(f"timestamp: {datetime.utcnow().isoformat()}\n")
        file.write(f"issue_type: {issue_type}\n")
        if metadata:
            file.write(f"metadata: {json.dumps(metadata, ensure_ascii=False)}\n")
        if messages is not None:
            file.write("messages:\n")
            file.write(json.dumps(messages, ensure_ascii=False, indent=2))
            file.write("\n")
        if response is not None:
            file.write("response:\n")
            file.write(response)
            file.write("\n")
        if error is not None:
            file.write(f"error_type: {type(error).__name__}\n")
            file.write(f"error_message: {error}\n")
            status = getattr(error, "status_code", None)
            if status is not None:
                file.write(f"status_code: {status}\n")
            body = getattr(error, "body", None)
            if body is not None:
                try:
                    file.write(f"error_body: {json.dumps(body, ensure_ascii=False)}\n")
                except TypeError:
                    file.write(f"error_body: {body}\n")
    return log_path


def _extract_error_code(exc: Exception) -> str | None:
    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return None
    error = body.get("error")
    if not isinstance(error, dict):
        return None
    return error.get("code") or error.get("type")


def _call_chatgpt(
    messages: list[dict[str, str]],
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> str:
    client = _client()
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except RateLimitError as exc:
            if attempt >= max_retries:
                raise
            delay = base_delay * (2**attempt)
            logging.warning("Rate limit 발생. %.1f초 후 재시도합니다.", delay, exc_info=exc)
            time.sleep(delay)
        except APIStatusError as exc:
            if exc.status_code != 429 or attempt >= max_retries:
                raise
            error_code = _extract_error_code(exc)
            if error_code == "insufficient_quota" and attempt >= max_retries - 2:
                raise
            delay = base_delay * (2**attempt)
            logging.warning("API 429 응답. %.1f초 후 재시도합니다.", delay, exc_info=exc)
            time.sleep(delay)
    return ""


def generate_chat_answer(message: str) -> tuple[str, str]:
    if not settings.openai_api_key:
        return (
            "OPENAI_API_KEY가 설정되지 않았습니다. 관리자에게 문의해주세요.",
            "OpenAI API 키 미설정",
        )

    system_prompt = (
        "당신은 스포츠과학자입니다. 사용자의 질문에 대해 가장 최근 발표된 논문과 실험을 찾고,"
        " 그 결과를 근거로 출처와 함께 답변하세요. 최신 논문이 오래된 경우에도 그 연도를 명시하세요."
        " 한국어로 답변하고, 마지막 줄에 '출처:' 형식으로 DOI나 링크를 포함하세요."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]
    try:
        content = _call_chatgpt(messages)
    except (RateLimitError, APIStatusError) as exc:
        issue_path = _log_issue(
            "chat_rate_limit",
            messages=messages,
            error=exc,
            metadata={"error_code": _extract_error_code(exc)},
        )
        logging.exception("ChatGPT 호출 중 429/Rate limit 발생 (로그: %s)", issue_path)
        return ("요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요.", "")
    except Exception as exc:
        issue_path = _log_issue("chat_error", messages=messages, error=exc)
        logging.exception("ChatGPT 호출 중 오류 발생 (로그: %s)", issue_path)
        return ("요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요.", "")

    if "출처:" in content:
        answer, reference = content.split("출처:", 1)
        return answer.strip(), reference.strip()
    return content.strip(), "출처 정보 없음"


def summarize_chat(content: str, date: datetime) -> str:
    if not settings.openai_api_key:
        return "OPENAI_API_KEY가 설정되지 않아 요약을 생성할 수 없습니다."
    system_prompt = (
        "다음 대화 기록을 하루 단위로 요약하세요. 핵심 개념과 학습 포인트만 간결하게 정리하세요."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "날짜: " + str(date.date()) + "\n대화 기록:\n" + content,
        },
    ]
    try:
        return _call_chatgpt(messages)
    except (RateLimitError, APIStatusError) as exc:
        issue_path = _log_issue(
            "summary_rate_limit",
            messages=messages,
            error=exc,
            metadata={"error_code": _extract_error_code(exc)},
        )
        logging.exception("요약 생성 중 429/Rate limit 발생 (로그: %s)", issue_path)
        return "요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요."
    except Exception as exc:
        issue_path = _log_issue("summary_error", messages=messages, error=exc)
        logging.exception("요약 생성 중 오류 발생 (로그: %s)", issue_path)
        return "요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요."


def generate_quiz(summary: str) -> dict:
    if not settings.openai_api_key:
        return {
            "question": "OPENAI_API_KEY가 설정되지 않아 퀴즈를 생성할 수 없습니다.",
            "choices": [],
            "correct_index": -1,
            "correct": "",
            "wrong": [],
            "explanation": "",
            "reference": "",
        }
    system_prompt = (
        "다음 요약 내용을 바탕으로 1개의 퀴즈를 생성하세요. "
        "JSON 형식으로만 답변하세요. "
        "보기는 4개이며 정답은 1개입니다. "
        "형식: {\"question\": \"...\", \"choices\": [\"보기1\", \"보기2\", \"보기3\", \"보기4\"], \"correct_index\": 0, \"explanation\": \"정답/오답 해설\", \"reference\": \"관련 논문 또는 영상 링크\"}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": summary},
    ]
    try:
        content = _call_chatgpt(messages)
    except (RateLimitError, APIStatusError) as exc:
        issue_path = _log_issue(
            "quiz_rate_limit",
            messages=messages,
            error=exc,
            metadata={"error_code": _extract_error_code(exc)},
        )
        logging.exception("퀴즈 생성 중 429/Rate limit 발생 (로그: %s)", issue_path)
        return {
            "question": "요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요.",
            "choices": [],
            "correct_index": -1,
            "correct": "",
            "wrong": [],
            "explanation": "",
            "reference": "",
        }
    except Exception as exc:
        issue_path = _log_issue("quiz_error", messages=messages, error=exc)
        logging.exception("퀴즈 생성 중 오류 발생 (로그: %s)", issue_path)
        return {
            "question": "요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요.",
            "choices": [],
            "correct_index": -1,
            "correct": "",
            "wrong": [],
            "explanation": "",
            "reference": "",
        }
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        _log_issue("quiz_response_parse", messages=messages, response=content)
        return {
            "question": content.strip(),
            "choices": [],
            "correct_index": -1,
            "correct": "",
            "wrong": [],
            "explanation": "",
            "reference": "",
        }
    return _normalize_quiz_payload(payload)


def _normalize_quiz_payload(payload: dict) -> dict:
    question = str(payload.get("question", "")).strip()
    choices = payload.get("choices", [])
    if not isinstance(choices, list):
        choices = []
    normalized_choices = [str(choice).strip() for choice in choices if str(choice).strip()]
    correct_index = payload.get("correct_index", -1)
    try:
        correct_index = int(correct_index)
    except (TypeError, ValueError):
        correct_index = -1
    if len(normalized_choices) != 4 or correct_index not in range(4):
        correct_text = str(payload.get("correct", "")).strip()
        wrong = payload.get("wrong", [])
        wrong_choices: list[str] = []
        if isinstance(wrong, list):
            wrong_choices = [str(item).strip() for item in wrong if str(item).strip()]
        elif isinstance(wrong, str):
            wrong_choices = [item.strip() for item in wrong.split("\n") if item.strip()]
        if correct_text:
            normalized_choices = [correct_text] + wrong_choices
            normalized_choices = normalized_choices[:4]
            while len(normalized_choices) < 4:
                normalized_choices.append(f"보기 {len(normalized_choices) + 1}")
            correct_index = 0
        else:
            normalized_choices = normalized_choices[:4]
            while len(normalized_choices) < 4:
                normalized_choices.append(f"보기 {len(normalized_choices) + 1}")
            correct_index = 0 if normalized_choices else -1
    correct = normalized_choices[correct_index] if correct_index in range(4) else ""
    wrong = [choice for index, choice in enumerate(normalized_choices) if index != correct_index]
    return {
        "question": question,
        "choices": normalized_choices,
        "correct_index": correct_index,
        "correct": correct,
        "wrong": wrong,
        "explanation": str(payload.get("explanation", "")).strip(),
        "reference": str(payload.get("reference", "")).strip(),
    }
