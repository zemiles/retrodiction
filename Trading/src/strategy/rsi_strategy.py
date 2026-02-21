# -*- coding: utf-8 -*-
"""
RSI 기반 매매 전략
- RSI < buy_threshold: 매수 신호 (과매도)
- RSI > sell_threshold: 매도 신호 (과매수)
- 손절/익절 적용
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

from ..data.indicators import calculate_rsi, get_closing_prices

logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    """전략 설정"""
    rsi_period: int = 14
    buy_threshold: int = 30
    sell_threshold: int = 70
    stop_loss: float = -0.03   # -3%
    take_profit: float = 0.05  # +5%


def get_signal(
    price_df,
    buy_price: Optional[float],
    config: StrategyConfig,
) -> str:
    """
    매매 신호 판단
    price_df: 일별 시세 DataFrame (stck_clpr 등)
    buy_price: 매수 단가 (보유 중이면 설정, 없으면 None)

    Returns:
        "buy" | "sell" | "hold"
    """
    if price_df is None or price_df.empty:
        return "hold"

    closes = get_closing_prices(price_df)
    if closes.empty or len(closes) < config.rsi_period + 1:
        return "hold"

    rsi = calculate_rsi(closes, config.rsi_period)
    if rsi is None:
        return "hold"

    current_price = float(closes.iloc[-1])

    # 보유 중인 경우: 손절/익절 체크
    if buy_price is not None and buy_price > 0:
        ret = (current_price - buy_price) / buy_price
        if ret <= config.stop_loss:
            logger.info(f"손절 신호: 수익률 {ret:.2%}")
            return "sell"
        if ret >= config.take_profit:
            logger.info(f"익절 신호: 수익률 {ret:.2%}")
            return "sell"

    # RSI 기반 신호
    if rsi <= config.buy_threshold:
        return "buy"
    if rsi >= config.sell_threshold:
        return "sell"
    return "hold"


def get_position_size(
    available_cash: float,
    current_price: float,
    max_per_stock: float,
) -> int:
    """
    매수 수량 계산 (1주 단위)

    Args:
        available_cash: 매수 가능 금액
        current_price: 현재가
        max_per_stock: 종목당 최대 투자금

    Returns:
        매수 수량 (주)
    """
    if current_price <= 0:
        return 0
    investable = min(available_cash, max_per_stock)
    qty = int(investable / current_price)
    return max(0, qty)
