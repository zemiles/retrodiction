# -*- coding: utf-8 -*-
"""
기술적 지표 계산
- RSI (Relative Strength Index)
- 이동평균 (MA)
"""

from typing import Optional

import pandas as pd


def calculate_rsi_series(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI 전체 시리즈 반환 (시각화용)

    Args:
        prices: 종가 시리즈
        period: RSI 기간

    Returns:
        RSI 시리즈 (NaN은 period 구간)
    """
    if prices is None or len(prices) < 2:
        return pd.Series()
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    """
    RSI(상대강도지수) 계산
    RSI = 100 - (100 / (1 + RS))
    RS = 평균상승폭 / 평균하락폭 (Wilder 스무딩)

    Args:
        prices: 종가 시리즈 (과거 -> 현재 순)
        period: RSI 기간 (기본 14)

    Returns:
        최신 RSI 값 (0~100), 데이터 부족 시 None
    """
    rsi_series = calculate_rsi_series(prices, period)
    if rsi_series.empty or pd.isna(rsi_series.iloc[-1]):
        return None
    return float(rsi_series.iloc[-1])


def calculate_ma(prices: pd.Series, period: int) -> pd.Series:
    """이동평균 (MA) 계산"""
    return prices.rolling(window=period).mean()


def get_closing_prices(df: pd.DataFrame) -> pd.Series:
    """
    DataFrame에서 종가 시리즈 추출
    API 응답 필드: stck_clpr, stck_clos_prc 등
    """
    for col in ["stck_clpr", "stck_clos_prc", "clos_prc", "close"]:
        if col in df.columns:
            series = df[col].copy()
            # 숫자 변환 (쉼표 제거)
            series = pd.to_numeric(series.astype(str).str.replace(",", ""), errors="coerce")
            return series.dropna()
    return pd.Series()
