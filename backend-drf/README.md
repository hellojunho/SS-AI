# backend-drf

기존 `backend`(FastAPI)를 유지한 채, 동일 기능을 Django Rest Framework + Celery로 마이그레이션한 백엔드입니다.

## 포트
- DRF API: `8000`

## 실행
루트에서 실행:

```bash
docker compose up --build backend-drf redis celery-worker celery-beat db
```

## 주요 구성
- Django + DRF API (`/auth`, `/chat`, `/quiz`, `/admin/docs`, `/admin/llm`)
- JWT 인증 (access/refresh, token version)
- MySQL 스키마 호환(기존 테이블명/컬럼명 유지)
- Celery 기반 비동기 작업
  - 관리자 퀴즈 생성 job/status
  - 전체 사용자 퀴즈 생성 job/status
  - 문서 학습 작업 job/status
  - 5분 주기 퀴즈 배치 작업(Celery Beat)

## 환경 변수
`backend-drf/.env` 또는 `backend-drf/.env.example` 참고

## 참고
- 기존 FastAPI 백엔드(`backend/`)는 삭제하지 않고 그대로 유지됩니다.
- 클라이언트에서 DRF를 사용하려면 API Base URL을 `http://localhost:8000`으로 설정하면 됩니다.
