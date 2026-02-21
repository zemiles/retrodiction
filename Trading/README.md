# 주식 자동매매 봇

한국투자증권 Open API 기반 RSI 전략 자동매매 봇입니다.

## 기능

- **한국투자증권 Open API** 연동 (무료)
- **RSI 전략**: RSI 30 이하 매수, RSI 70 이상 매도
- **손절/익절**: -3% 손절, +5% 익절
- **모의투자/실전투자** 지원

## 사전 준비

1. [한국투자증권 Open API](https://apiportal.koreainvestment.com) 서비스 신청
2. 앱키(App Key), 앱시크릿(App Secret) 발급
3. 모의투자 앱키 별도 발급 (테스트 권장)

## 설치

```bash
pip install -r requirements.txt
```

## 설정

### API 키 넣는 위치: `config/kis_devlp.yaml`

**모의투자**로 시작하려면 아래만 입력하세요:

```yaml
# 모의투자 (https://apiportal.koreainvestment.com 에서 발급)
paper_app: "발급받은_모의투자_앱키"
paper_sec: "발급받은_모의투자_앱시크릿"
my_htsid: "KIS_고객ID"
my_paper_stock: "모의투자_계좌번호_앞8자리"
my_paper_future: "모의투자_계좌번호_앞8자리"
```

- **실전투자**(my_app, my_sec)는 나중에 실거래할 때 입력
- 상세 설정: `설정_가이드.md` 참고

### 모의투자 모드

`config/settings.yaml`에서 `mode: "vps"` 이면 모의투자 (기본값)

## 실행

**전체 절차**: `시작하기.md` 참고 (발급 → 설정 → 실행)

```bash
# 1. 의존성 설치 (최초 1회)
pip install -r requirements.txt

# 2. 봇 실행
python main.py
```

- Windows: `run.bat` 더블클릭
- **모의투자**: `config/settings.yaml`의 `mode: "vps"`
- **실전투자**: `mode: "prod"` (주의: 실제 자금 거래)

## 백테스팅 (필수)

**시작 시 자동 전략 검증**: `main.py` 실행 시 `backtest.auto_validate: true`이면 백테스트를 자동 실행합니다.

- 실전투자 + 수익률 음수 → 매매 차단 (`block_on_negative: true`)
- 모의투자 → 검증만 수행, 차단 없음
- `backtest_output/`에 결과 차트 저장

수동 실행:
```bash
python backtest.py
```

설정 (`config/settings.yaml`):
```yaml
backtest:
  auto_validate: true    # 시작 시 자동 검증
  block_on_negative: true  # 실전에서 수익률 음수 시 매매 차단
```

## 지표 시각화

pandas + matplotlib로 주가, RSI, 이동평균선 차트를 생성합니다.

```bash
python view_charts.py
```

- `charts_output/` 폴더에 PNG 차트 저장
- main.py 실행 시 `visualization.save_charts: true`이면 시작 시 차트 자동 생성

## 프로젝트 구조

```
Trading/
├── config/
│   ├── kis_devlp.yaml      # API 앱키 (직접 입력)
│   ├── kis_devlp.yaml.example
│   └── settings.yaml       # 전략/종목 설정
├── src/
│   ├── api/                # 한국투자증권 API
│   ├── data/               # 지표 계산 (RSI)
│   ├── strategy/           # 매매 전략
│   └── scheduler/          # 장 시간
├── main.py
└── requirements.txt
```

## 주의사항

- **반드시 모의투자로 충분히 테스트** 후 실전투자 사용
- 자동매매로 인한 손실에 대해 개발자는 책임지지 않습니다
- API 호출 제한(유량)을 준수하세요
