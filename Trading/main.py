# -*- coding: utf-8 -*-
"""
주식 자동매매 봇 - 메인 실행
한국투자증권 Open API 기반 RSI 전략
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import yaml

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api import kis_auth
from src.api import korea_investment as api
from src.backtest.engine import run_backtest
from src.backtest.metrics import format_result
from src.backtest.visualization import plot_backtest_result
from src.scheduler.market_scheduler import is_market_closing_soon, is_market_open
from src.strategy.rsi_strategy import StrategyConfig, get_position_size, get_signal
from src.visualization.charts import plot_stock_indicators

# 종목코드 -> 종목명
STOCK_NAMES = {"005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", "051910": "LG화학", "006400": "삼성SDI"}

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config():
    """설정 로드"""
    config_path = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일 없음: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_holdings() -> dict:
    """보유 종목 {종목코드: (매입평균가, 보유수량)}"""
    _, df2 = api.inquire_balance()
    holdings = {}
    if df2 is not None and not df2.empty:
        for _, row in df2.iterrows():
            code = str(row.get("pdno", row.get("prdt_name", ""))).strip()
            if not code or len(code) != 6 or not code.isdigit():
                continue
            avg_prc = 0.0
            for col in ["pchs_avg_pric", "avg_pric"]:
                if col in row:
                    try:
                        avg_prc = float(str(row[col]).replace(",", ""))
                        break
                    except (ValueError, TypeError):
                        pass
            qty = 0
            for col in ["hldg_qty", "ord_qty", "qty"]:
                if col in row:
                    try:
                        qty = int(float(str(row[col]).replace(",", "")))
                        break
                    except (ValueError, TypeError):
                        pass
            if qty > 0:
                holdings[code] = (avg_prc, qty)
    return holdings


def run_trading_cycle(config: dict):
    """1회 매매 사이클 실행"""
    if not is_market_open():
        logger.info("장 종료 시간 - 대기 중")
        return

    strategy_cfg = StrategyConfig(
        rsi_period=config["strategy"]["rsi_period"],
        buy_threshold=config["strategy"]["buy_threshold"],
        sell_threshold=config["strategy"]["sell_threshold"],
        stop_loss=config["strategy"]["stop_loss"],
        take_profit=config["strategy"]["take_profit"],
    )
    stocks = config["stocks"]
    risk = config["risk"]
    max_per_stock = risk["max_position_per_stock"]

    # 보유 종목 {종목코드: (매입평균가, 보유수량)}
    holdings = get_holdings()

    # 일별 시세 조회 기간 (RSI 14 + 여유)
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=30)
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    for stock_code in stocks:
        try:
            # 일별 시세 (RSI 계산용)
            price_df = api.inquire_daily_itemchartprice(stock_code, start_str, end_str)
            current_price = api.get_current_price(stock_code)
            if current_price is None:
                logger.warning(f"{stock_code} 현재가 조회 실패 - 스킵")
                continue

            buy_price = holdings.get(stock_code, (None, 0))[0] if stock_code in holdings else None

            signal = get_signal(price_df, buy_price, strategy_cfg)

            if signal == "buy":
                if is_market_closing_soon():
                    logger.info(f"{stock_code} 장 마감 임박 - 매수 보류")
                    continue
                cash = api.get_available_cash()
                if cash is None or cash < current_price:
                    logger.info(f"{stock_code} 매수 가능 금액 부족")
                    continue
                qty = get_position_size(cash, current_price, max_per_stock)
                if qty <= 0:
                    continue
                result = api.order_cash(
                    ord_dv="buy",
                    pdno=stock_code,
                    ord_qty=str(qty),
                    ord_unpr=str(int(current_price)),
                )
                if result is not None and not result.empty:
                    logger.info(f"{stock_code} 매수 주문 완료: {qty}주 @ {current_price:,.0f}원")
                else:
                    logger.warning(f"{stock_code} 매수 주문 실패")

            elif signal == "sell" and stock_code in holdings:
                buy_price, qty = holdings[stock_code]
                if qty <= 0:
                    continue
                result = api.order_cash(
                    ord_dv="sell",
                    pdno=stock_code,
                    ord_qty=str(qty),
                    ord_unpr=str(int(current_price)),
                )
                if result is not None and not result.empty:
                    logger.info(f"{stock_code} 매도 주문 완료: {qty}주 @ {current_price:,.0f}원")
                else:
                    logger.warning(f"{stock_code} 매도 주문 실패")

            kis_auth.smart_sleep()

        except Exception as e:
            logger.exception(f"{stock_code} 처리 중 오류: {e}")


def run_strategy_validation(config: dict) -> tuple:
    """
    시작 전 자동 전략 검증 (백테스트)
    Returns:
        (passed: bool, summary: str)
    """
    bt_cfg = config.get("backtest", {})
    if not bt_cfg.get("auto_validate", False):
        return True, "자동 검증 비활성화"

    strategy_cfg = StrategyConfig(
        rsi_period=config["strategy"]["rsi_period"],
        buy_threshold=config["strategy"]["buy_threshold"],
        sell_threshold=config["strategy"]["sell_threshold"],
        stop_loss=config["strategy"]["stop_loss"],
        take_profit=config["strategy"]["take_profit"],
    )
    initial_cash = bt_cfg.get("initial_cash", 10_000_000)
    max_position_pct = bt_cfg.get("max_position_pct", 0.2)
    commission_rate = bt_cfg.get("commission_rate", 0.00015)
    days = bt_cfg.get("days", 100)

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    results = []
    output_dir = os.path.join(os.path.dirname(__file__), "backtest_output")
    os.makedirs(output_dir, exist_ok=True)

    for stock_code in config["stocks"]:
        try:
            price_df = api.inquire_daily_itemchartprice(stock_code, start_str, end_str)
            if price_df is None or price_df.empty:
                continue
            result = run_backtest(
                price_df=price_df,
                initial_cash=initial_cash,
                config=strategy_cfg,
                max_position_pct=max_position_pct,
                commission_rate=commission_rate,
            )
            results.append((stock_code, result))
            name = STOCK_NAMES.get(stock_code, stock_code)
            chart_path = os.path.join(output_dir, f"backtest_{stock_code}_{name}.png")
            plot_backtest_result(result=result, price_df=price_df, stock_name=name, save_path=chart_path)
            kis_auth.smart_sleep()
        except Exception as e:
            logger.warning("백테스트 %s 실패: %s", stock_code, e)

    if not results:
        return False, "백테스트 데이터 없음 - 검증 실패"

    # 전체 종목 평균 수익률로 검증
    avg_return = sum(r.total_return_pct for _, r in results) / len(results)
    block_on_neg = bt_cfg.get("block_on_negative", False) and not kis_auth.is_paper_trading()

    summary_lines = [
        f"전략 검증 완료 ({len(results)}종목)",
        f"평균 수익률: {avg_return:.2%}",
    ]
    for code, r in results:
        name = STOCK_NAMES.get(code, code)
        summary_lines.append(f"  - {name}: {r.total_return_pct:.2%} (승률 {r.win_rate:.0%})")
    summary = "\n".join(summary_lines)

    if block_on_neg and avg_return < 0:
        return False, summary + "\n\n[차단] 과거 수익률 음수 - 매매를 시작하지 않습니다. 전략을 조정하세요."
    return True, summary


def update_charts(config: dict):
    """관심 종목 지표 차트 생성 및 저장"""
    viz = config.get("visualization", {})
    if not viz.get("save_charts", False):
        return
    output_dir = viz.get("output_dir", "charts_output")
    output_path = os.path.join(os.path.dirname(__file__), output_dir)
    os.makedirs(output_path, exist_ok=True)

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=90)
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")
    strategy = config["strategy"]

    for stock_code in config["stocks"]:
        try:
            price_df = api.inquire_daily_itemchartprice(stock_code, start_str, end_str)
            if price_df is None or price_df.empty:
                continue
            name = STOCK_NAMES.get(stock_code, stock_code)
            save_path = os.path.join(output_path, f"{stock_code}_{name}.png")
            plot_stock_indicators(
                price_df=price_df,
                stock_name=name,
                rsi_period=strategy["rsi_period"],
                buy_threshold=strategy["buy_threshold"],
                sell_threshold=strategy["sell_threshold"],
                save_path=save_path,
            )
            logger.info("차트 저장: %s", save_path)
            kis_auth.smart_sleep()
        except Exception as e:
            logger.warning("차트 생성 실패 %s: %s", stock_code, e)


def main():
    """메인 진입점"""
    logger.info("=== 주식 자동매매 봇 시작 ===")

    config = load_config()
    mode = config.get("mode", "vps")
    interval = config["risk"].get("check_interval_seconds", 60)

    # 인증
    kis_auth.auth(svr=mode, product="01")
    logger.info(f"모드: {'모의투자' if kis_auth.is_paper_trading() else '실전투자'}")

    # 자동 전략 검증 (백테스트)
    passed, summary = run_strategy_validation(config)
    logger.info("\n%s", summary)
    if not passed:
        logger.error("전략 검증 실패 - 매매를 시작하지 않습니다.")
        return

    # 시작 시 차트 생성 (visualization.save_charts: true일 때)
    viz = config.get("visualization", {})
    if viz.get("save_charts"):
        try:
            update_charts(config)
        except Exception as e:
            logger.warning("차트 생성 실패: %s", e)

    # 장 중 루프
    while True:
        try:
            run_trading_cycle(config)
        except KeyboardInterrupt:
            logger.info("사용자 종료")
            break
        except Exception as e:
            logger.exception("사이클 오류: %s", e)

        if not is_market_open():
            logger.info("장 종료 - 1분 후 재확인")
        import time

        time.sleep(interval)


if __name__ == "__main__":
    main()
