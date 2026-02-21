# Python 자동매매 서버 연동 가이드

## 개요

Retrodiction Node.js 백엔드에서 Python 자동매매 서버와 통신하는 방법입니다.

## 1. Python 서버 요구사항

### 필수 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 서버 상태 확인 (Retrodiction 대시보드에서 연결 상태 표시) |

### 권장 응답 형식 (예시)

```python
# Flask 예시
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "auto-trading",
        "timestamp": datetime.utcnow().isoformat()
    })
```

## 2. Retrodiction 서버 설정

`server/.env` 파일에 Python 서버 URL 추가:

```
PYTHON_TRADING_SERVER_URL=http://localhost:8000
```

## 3. API 호출 방법

### Node.js 백엔드를 통한 프록시

클라이언트(React)에서 Python 서버를 직접 호출할 수 없을 때, Node.js 백엔드가 프록시 역할을 합니다.

```
POST /api/python/proxy
Content-Type: application/json

{
  "method": "GET",
  "path": "trades/history",
  "data": {}
}
```

- `method`: GET, POST, PUT, DELETE 등
- `path`: Python 서버의 상대 경로 (예: `trades/history`, `strategy/status`)
- `data`: POST/PUT 시 전달할 body (선택)

### React에서 호출 예시

```javascript
import { proxyToPython } from './utils/api';

// 거래 내역 조회
const history = await proxyToPython('GET', 'trades/history');

// 전략 실행
const result = await proxyToPython('POST', 'strategy/run', { symbol: 'BTC' });
```

## 4. Python 서버 CORS 설정 (선택)

React 앱이 Python 서버를 직접 호출하려면 Python 서버에 CORS를 허용해야 합니다.

```python
# Flask-CORS 예시
from flask_cors import CORS
CORS(app, origins=["http://localhost:3000"])
```

일반적으로 Node.js 프록시를 사용하는 것이 더 안전합니다.
