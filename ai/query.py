from __future__ import annotations

import argparse
import os
from pathlib import Path

from openai import OpenAI

from rag_pipeline import load_index, search


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="문서 기반 Q&A")
    parser.add_argument("--question", required=True, help="질문")
    parser.add_argument("--index-dir", default="ai/index", help="인덱스 경로")
    parser.add_argument("--top-k", type=int, default=4, help="검색 결과 수")
    return parser.parse_args()


def build_prompt(question: str, contexts: list[str]) -> list[dict[str, str]]:
    system_prompt = (
        "당신은 스포츠과학 전문가입니다. 한국어로 답변하되 '-습니다/했습니다' 체를 유지하십시오. "
        "필요 시 수식, 계산 과정, 근거 실험/논문을 구체적으로 인용해 설명하십시오. "
        "제공된 문서 내용을 기반으로 답변하며, 불확실하면 추가 정보가 필요하다고 말하십시오."
    )
    context_block = "\n\n".join(contexts)
    user_prompt = f"문서 발췌:\n{context_block}\n\n질문: {question}"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def main() -> None:
    args = parse_args()
    artifacts = load_index(Path(args.index_dir))
    results = search(artifacts, args.question, top_k=args.top_k)
    contexts = [f"[출처: {item.source}]\n{item.text}" for item in results]

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY가 없어 검색 결과만 출력합니다.")
        for context in contexts:
            print("\n---\n")
            print(context)
        return

    client = OpenAI(api_key=api_key)
    messages = build_prompt(args.question, contexts)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
    )
    print(response.choices[0].message.content or "")


if __name__ == "__main__":
    main()
