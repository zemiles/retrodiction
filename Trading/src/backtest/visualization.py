# -*- coding: utf-8 -*-
"""
백테스트 결과 시각화
- 자산 곡선 vs 벤치마크(바닥)
- 낙폭(Drawdown) 차트
"""

import logging
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from ..data.indicators import get_closing_prices
from .engine import BacktestResult

import platform
if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
else:
    plt.rcParams["font.family"] = ["AppleGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

logger = logging.getLogger(__name__)


def plot_backtest_result(
    result: BacktestResult,
    price_df: Optional[pd.DataFrame] = None,
    stock_name: str = "종목",
    save_path: Optional[str] = None,
    figsize: tuple = (12, 8),
) -> None:
    """
    백테스트 결과 시각화
    - 상단: 자산 곡선 vs 보유(바닥) 수익률
    - 하단: 일별 낙폭(Drawdown)
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, height_ratios=[1.5, 1], sharex=True)
    fig.suptitle(f"{stock_name} - 백테스트 결과", fontsize=14, fontweight="bold")

    equity = result.equity_curve
    if equity.index.dtype == "int64" or isinstance(equity.index, pd.RangeIndex):
        x = equity.index
    else:
        x = equity.index

    # 1. 자산 곡선
    ax1 = axes[0]
    ax1.plot(x, equity.values, label="포트폴리오", color="#2E86AB", linewidth=2)
    ax1.axhline(y=result.initial_cash, color="#95A5A6", linestyle="--", alpha=0.6, label="초기자본")
    ax1.set_ylabel("자산 (원)", fontsize=10)
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)
    ax1.set_title("자산 곡선")

    # 2. 낙폭(Drawdown)
    ax2 = axes[1]
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax.replace(0, 1e-10)
    ax2.fill_between(x, drawdown.values, 0, color="#E74C3C", alpha=0.5)
    ax2.plot(x, drawdown.values, color="#C0392B", linewidth=1)
    ax2.set_ylabel("낙폭 (%)", fontsize=10)
    dd_min = float(drawdown.min())
    ax2.set_ylim(min(dd_min - 0.05, -0.5), 0.02)
    ax2.grid(True, alpha=0.3)
    ax2.set_title("일별 낙폭 (Drawdown)")

    plt.xlabel("기간", fontsize=10)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info("백테스트 차트 저장: %s", save_path)
    else:
        plt.show()
    plt.close()
