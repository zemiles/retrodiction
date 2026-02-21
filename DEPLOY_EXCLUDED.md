# 푸시 시 제외된 민감정보

GitHub 푸시 시 `.gitignore`에 의해 **제외된** 파일 목록입니다.

## 제외된 파일/폴더

| 경로 | 포함 내용 | 비고 |
|------|-----------|------|
| `server/.env` | PORT, PYTHON_TRADING_SERVER_URL | 서버 설정 (배포 시 환경변수로 설정) |
| `Trading/config/kis_devlp.yaml` | 한국투자증권 API 앱키, 앱시크릿, 계좌번호, HTS ID | **절대 공개 금지** |
| `Trading/config/tokens/` | KIS 인증 토큰 (자동 생성) | 만료 시 재발급 |
| `server/node_modules/` | npm 패키지 | `npm install`로 설치 |
| `node_modules/` | npm 패키지 | `npm install`로 설치 |

## 포함된 예시 파일 (실제 값 없음)

| 경로 | 설명 |
|------|------|
| `server/.env.example` | 환경변수 템플릿 (값 비어 있음) |
| `Trading/config/kis_devlp.yaml.example` | API 설정 템플릿 (플레이스홀더만) |

## 배포 시 설정 방법

1. **Vercel/Render**: 환경변수에 `REACT_APP_API_URL`, `PYTHON_TRADING_SERVER_URL` 등 설정
2. **Trading**: `kis_devlp.yaml.example`을 `kis_devlp.yaml`로 복사 후 본인 API 키 입력
