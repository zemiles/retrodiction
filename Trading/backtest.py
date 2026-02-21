# -*- coding: utf-8 -*-
"""
백테스트 실행 스크립트
- 설정 기반 RSI 전략 백테스트
- API 또는 로컬 데이터 사용
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api import kis_auth
from src.api import korea_investment as api
from src.backtest.engine import run_backtest
from src.backtest.metrics import format_result, print_trade_log
from src.backtest.visualization import plot_backtest_result
from src.strategy.rsi_strategy import StrategyConfig

STOCK_NAMES = {"005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", "051910": "LG화학", "006400": "삼성SDI"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """백테스트 실행"""
    config_path = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")
    if not os.path.exists(config_path):
        logger.error("config/settings.yaml 없음")
        return

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    strategy_cfg = StrategyConfig(
        rsi_period=config["strategy"]["rsi_period"],
        buy_threshold=config["strategy"]["buy_threshold"],
        sell_threshold=config["strategy"]["sell_threshold"],
        stop_loss=config["strategy"]["stop_loss"],
        take_profit=config["strategy"]["take_profit"],
    )

    bt_cfg = config.get("backtest", {})
    initial_cash = bt_cfg.get("initial_cash", 10_000_000)
    max_position_pct = bt_cfg.get("max_position_pct", 0.2)
    commission_rate = bt_cfg.get("commission_rate", 0.00015)
    days = bt_cfg.get("days", 100)

    # API 인증
    mode = config.get("mode", "vps")
    kis_auth.auth(svr=mode, product="01")
    logger.info("인증 완료 - 백테스트 데이터 조회 중...")

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    output_dir = os.path.join(os.path.dirname(__file__), "backtest_output")
    os.makedirs(output_dir, exist_ok=True)

    for stock_code in config["stocks"]:
        try:
            price_df = api.inquire_daily_itemchartprice(stock_code, start_str, end_str)
            if price_df is None or price_df.empty:
                logger.warning("%s 시세 데이터 없음 - 스킵", stock_code)
                continue

            result = run_backtest(
                price_df=price_df,
                initial_cash=initial_cash,
                config=strategy_cfg,
                max_position_pct=max_position_pct,
                commission_rate=commission_rate,
            )

            stock_name = STOCK_NAMES.get(stock_code, stock_code)
            print("\n" + format_result(result))
            print_trade_log(result)

            # 차트 저장
            chart_path = os.path.join(output_dir, f"backtest_{stock_code}_{stock_name}.png")
            plot_backtest_result(
                result=result,
                price_df=price_df,
                stock_name=stock_name,
                save_path=chart_path,
            )
            logger.info("백테스트 차트 저장: %s", chart_path)

            kis_auth.smart_sleep()
        except Exception as e:
            logger.exception("%s 백테스트 오류: %s", stock_code, e)

    logger.info("백테스트 완료. backtest_output 폴더를 확인하세요.")


if __name__ == "__main__":
    main()
