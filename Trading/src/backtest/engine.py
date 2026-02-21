# -*- coding: utf-8 -*-
"""
백테스팅 엔진
- RSI 전략 시뮬레이션
- 거래 내역 및 성과 지표 산출
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from ..data.indicators import calculate_rsi_series, get_closing_prices
from ..strategy.rsi_strategy import StrategyConfig

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """단일 거래 기록"""
    date: str
    action: str  # "buy" | "sell"
    price: float
    qty: int
    value: float
    cash_after: float
    position_value: float
    total_equity: float
    rsi: Optional[float] = None


@dataclass
class BacktestResult:
    """백테스트 결과"""
    initial_cash: float
    final_equity: float
    total_return: float
    total_return_pct: float
    annual_return_pct: Optional[float]
    num_trades: int
    win_trades: int
    loss_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: Optional[float]
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)


def _get_signal_for_day(
    closes: pd.Series,
    idx: int,
    buy_price: Optional[float],
    config: StrategyConfig,
) -> str:
    """
    특정 일자의 매매 신호 (백테스트용)
    idx: 현재 일자 인덱스 (0-based)
    """
    if idx < config.rsi_period:
        return "hold"
    hist = closes.iloc[: idx + 1]
    rsi_series = calculate_rsi_series(hist, config.rsi_period)
    rsi = rsi_series.iloc[-1]
    if pd.isna(rsi):
        return "hold"
    current_price = float(hist.iloc[-1])

    # 손절/익절
    if buy_price is not None and buy_price > 0:
        ret = (current_price - buy_price) / buy_price
        if ret <= config.stop_loss:
            return "sell"
        if ret >= config.take_profit:
            return "sell"

    if rsi <= config.buy_threshold:
        return "buy"
    if rsi >= config.sell_threshold:
        return "sell"
    return "hold"


def run_backtest(
    price_df: pd.DataFrame,
    initial_cash: float = 10_000_000,
    config: Optional[StrategyConfig] = None,
    max_position_pct: float = 0.2,
    commission_rate: float = 0.00015,
) -> BacktestResult:
    """
    RSI 전략 백테스트 실행

    Args:
        price_df: 일별 시세 DataFrame (stck_clpr, stck_bsop_date 등)
        initial_cash: 초기 자본금 (원)
        config: 전략 설정 (None이면 기본값)
        max_position_pct: 종목당 최대 투자 비율 (0.2 = 20%)
        commission_rate: 수수료율 (0.00015 = 0.015%)

    Returns:
        BacktestResult
    """
    if config is None:
        config = StrategyConfig()

    # 날짜 기준 정렬 (과거 -> 현재)
    df = price_df.copy()
    for col in ["stck_bsop_date", "stck_clos_date", "date"]:
        if col in df.columns:
            df = df.sort_values(col).reset_index(drop=True)
            break

    closes = get_closing_prices(df)
    if closes.empty or len(closes) < config.rsi_period + 1:
        raise ValueError("데이터 부족 (RSI 기간+1일 이상 필요)")

    # 날짜 인덱스
    date_col = None
    for col in ["stck_bsop_date", "stck_clos_date", "date"]:
        if col in price_df.columns:
            date_col = col
            break
    dates = df[date_col].astype(str).tolist() if date_col else [str(i) for i in range(len(closes))]

    cash = initial_cash
    position_qty = 0
    position_avg_price = 0.0
    trades: List[Trade] = []
    equity_values: List[float] = []

    for i in range(len(closes)):
        price = float(closes.iloc[i])
        date_str = dates[i] if i < len(dates) else str(i)

        # RSI 계산 (과거 데이터만 사용)
        buy_price = position_avg_price if position_qty > 0 else None
        signal = _get_signal_for_day(closes, i, buy_price, config)

        rsi_val = None
        if i >= config.rsi_period:
            rsi_series = calculate_rsi_series(closes.iloc[: i + 1], config.rsi_period)
            rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None

        if signal == "buy" and position_qty == 0:
            investable = min(cash * max_position_pct, cash * 0.95)
            qty = int(investable / price)
            if qty > 0:
                cost = qty * price
                commission = cost * commission_rate
                cash -= cost + commission
                position_qty = qty
                position_avg_price = price
                pos_val = position_qty * price
                eq = cash + pos_val
                trades.append(
                    Trade(
                        date=date_str,
                        action="buy",
                        price=price,
                        qty=qty,
                        value=cost,
                        cash_after=cash,
                        position_value=pos_val,
                        total_equity=eq,
                        rsi=rsi_val,
                    )
                )

        elif signal == "sell" and position_qty > 0:
            sell_value = position_qty * price
            commission = sell_value * commission_rate
            cash += sell_value - commission
            trades.append(
                Trade(
                    date=date_str,
                    action="sell",
                    price=price,
                    qty=position_qty,
                    value=sell_value,
                    cash_after=cash,
                    position_value=0,
                    total_equity=cash,
                    rsi=rsi_val,
                )
            )
            position_qty = 0
            position_avg_price = 0.0

        pos_val = position_qty * price
        equity = cash + pos_val
        equity_values.append(equity)

    final_equity = cash + position_qty * float(closes.iloc[-1])
    total_return = final_equity - initial_cash
    total_return_pct = total_return / initial_cash if initial_cash > 0 else 0

    # 연율화 수익률 (거래일 기준, 252일/년)
    days = len(closes)
    annual_return_pct = None
    if days >= 1 and total_return_pct > -1:
        annual_return_pct = (1 + total_return_pct) ** (252 / days) - 1

    # 승률, Profit Factor
    sell_trades = [t for t in trades if t.action == "sell"]
    buy_trades = [t for t in trades if t.action == "buy"]
    num_trades = len(sell_trades) + len(buy_trades)

    win_trades = 0
    loss_trades = 0
    gross_profit = 0.0
    gross_loss = 0.0
    for i, sell in enumerate(sell_trades):
        if i < len(buy_trades):
            buy = buy_trades[i]
            pnl = (sell.price - buy.price) * sell.qty
            if pnl > 0:
                win_trades += 1
                gross_profit += pnl
            else:
                loss_trades += 1
                gross_loss += abs(pnl)
    win_rate = win_trades / len(sell_trades) if sell_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0)

    # 최대 낙폭 (MDD)
    equity_series = pd.Series(equity_values)
    cummax = equity_series.cummax()
    drawdown = (equity_series - cummax) / cummax.replace(0, 1e-10)
    max_drawdown_pct = float(drawdown.min())
    max_drawdown = float((equity_series - cummax).min())

    # 샤프 비율 (일간 수익률 기준, 무위험수익률 0 가정)
    daily_returns = equity_series.pct_change().dropna()
    sharpe_ratio = None
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe_ratio = float(daily_returns.mean() / daily_returns.std() * (252 ** 0.5))

    return BacktestResult(
        initial_cash=initial_cash,
        final_equity=final_equity,
        total_return=total_return,
        total_return_pct=total_return_pct,
        annual_return_pct=annual_return_pct,
        num_trades=num_trades,
        win_trades=win_trades,
        loss_trades=loss_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        sharpe_ratio=sharpe_ratio,
        trades=trades,
        equity_curve=equity_series,
    )
