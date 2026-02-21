# -*- coding: utf-8 -*-
"""
장 시간 스케줄러
- 한국 주식장: 09:00 ~ 15:30
"""

from datetime import datetime, time


def is_market_open() -> bool:
    """현재 장 중인지 확인"""
    now = datetime.now().time()
    return time(9, 0) <= now <= time(15, 30)


def is_market_closing_soon() -> bool:
    """장 마감 임박 (15:20 이후) - 신규 매수 중단"""
    now = datetime.now().time()
    return now >= time(15, 20)


def get_market_status() -> str:
    """장 상태 문자열"""
    if is_market_closing_soon():
        return "장마감임박"
    if is_market_open():
        return "장중"
    return "장종료"
