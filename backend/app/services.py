from __future__ import annotations

import json
from datetime import datetime
import requests
from typing import Optional

# 기존 OpenAI 사용 코드는 주석으로 보관합니다. 필요하면 주석 해제 후 사용하세요.
# from openai import OpenAI
#
# def _client() -> OpenAI | None:
#     if not settings.openai_api_key:
#         return None
#     return OpenAI(api_key=settings.openai_api_key)

from .config import settings


def _call_gemini(prompt: str) -> str:
    """간단한 Gemini(Generative Language) REST 호출기.

    환경변수 `GEMINI_API_KEY`(settings.gemini_api_key)를 사용합니다.
    응답 스키마가 달라질 수 있으므로 안전하게 여러 위치에서 텍스트를 추출합니다.
    """
    api_key = settings.gemini_api_key
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

    # REST 엔드포인트: 최신 Gemini 모델을 기본으로 사용합니다.
    model = settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }

    resp = requests.post(url, json=body, timeout=30)
    # HTTP 오류를 직접 처리하여 404/권한 문제에 대한 상세 로그와 안내를 반환합니다.
    try:
        data = resp.json()
    except ValueError:
        data = None

    if resp.status_code != 200:
        import logging

        logging.error("Gemini API error %s: %s", resp.status_code, resp.text)
        # 404인 경우 서비스 계정 인증으로 재시도 시도
        if resp.status_code == 404:
            import os
            try:
                sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                # 서비스 계정 경로가 실제 파일인지 확인합니다. (디렉토리일 경우 오류 방지)
                if sa_path and os.path.isfile(sa_path):
                    from google.oauth2 import service_account
                    from google.auth.transport.requests import Request as GoogleAuthRequest

                    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
                    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=scopes)
                    creds.refresh(GoogleAuthRequest())
                    token = creds.token
                    auth_url = url.split("?", 1)[0]
                    headers = {"Authorization": f"Bearer {token}"}
                    retry_resp = requests.post(auth_url, json=body, headers=headers, timeout=30)
                    try:
                        retry_text = retry_resp.text
                    except Exception:
                        retry_text = ""
                    if retry_resp.status_code == 200:
                        try:
                            data = retry_resp.json()
                        except Exception:
                            data = None
                    else:
                        logging.error("Gemini retry with service account failed %s: %s", retry_resp.status_code, retry_text)
                        # 클라이언트에게는 서버가 반환한 원문을 그대로 전달합니다.
                        return retry_text or f"HTTP {retry_resp.status_code}"
                else:
                    # API 키 방식에서 바로 404인 경우, 서버 응답 원문을 전달
                    return resp.text or f"HTTP {resp.status_code}"
            except Exception:
                logging.exception("서비스 계정 인증 시도 중 오류")
                return resp.text or f"HTTP {resp.status_code}"
        # 그 외 상태 코드는 서버 응답 본문을 그대로 반환
        return resp.text or f"HTTP {resp.status_code}"

    text: Optional[str] = None
    # 여러 가능한 필드명을 검사
    if isinstance(data, dict):
        if "candidates" in data and data.get("candidates"):
            cand = data["candidates"][0]
            if isinstance(cand, dict):
                content = cand.get("content")
                if isinstance(content, dict):
                    parts = content.get("parts")
                    if isinstance(parts, list) and parts:
                        part_text = parts[0].get("text")
                        if isinstance(part_text, str):
                            text = part_text
                if not text:
                    text = cand.get("output") or cand.get("text")
        elif "output" in data and isinstance(data["output"], str):
            text = data["output"]
        elif "content" in data and isinstance(data["content"], str):
            text = data["content"]
    if not text:
        # 안전하게 전체 응답을 문자열로 반환
        text = json.dumps(data, ensure_ascii=False)
    return text


def generate_chat_answer(message: str) -> tuple[str, str]:
    # Gemini 사용: 설정에서 키를 확인
    if not settings.gemini_api_key:
        # 기존 OpenAI 메시지는 주석으로 남겨둔 상태입니다.
        return (
            "GEMINI_API_KEY가 설정되지 않았습니다. 관리자에게 문의해주세요.",
            "GEMINI API 키 미설정",
        )

    prompt = (
        "당신은 스포츠과학자입니다. 사용자의 질문에 대해 가장 최근 발표된 논문과 실험을 찾고,"
        " 그 결과를 근거로 출처와 함께 답변하세요. 최신 논문이 오래된 경우에도 그 연도를 명시하세요."
        " 한국어로 답변하고, 마지막 줄에 '출처:' 형식으로 DOI나 링크를 포함하세요."
    )
    try:
        content = _call_gemini(prompt + "\n" + message)
    except Exception as exc:
        import logging

        logging.exception("Gemini 호출 중 오류 발생")
        return (
            "Gemini 호출 중 오류가 발생했습니다. 관리자에게 문의하세요.",
            "Gemini 호출 오류",
        )

    if "출처:" in content:
        answer, reference = content.split("출처:", 1)
        return answer.strip(), reference.strip()
    return content.strip(), "출처 정보 없음"


def summarize_chat(content: str, date: datetime) -> str:
    if not settings.gemini_api_key:
        return "GEMINI_API_KEY가 설정되지 않아 요약을 생성할 수 없습니다."
    prompt = "다음 대화 기록을 하루 단위로 요약하세요. 핵심 개념과 학습 포인트만 간결하게 정리하세요."
    try:
        return _call_gemini(prompt + "\n날짜: " + str(date.date()) + "\n대화 기록:\n" + content)
    except Exception:
        return "요약 생성 중 오류가 발생했습니다."


def generate_quiz(summary: str) -> dict:
    if not settings.gemini_api_key:
        return {
            "question": "GEMINI_API_KEY가 설정되지 않아 퀴즈를 생성할 수 없습니다.",
            "correct": "",
            "wrong": "",
            "explanation": "",
            "reference": "",
        }
    prompt = (
        "다음 요약 내용을 바탕으로 1개의 퀴즈를 생성하세요. "
        "JSON 형식으로만 답변하세요. "
        "형식: {\"question\": \"...\", \"correct\": \"...\", \"wrong\": \"...\", \"explanation\": \"정답/오답 해설\", \"reference\": \"관련 논문 또는 영상 링크\"}"
    )
    try:
        content = _call_gemini(prompt + "\n" + summary)
    except Exception:
        return {
            "question": "퀴즈 생성 중 오류가 발생했습니다.",
            "correct": "",
            "wrong": "",
            "explanation": "",
            "reference": "",
        }
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "question": content.strip(),
            "correct": "",
            "wrong": "",
            "explanation": "",
            "reference": "",
        }
