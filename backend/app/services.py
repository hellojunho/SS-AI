from __future__ import annotations

import json
from datetime import datetime

from openai import OpenAI

from .config import settings


def _client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def generate_chat_answer(message: str) -> tuple[str, str]:
    client = _client()
    if client is None:
        return (
            "OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의해주세요.",
            "OpenAI API 키 미설정",
        )
    prompt = (
        "당신은 스포츠과학자입니다. 사용자의 질문에 대해 가장 최근 발표된 논문과 실험을 찾고,"
        " 그 결과를 근거로 출처와 함께 답변하세요. 최신 논문이 오래된 경우에도 그 연도를 명시하세요."
        " 한국어로 답변하고, 마지막 줄에 '출처:' 형식으로 DOI나 링크를 포함하세요."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ],
    )
    content = response.choices[0].message.content or ""
    if "출처:" in content:
        answer, reference = content.split("출처:", 1)
        return answer.strip(), reference.strip()
    return content.strip(), "출처 정보 없음"


def summarize_chat(content: str, date: datetime) -> str:
    client = _client()
    if client is None:
        return "OpenAI API 키가 설정되지 않아 요약을 생성할 수 없습니다."
    prompt = (
        "다음 대화 기록을 하루 단위로 요약하세요. 핵심 개념과 학습 포인트만 간결하게 정리하세요."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"날짜: {date.date()}\n대화 기록:\n{content}"},
        ],
    )
    return response.choices[0].message.content or ""


def generate_quiz(summary: str) -> dict:
    client = _client()
    if client is None:
        return {
            "question": "OpenAI API 키가 설정되지 않아 퀴즈를 생성할 수 없습니다.",
            "correct": "",
            "wrong": "",
            "explanation": "",
            "reference": "",
        }
    prompt = (
        "다음 요약 내용을 바탕으로 1개의 퀴즈를 생성하세요."
        " JSON 형식으로만 답변하세요."
        " 형식: {\"question\": \"...\", \"correct\": \"...\","
        " \"wrong\": \"...\", \"explanation\": \"정답/오답 해설\","
        " \"reference\": \"관련 논문 또는 영상 링크\"}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": summary},
        ],
    )
    content = response.choices[0].message.content or "{}"
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
