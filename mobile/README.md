# SS-AI Mobile (Flutter)

Flutter 기반의 모바일 클라이언트입니다. 기존 FastAPI 백엔드를 그대로 사용하며, 동일한 MySQL DB를 공유합니다.

## 구성
- 로그인/회원가입
- AI Q&A 질문 전송
- 퀴즈 조회 및 제출
- 내 정보 조회

## 실행
```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://localhost:9000
```

## Docker Compose 실행
```bash
docker-compose up --build mobile
```

## 환경 변수
- `API_BASE_URL`: FastAPI 서버 주소 (기본값: `http://localhost:9000`)

## 참고
- 토큰 만료 처리 로직은 웹 클라이언트와 동일하게 30분 세션 기준으로 갱신됩니다.
- 데이터는 기존 DB를 그대로 사용합니다.
