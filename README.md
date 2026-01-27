# SS-AI Sports Science

FastAPI + React(TypeScript) + Flutter 기반 스포츠 과학 학습 서비스입니다. Docker Compose로 MySQL, Backend, Frontend를 함께 실행합니다.

## 구성
- **Backend**: FastAPI (`/backend`)
- **Frontend**: React + Vite (`/frontend`)
- **Mobile**: Flutter (`/mobile`)
- **DB**: MySQL

## 준비
1. Backend 환경 변수 설정
   - `/backend/.env` 생성 (예시는 `.env.example` 참고)
2. Frontend 환경 변수
   - `/frontend/secrets.json`에 API 주소 등 민감 정보를 저장합니다.

## 실행

### 웹 서비스 (Backend + Frontend)
```bash
docker-compose up --build
```

### 모바일 앱
```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://localhost:5001
```

### 모바일 앱 (Docker Compose)
```bash
docker-compose up --build mobile
```

**참고**: 
- iOS 시뮬레이터/기기에서는 `localhost` 대신 실제 IP 주소를 사용해야 합니다.
- Android 에뮬레이터에서는 `http://10.0.2.2:5001` 사용 가능합니다.
- 실제 기기에서는 `http://<YOUR_IP>:5001`을 사용하세요.

## 주요 기능
- JWT 기반 회원가입/로그인
- ChatGPT 기반 스포츠 과학 Q&A (대화 기록 저장)
- 일일 대화 요약 저장
- 요약 기반 퀴즈 생성/풀이

## 폴더 구조
```
backend/
  app/
  chat/record/{user_id}/{user_id}-YYYY-MM-DD.txt
  chat/summation/{user_id}/{user_id}-YYYY-MM-DD_sum.txt
  ai/
    README.md
    ingest.py
    query.py
    rag_pipeline.py
frontend/
  src/
mobile/
  lib/
  README.md
```

## 문서 기반 Q&A (RAG)
- GPU 없이도 문서(txt/csv/pdf/md/웹페이지)를 인덱싱하고 질문에 답할 수 있는 예시 스크립트를 `backend/ai/`에 제공합니다.
- 자세한 사용법은 `backend/ai/README.md`를 참고하세요.
