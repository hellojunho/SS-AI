from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline import build_index, load_documents, save_index


def parse_args() -> argparse.Namespace:
    default_output_dir = Path(__file__).resolve().parent / "index"
    parser = argparse.ArgumentParser(description="문서/URL 인덱싱")
    parser.add_argument("--input", action="append", default=[], help="파일 또는 디렉터리 경로")
    parser.add_argument("--url", action="append", default=[], help="웹페이지 URL")
    parser.add_argument("--output-dir", default=str(default_output_dir), help="인덱스 저장 경로")
    parser.add_argument("--model", default="intfloat/multilingual-e5-small", help="임베딩 모델")
    parser.add_argument("--max-chars", type=int, default=1000, help="청크 최대 길이")
    parser.add_argument("--overlap", type=int, default=200, help="청크 겹침 길이")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = [Path(path_str) for path_str in args.input]
    documents = load_documents(paths, args.url)
    if not documents:
        raise SystemExit("인덱싱할 문서가 없습니다.")
    artifacts = build_index(
        documents,
        model_name=args.model,
        max_chars=args.max_chars,
        overlap=args.overlap,
    )
    save_index(artifacts, Path(args.output_dir))
    print(f"인덱스 저장 완료: {args.output_dir}")


if __name__ == "__main__":
    main()
