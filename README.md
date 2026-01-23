# SS-AI Sports Science

FastAPI + React(TypeScript) 기반 스포츠 과학 학습 서비스입니다. Docker Compose로 MySQL, Backend, Frontend를 함께 실행합니다.

## 구성
- **Backend**: FastAPI (`/backend`)
- **Frontend**: React + Vite (`/frontend`)
- **DB**: MySQL

## 준비
1. Backend 환경 변수 설정
   - `/backend/.env` 생성 (예시는 `.env.example` 참고)
2. Frontend 환경 변수
   - `/frontend/secrets.json`에 API 주소 등 민감 정보를 저장합니다.

## 실행
```bash
docker-compose up --build
```

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
frontend/
  src/
```
