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
  --input ai/docs/ \
  --input data/papers/sample.pdf \
  --url https://example.com/article \
  --output-dir ai/index
```

## 운영 환경에서 문서 학습(관리자 페이지 연동)
관리자 페이지에서 문서를 업로드하면 `ai/docs` 아래 확장자 폴더에 자동 저장됩니다. 학습 버튼을 누르면 백엔드가
`ai/ingest.py`를 호출하여 인덱스를 갱신합니다. 학습 진행 상황은 큰 작업 단위(문서 수집 → 청킹 → 임베딩 → 저장)를
기준으로 가중치를 부여해 0~100%로 표시합니다.

### 폴더 구조
```
ai/docs/
  csv/  # CSV 문서
  txt/  # 텍스트 문서
  pdf/  # PDF 문서
  md/   # 마크다운 문서
  web/  # 웹 문서 URL
    urls.txt
```

### 웹 페이지 학습 방법
웹 페이지는 `ai/docs/web/urls.txt`에 URL을 한 줄씩 추가하거나, 관리자 페이지의 “웹 URL 추가” 입력창으로 등록합니다.
`ai/ingest.py`는 해당 URL을 읽어 HTML 본문을 추출하고 텍스트로 변환한 뒤 인덱싱합니다.

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
