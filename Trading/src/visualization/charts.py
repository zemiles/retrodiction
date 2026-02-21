# -*- coding: utf-8 -*-
"""
주식 지표 시각화
- pandas DataFrame 기반 차트
- 가격, RSI, 이동평균, 거래량
"""

import logging
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from ..data.indicators import calculate_ma, calculate_rsi_series, get_closing_prices

# 한글 폰트 설정 (Windows: 맑은고딕, macOS: AppleGothic)
import platform
if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
else:
    plt.rcParams["font.family"] = ["AppleGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

logger = logging.getLogger(__name__)


def _prepare_chart_data(price_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    API 시세 DataFrame을 차트용 DataFrame으로 변환
    한국투자증권 API: stck_bsop_date(영업일), stck_clpr(종가)
    """
    if price_df is None or price_df.empty:
        return None
    closes = get_closing_prices(price_df)
    if closes.empty:
        return None
    df = price_df.copy()
    # 날짜 인덱스
    for col in ["stck_bsop_date", "stck_clos_date", "stck_clpr_dt", "date"]:
        if col in df.columns:
            dates = pd.to_datetime(df[col].astype(str), format="%Y%m%d", errors="coerce")
            df = pd.DataFrame({"close": closes.values[: len(dates)]}, index=dates.dropna())
            df = df.sort_index().dropna()
            return df
    # 날짜 없으면 순번
    return pd.DataFrame({"close": closes.values}, index=pd.RangeIndex(len(closes)))


def plot_stock_indicators(
    price_df: pd.DataFrame,
    stock_name: str = "종목",
    rsi_period: int = 14,
    ma_periods: tuple = (5, 20, 60),
    buy_threshold: int = 30,
    sell_threshold: int = 70,
    save_path: Optional[str] = None,
    figsize: tuple = (12, 10),
) -> None:
    """
    주식 지표 종합 차트 시각화
    - 상단: 가격 + 이동평균선
    - 하단: RSI + 매수/매도 기준선

    Args:
        price_df: 일별 시세 DataFrame (API inquire_daily_itemchartprice 결과)
        stock_name: 종목명 (차트 제목)
        rsi_period: RSI 기간
        ma_periods: 이동평균 기간 (5, 20, 60)
        buy_threshold: RSI 매수 기준선
        sell_threshold: RSI 매도 기준선
        save_path: 저장 경로 (None이면 화면 표시)
        figsize: 차트 크기
    """
    df = _prepare_chart_data(price_df)
    if df is None:
        logger.warning("차트 데이터 준비 실패")
        return

    closes = df["close"] if "close" in df.columns else get_closing_prices(price_df)
    if closes.empty:
        closes = df.iloc[:, 0] if len(df.columns) > 0 else pd.Series()
    x_labels = df.index

    fig, axes = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1], sharex=True)
    fig.suptitle(f"{stock_name} - 주가 및 지표", fontsize=14, fontweight="bold")

    # --- 1. 가격 + 이동평균 ---
    ax1 = axes[0]
    ax1.plot(x_labels, closes.values, label="종가", color="#2E86AB", linewidth=2)

    for period, color in zip(ma_periods, ["#E94F37", "#44AF69", "#F4A261"]):
        if len(closes) >= period:
            ma = calculate_ma(closes, period)
            ax1.plot(x_labels, ma.values, label=f"MA{period}", color=color, linewidth=1.2, alpha=0.8)

    ax1.set_ylabel("가격 (원)", fontsize=10)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_title("가격 및 이동평균선")

    # --- 2. RSI ---
    ax2 = axes[1]
    rsi_series = calculate_rsi_series(closes, rsi_period)
    ax2.plot(x_labels, rsi_series.values, label="RSI", color="#9B59B6", linewidth=2)
    ax2.axhline(y=buy_threshold, color="#27AE60", linestyle="--", alpha=0.7, label=f"매수기준({buy_threshold})")
    ax2.axhline(y=sell_threshold, color="#E74C3C", linestyle="--", alpha=0.7, label=f"매도기준({sell_threshold})")
    ax2.axhline(y=50, color="#95A5A6", linestyle=":", alpha=0.5)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI", fontsize=10)
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_title("RSI (상대강도지수)")

    plt.xlabel("날짜", fontsize=10)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info("차트 저장: %s", save_path)
    else:
        plt.show()
    plt.close()


def plot_simple_price(price_df: pd.DataFrame, stock_name: str = "종목", save_path: Optional[str] = None) -> None:
    """
    단순 가격 차트 (pandas plot 사용)
    """
    df = _prepare_chart_data(price_df)
    if df is None:
        return
    closes = get_closing_prices(price_df) if "close" not in df.columns else df.iloc[:, 0]
    series = pd.Series(closes.values, index=df.index if isinstance(df.index, pd.DatetimeIndex) else range(len(closes)))
    ax = series.plot(title=f"{stock_name} - 종가", figsize=(10, 5), color="#2E86AB", linewidth=2)
    ax.set_ylabel("가격 (원)")
    ax.grid(True, alpha=0.3)
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()
    plt.close()
