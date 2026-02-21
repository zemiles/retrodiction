# -*- coding: utf-8 -*-
"""
백테스트 성과 지표 포맷팅 및 요약
"""

from typing import Optional

from .engine import BacktestResult


def format_result(result: BacktestResult) -> str:
    """백테스트 결과를 읽기 쉬운 문자열로 반환"""
    lines = [
        "=" * 50,
        "백테스트 결과",
        "=" * 50,
        f"초기 자본:     {result.initial_cash:,.0f} 원",
        f"최종 평가:     {result.final_equity:,.0f} 원",
        f"총 수익률:     {result.total_return_pct:.2%}",
        f"총 수익금:     {result.total_return:+,.0f} 원",
        "",
        "[거래 통계]",
        f"총 거래 횟수:  {result.num_trades}회",
        f"승리 거래:    {result.win_trades}회",
        f"패배 거래:    {result.loss_trades}회",
        f"승률:         {result.win_rate:.1%}",
        f"Profit Factor: {result.profit_factor:.2f}",
        "",
        "[리스크 지표]",
        f"최대 낙폭(MDD): {result.max_drawdown_pct:.2%}",
        f"샤프 비율:     {result.sharpe_ratio:.2f}" if result.sharpe_ratio is not None else "샤프 비율:     N/A",
        f"연율화 수익률: {result.annual_return_pct:.2%}" if result.annual_return_pct is not None else "연율화 수익률: N/A",
        "=" * 50,
    ]
    return "\n".join(lines)


def print_trade_log(result: BacktestResult, max_display: int = 20):
    """거래 내역 출력"""
    trades = result.trades
    if not trades:
        print("거래 내역 없음")
        return
    print("\n[거래 내역] (최근 %d건)" % min(max_display, len(trades)))
    for t in trades[-max_display:]:
        rsi_str = f" RSI={t.rsi:.1f}" if t.rsi is not None else ""
        print(f"  {t.date} {t.action:4} {t.qty:4}주 @ {t.price:,.0f} = {t.value:,.0f}원 | 잔고={t.total_equity:,.0f}{rsi_str}")
