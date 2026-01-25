# AI 문서 기반 Q&A (RAG) 파이프라인

GPU 없이도 동작하는 **문서 검색 + 답변 생성(RAG)** 파이프라인 예시입니다. txt/csv/pdf/md/웹페이지를 수집하고, 텍스트를 청킹한 뒤 임베딩을 생성하여 FAISS 인덱스에 저장합니다. 이후 질의 시 관련 문서를 검색하고, 필요하면 OpenAI API로 답변을 생성합니다.

## 구성
- `ingest.py`: 문서/URL 수집 → 청킹 → 임베딩 → FAISS 인덱스 저장
- `query.py`: 질문 → 관련 문서 검색 → (선택) OpenAI 답변 생성
- `rag_pipeline.py`: 공통 로직 (로더/청킹/임베딩/검색)

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ai/requirements.txt
```

## 문서 수집/인덱싱
```bash
python ai/ingest.py \
  --input docs/ \
  --input data/papers/sample.pdf \
  --url https://example.com/article \
  --output-dir ai/index
```

### 지원 형식
- txt, csv, pdf, md
- 웹페이지(URL)

## 질의/응답
OpenAI 키가 없으면 검색 결과만 출력합니다.
```bash
export OPENAI_API_KEY=YOUR_KEY
python ai/query.py \
  --question "스포츠 과학에서 근비대에 영향을 주는 주요 변수는?" \
  --index-dir ai/index \
  --top-k 4
```

## 권장 사항
- 데이터가 증가하면 `ai/index`를 주기적으로 재생성하세요.
- GPU가 추가되면 더 큰 임베딩 모델로 교체할 수 있습니다.
