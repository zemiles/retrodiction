# Retrodiction

매매 패턴 분석 및 향후 매매 제안을 제공하는 웹 앱입니다.

## 구조

- **프론트엔드** (React): `npm start` (포트 3000)
- **백엔드** (Node.js): `server/` (포트 3001)
- **Python 자동매매 서버**: 별도 연동 (선택)

## 실행 방법

### 1. 의존성 설치

```bash
npm install
cd server && npm install && cd ..
```

### 2. 백엔드 서버 실행

```bash
cd server
npm run dev
```

### 3. 프론트엔드 실행

```bash
npm start
```

브라우저에서 http://localhost:3000 접속

## Trading 봇 연동

1. Trading API 서버 실행:
   ```bash
   cd Trading
   pip install -r requirements.txt
   python api_server.py
   ```
   (또는 `Trading/run_api.bat` 실행)

2. `server/.env`에 `PYTHON_TRADING_SERVER_URL=http://localhost:5000` 설정 (기본값)

3. Retrodiction 화면에서 **Trading 봇** 메뉴로 접속

## API

| 엔드포인트 | 설명 |
|-----------|------|
| GET /api/health | 서버 상태 |
| GET /api/upbit/market/all | 업비트 마켓 목록 |
| GET /api/upbit/ticker?markets=KRW-BTC | 업비트 시세 |
| POST /api/kis/token | 한국투자증권 토큰 발급 |
| GET /api/python/status | Python 서버 연결 상태 |
