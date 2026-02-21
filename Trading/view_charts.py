# -*- coding: utf-8 -*-
"""
주식 지표 시각화 실행 스크립트
- API 연동 후 관심 종목 차트 표시
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api import kis_auth
from src.api import korea_investment as api
from src.visualization.charts import plot_stock_indicators

# 종목코드 -> 종목명 매핑
STOCK_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "051910": "LG화학",
    "006400": "삼성SDI",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    """차트 시각화 실행"""
    # 설정 로드
    config_path = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")
    if not os.path.exists(config_path):
        logger.error("config/settings.yaml 없음")
        return
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 인증
    mode = config.get("mode", "vps")
    kis_auth.auth(svr=mode, product="01")
    logger.info("인증 완료 - 차트 데이터 조회 중...")

    # 기간 설정
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=90)
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    strategy = config["strategy"]
    output_dir = os.path.join(os.path.dirname(__file__), "charts_output")
    os.makedirs(output_dir, exist_ok=True)

    for stock_code in config["stocks"]:
        try:
            price_df = api.inquire_daily_itemchartprice(stock_code, start_str, end_str)
            if price_df is None or price_df.empty:
                logger.warning("%s 시세 데이터 없음 - 스킵", stock_code)
                continue

            stock_name = STOCK_NAMES.get(stock_code, stock_code)
            save_path = os.path.join(output_dir, f"{stock_code}_{stock_name}.png")

            # save_path: 파일 저장, None이면 plt.show()로 화면 표시
            plot_stock_indicators(
                price_df=price_df,
                stock_name=stock_name,
                rsi_period=strategy["rsi_period"],
                buy_threshold=strategy["buy_threshold"],
                sell_threshold=strategy["sell_threshold"],
                save_path=save_path,  # charts_output/에 저장
            )
            logger.info("%s 차트 저장 완료: %s", stock_name, save_path)

            kis_auth.smart_sleep()
        except Exception as e:
            logger.exception("%s 차트 생성 오류: %s", stock_code, e)

    logger.info("모든 차트 생성 완료. charts_output 폴더를 확인하세요.")


if __name__ == "__main__":
    main()
