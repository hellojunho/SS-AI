from __future__ import annotations

import json
from datetime import datetime

from openai import OpenAI

from .config import settings


def _client() -> OpenAI:
    api_key = settings.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


def _call_chatgpt(prompt: str) -> str:
    client = _client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def generate_chat_answer(message: str) -> tuple[str, str]:
    if not settings.openai_api_key:
        return (
            "OPENAI_API_KEY가 설정되지 않았습니다. 관리자에게 문의해주세요.",
            "OpenAI API 키 미설정",
        )

    prompt = (
        "당신은 스포츠과학자입니다. 사용자의 질문에 대해 가장 최근 발표된 논문과 실험을 찾고,"
        " 그 결과를 근거로 출처와 함께 답변하세요. 최신 논문이 오래된 경우에도 그 연도를 명시하세요."
        " 한국어로 답변하고, 마지막 줄에 '출처:' 형식으로 DOI나 링크를 포함하세요."
    )
    try:
        content = _call_chatgpt(prompt + "\n" + message)
    except Exception:
        import logging

        logging.exception("ChatGPT 호출 중 오류 발생")
        return (
            "ChatGPT 호출 중 오류가 발생했습니다. 관리자에게 문의하세요.",
            "ChatGPT 호출 오류",
        )

    if "출처:" in content:
        answer, reference = content.split("출처:", 1)
        return answer.strip(), reference.strip()
    return content.strip(), "출처 정보 없음"


def summarize_chat(content: str, date: datetime) -> str:
    if not settings.openai_api_key:
        return "OPENAI_API_KEY가 설정되지 않아 요약을 생성할 수 없습니다."
    prompt = "다음 대화 기록을 하루 단위로 요약하세요. 핵심 개념과 학습 포인트만 간결하게 정리하세요."
    try:
        return _call_chatgpt(prompt + "\n날짜: " + str(date.date()) + "\n대화 기록:\n" + content)
    except Exception:
        return "요약 생성 중 오류가 발생했습니다."


def generate_quiz(summary: str) -> dict:
    if not settings.openai_api_key:
        return {
            "question": "OPENAI_API_KEY가 설정되지 않아 퀴즈를 생성할 수 없습니다.",
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
        content = _call_chatgpt(prompt + "\n" + summary)
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
