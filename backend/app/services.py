from __future__ import annotations

import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests
from openai import APIStatusError, OpenAI, RateLimitError

from .config import settings

BASE_DIR = Path(__file__).resolve().parents[1]
ISSUE_LOG_DIR = BASE_DIR / "logs" / "issues"
URL_REGEX = re.compile(r"https?://[^\s\]\)]+")


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


def _is_accessible_reference(url: str, timeout: float = 3.0) -> bool:
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        if response.status_code >= 400:
            return False
        content_length = response.headers.get("Content-Length")
        if content_length and content_length.isdigit():
            return int(content_length) > 0
    except requests.RequestException as exc:
        logging.info("출처 링크 확인 실패(HEAD): %s", url, exc_info=exc)
        return False
    try:
        response = requests.get(url, allow_redirects=True, timeout=timeout + 2, stream=True)
        if response.status_code >= 400:
            return False
        return bool(response.raw.read(128))
    except requests.RequestException as exc:
        logging.info("출처 링크 확인 실패(GET): %s", url, exc_info=exc)
        return False


def _filter_references(reference: str) -> str:
    urls = URL_REGEX.findall(reference)
    if not urls:
        return ""
    valid_urls = []
    for url in urls:
        if _is_accessible_reference(url):
            valid_urls.append(url)
    return " ".join(valid_urls)


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
        "당신은 '스포츠과학 전문가'입니다. 답변 첫 줄은 반드시 '스포츠과학 전문가:'로 시작하십시오. "
        "한국어로 전문적이고 성의 있게 답변해야 합니다. "
        "말투는 반드시 '-습니다/했습니다' 체로 유지하고 '~요'를 사용하지 마십시오. "
        "답변은 가독성이 높은 구조(제목, 핵심 요약, 상세 설명, 예시, 적용 팁)로 작성하고, "
        "항상 구체적인 예시를 포함하십시오. "
        "질문에 지식/이론/실험 결과를 제시할 경우, 실제로 깊은 연관이 있는 논문 또는 실험 결과를 반드시 첨부하고 "
        "각 주장에 대한 근거를 명확한 출처와 함께 제시하십시오. "
        "출처는 질문과 직접 연관된 권위 있는 기관(피어리뷰 논문, 정부/공공기관, 대학, 전문 학회)의 "
        "링크만 사용하고, example.com 같은 임시/비권위 도메인은 금지합니다. "
        "검색 엔진은 관련 논문/기관을 찾는 용도로만 사용하고 검색 결과 페이지 자체는 출처로 쓰지 마십시오. "
        "연관성이 낮거나 불명확한 링크는 포함하지 말고, 출처가 불명확하거나 없는 경우에는 답변을 거절하고 "
        "추가 확인이 필요하다고 안내하십시오. "
        "링크는 클릭 가능한 URL 형태로 제공하고, 마지막 줄에 '출처:' 형식으로 정리하십시오."
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
        filtered_reference = _filter_references(reference.strip())
        return answer.strip(), filtered_reference or "출처 정보 없음"
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


def generate_quiz(summary: str) -> list[dict]:
    if not settings.openai_api_key:
        return [
            {
                "question": "OPENAI_API_KEY가 설정되지 않아 퀴즈를 생성할 수 없습니다.",
                "choices": [],
                "correct_index": -1,
                "correct": "",
                "wrong": [],
                "explanation": "",
                "reference": "",
                "link": "",
            }
        ]
    system_prompt = (
        "다음 요약 내용을 바탕으로 3~5개의 퀴즈를 생성하세요. "
        "대한민국의 물리치료사/간호사/의사/재활전문가/스포츠과학 전문가/NSCA 관련 자격시험에서 "
        "실제로 출제된 문제를 찾을 수 있다면 해당 문제를 우선 사용하십시오. "
        "실제 기출 문제로 확신할 수 없는 경우에는 유사한 출제 의도에 맞춘 창작 문제로 표시하고 "
        "출처 링크는 비워두십시오. "
        "모든 문제는 문항 내용과 직접 관련된 권위 있는 기관/논문 기반 참고자료 링크를 포함해야 하며, "
        "연관성이 낮은 링크는 금지합니다. example.com 같은 비권위 도메인은 금지합니다. "
        "해설에는 반드시 자세한 설명과 구체적인 예시를 포함하십시오. "
        "JSON 형식으로만 답변하세요. "
        "형식: {\"questions\": ["
        "{\"question\": \"...\", \"choices\": [\"보기1\", \"보기2\", \"보기3\", \"보기4\"], "
        "\"correct_index\": 0, \"explanation\": \"정답/오답 해설\", "
        "\"reference\": \"관련 논문/기관 링크\", "
        "\"is_actual\": true, \"link\": \"기출문제 출처 링크\"}"
        "]}"
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
        return [
            {
                "question": "요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요.",
                "choices": [],
                "correct_index": -1,
                "correct": "",
                "wrong": [],
                "explanation": "",
                "reference": "",
                "link": "",
            }
        ]
    except Exception as exc:
        issue_path = _log_issue("quiz_error", messages=messages, error=exc)
        logging.exception("퀴즈 생성 중 오류 발생 (로그: %s)", issue_path)
        return [
            {
                "question": "요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요.",
                "choices": [],
                "correct_index": -1,
                "correct": "",
                "wrong": [],
                "explanation": "",
                "reference": "",
                "link": "",
            }
        ]
    payloads = _extract_quiz_payloads(content)
    if not payloads:
        _log_issue("quiz_response_parse", messages=messages, response=content)
        return [
            {
                "question": content.strip(),
                "choices": [],
                "correct_index": -1,
                "correct": "",
                "wrong": [],
                "explanation": "",
                "reference": "",
                "link": "",
            }
        ]
    return _normalize_quiz_payloads(payloads)


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
    if correct_index in range(len(normalized_choices)):
        tagged = [
            {"choice": choice, "is_correct": index == correct_index}
            for index, choice in enumerate(normalized_choices)
        ]
        random.shuffle(tagged)
        normalized_choices = [item["choice"] for item in tagged]
        correct_index = next(
            (index for index, item in enumerate(tagged) if item["is_correct"]),
            -1,
        )
    correct = normalized_choices[correct_index] if correct_index in range(4) else ""
    wrong = [choice for index, choice in enumerate(normalized_choices) if index != correct_index]
    is_actual = payload.get("is_actual")
    link = str(payload.get("link", "")).strip()
    if isinstance(is_actual, str):
        is_actual = is_actual.strip().lower() in {"true", "yes", "y", "1"}
    if not is_actual:
        link = ""
    return {
        "question": question,
        "choices": normalized_choices,
        "correct_index": correct_index,
        "correct": correct,
        "wrong": wrong,
        "explanation": str(payload.get("explanation", "")).strip(),
        "reference": str(payload.get("reference", "")).strip(),
        "link": link,
    }


def _normalize_quiz_payloads(payloads: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        normalized.append(_normalize_quiz_payload(payload))
    return normalized


def _extract_quiz_payloads(content: str) -> list[dict] | None:
    content = content.strip()
    if not content:
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        if isinstance(parsed.get("questions"), list):
            return parsed["questions"]
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if code_block:
        json_block = code_block.group(1).strip()
        try:
            parsed = json.loads(json_block)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            if isinstance(parsed.get("questions"), list):
                return parsed["questions"]
            return [parsed]
        if isinstance(parsed, list):
            return parsed
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = content[start : end + 1]
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            if isinstance(parsed.get("questions"), list):
                return parsed["questions"]
            return [parsed]
        if isinstance(parsed, list):
            return parsed
    return None
