# -*- coding: utf-8 -*-
"""
한국투자증권 Open API 래퍼
- 현재가 조회 (inquire_price)
- 잔고 조회 (inquire_balance)
- 주문 (order_cash)
"""

import logging
from typing import Optional, Tuple

import pandas as pd

from . import kis_auth as ka

logger = logging.getLogger(__name__)

# API URL 상수
API_INQUIRE_PRICE = "/uapi/domestic-stock/v1/quotations/inquire-price"
API_INQUIRE_BALANCE = "/uapi/domestic-stock/v1/trading/inquire-balance"
API_ORDER_CASH = "/uapi/domestic-stock/v1/trading/order-cash"
API_INQUIRE_DAILY_CHART = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"


def inquire_daily_itemchartprice(
    stock_code: str,
    start_date: str,
    end_date: str,
    period: str = "D",
    market_code: str = "J",
) -> Optional[pd.DataFrame]:
    """
    국내주식 기간별 시세 (일/주/월/년)
    [국내주식] 기본시세 > 국내주식기간별시세

    Args:
        stock_code: 종목코드 6자리
        start_date: 조회 시작일 (YYYYMMDD)
        end_date: 조회 종료일 (YYYYMMDD, 최대 100건)
        period: D(일), W(주), M(월), Y(년)
        market_code: J(KRX)

    Returns:
        output2: 일별 시세 DataFrame (stck_clpr: 종가 등)
    """
    tr_id = "FHKST03010100"
    params = {
        "FID_COND_MRKT_DIV_CODE": market_code,
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": period,
        "FID_ORG_ADJ_PRC": "0",  # 수정주가
    }
    try:
        res = ka._url_fetch(API_INQUIRE_DAILY_CHART, tr_id, "", params)
        if res.is_ok():
            body = res.get_body()
            o2 = body.output2
            if o2:
                return pd.DataFrame(o2 if isinstance(o2, list) else [o2])
        else:
            res.print_error(API_INQUIRE_DAILY_CHART)
    except Exception as e:
        logger.exception("기간별 시세 조회 오류: %s", e)
    return None


def inquire_price(stock_code: str, market_code: str = "J") -> Optional[pd.DataFrame]:
    """
    주식 현재가 시세 조회
    [국내주식] 기본시세 > 주식현재가 시세

    Args:
        stock_code: 종목코드 6자리 (예: 005930)
        market_code: J(KRX), NX(NXT), UN(통합)

    Returns:
        현재가 시세 DataFrame, 실패 시 None
    """
    tr_id = "FHKST01010100"
    params = {
        "FID_COND_MRKT_DIV_CODE": market_code,
        "FID_INPUT_ISCD": stock_code,
    }
    try:
        res = ka._url_fetch(API_INQUIRE_PRICE, tr_id, "", params)
        if res.is_ok():
            output = res.get_body().output
            if output:
                return pd.DataFrame([output] if isinstance(output, dict) else output)
        else:
            res.print_error(API_INQUIRE_PRICE)
    except Exception as e:
        logger.exception("현재가 조회 오류: %s", e)
    return None


def inquire_balance(
    afhr_flpr_yn: str = "N",
    inqr_dvsn: str = "01",
    prcs_dvsn: str = "00",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    주식 잔고 조회
    [국내주식] 주문/계좌 > 주식잔고조회

    Args:
        afhr_flpr_yn: N(기본), Y(시간외단일가), X(NXT)
        inqr_dvsn: 01(대출일별), 02(종목별)
        prcs_dvsn: 00(전일매매포함), 01(전일매매미포함)

    Returns:
        (output1: 예수금/총평가 등, output2: 잔고목록)
    """
    trenv = ka.get_trenv()
    tr_id = "TTTC8434R"
    params = {
        "CANO": trenv.my_acct,
        "ACNT_PRDT_CD": trenv.my_prod,
        "AFHR_FLPR_YN": afhr_flpr_yn,
        "OFL_YN": "",
        "INQR_DVSN": inqr_dvsn,
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": prcs_dvsn,
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    try:
        res = ka._url_fetch(API_INQUIRE_BALANCE, tr_id, "", params)
        if res.is_ok():
            body = res.get_body()
            o1 = body.output1
            o2 = body.output2
            df1 = pd.DataFrame([o1] if isinstance(o1, dict) else (o1 or []))
            df2 = pd.DataFrame(o2 if isinstance(o2, list) else ([o2] if o2 else []))
            return df1, df2
        else:
            res.print_error(API_INQUIRE_BALANCE)
    except Exception as e:
        logger.exception("잔고 조회 오류: %s", e)
    return pd.DataFrame(), pd.DataFrame()


def order_cash(
    ord_dv: str,
    pdno: str,
    ord_qty: str,
    ord_unpr: str,
    ord_dvsn: str = "00",
    excg_id_dvsn_cd: str = "KRX",
) -> Optional[pd.DataFrame]:
    """
    주식 주문 (현금)
    [국내주식] 주문/계좌 > 주식주문(현금)

    Args:
        ord_dv: "buy"(매수) | "sell"(매도)
        pdno: 종목코드 6자리
        ord_qty: 주문수량 (문자열)
        ord_unpr: 주문단가 (문자열)
        ord_dvsn: 00(보통), 01(시장가) 등
        excg_id_dvsn_cd: KRX

    Returns:
        주문 결과 DataFrame, 실패 시 None
    """
    trenv = ka.get_trenv()
    tr_id = "TTTC0011U" if ord_dv == "sell" else "TTTC0012U"
    params = {
        "CANO": trenv.my_acct,
        "ACNT_PRDT_CD": trenv.my_prod,
        "PDNO": pdno,
        "ORD_DVSN": ord_dvsn,
        "ORD_QTY": str(ord_qty),
        "ORD_UNPR": str(ord_unpr),
        "EXCG_ID_DVSN_CD": excg_id_dvsn_cd,
        "SLL_TYPE": "",
        "CNDT_PRIC": "",
    }
    try:
        res = ka._url_fetch(API_ORDER_CASH, tr_id, "", params, post_flag=True)
        if res.is_ok():
            output = res.get_body().output
            if output:
                return pd.DataFrame([output] if isinstance(output, dict) else output)
        else:
            res.print_error(API_ORDER_CASH)
    except Exception as e:
        logger.exception("주문 오류: %s", e)
    return None


def get_current_price(stock_code: str) -> Optional[float]:
    """
    종목 현재가만 반환 (편의 함수)
    API 응답: stck_prpr(주식현재가)

    Returns:
        현재가 (float), 실패 시 None
    """
    df = inquire_price(stock_code)
    if df is not None and not df.empty:
        for col in ["stck_prpr", "prpr"]:
            if col in df.columns:
                try:
                    val = df[col].iloc[0]
                    return float(str(val).replace(",", ""))
                except (ValueError, TypeError):
                    pass
    return None


def get_available_cash() -> Optional[float]:
    """
    예수금(매수 가능 금액) 반환
    output1: ord_psbl_cash(주문가능현금), dnca_tot_amt(예수금총액)

    Returns:
        예수금 (float), 실패 시 None
    """
    df1, _ = inquire_balance()
    if df1 is not None and not df1.empty:
        for col in ["ord_psbl_cash", "dnca_tot_amt"]:
            if col in df1.columns:
                try:
                    val = df1[col].iloc[0]
                    return float(str(val).replace(",", ""))
                except (ValueError, TypeError):
                    pass
    return None
