# -*- coding: utf-8 -*-
"""
한국투자증권 Open API 인증 모듈
- 토큰 발급 및 갱신
- API 호출 공통 함수
- 실전/모의투자 환경 전환
"""

import copy
import json
import logging
import os
import time
from collections import namedtuple
from datetime import datetime

import requests
import yaml

# 프로젝트 루트 기준 config 경로
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONFIG_DIR = os.path.join(_PROJECT_ROOT, "config")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "kis_devlp.yaml")
_TOKEN_DIR = os.path.join(_CONFIG_DIR, "tokens")
_TOKEN_FILE = os.path.join(_TOKEN_DIR, f"KIS{datetime.today().strftime('%Y%m%d')}.yaml")

_TRENV = None
_last_auth_time = datetime.now()
_is_paper = False
_smart_sleep = 0.1

# 설정 로드
def _load_config():
    """kis_devlp.yaml 설정 로드"""
    if not os.path.exists(_CONFIG_PATH):
        raise FileNotFoundError(
            f"설정 파일을 찾을 수 없습니다: {_CONFIG_PATH}\n"
            "kis_devlp.yaml.example을 kis_devlp.yaml로 복사한 후 앱키를 입력하세요."
        )
    with open(_CONFIG_PATH, encoding="UTF-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)

_CFG = _load_config()

# 기본 헤더
_base_headers = {
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "charset": "UTF-8",
    "User-Agent": _CFG.get("my_agent", "Mozilla/5.0"),
}


def _ensure_token_dir():
    """토큰 저장 디렉토리 생성"""
    os.makedirs(_TOKEN_DIR, exist_ok=True)


def save_token(token: str, expired: str):
    """토큰 저장"""
    _ensure_token_dir()
    valid_date = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
    with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(f"token: {token}\n")
        f.write(f"valid-date: {valid_date}\n")


def read_token() -> str | None:
    """저장된 토큰 확인 (만료 전이면 반환)"""
    if not os.path.exists(_TOKEN_FILE):
        return None
    try:
        with open(_TOKEN_FILE, encoding="UTF-8") as f:
            tkg = yaml.load(f, Loader=yaml.FullLoader)
        exp_dt = datetime.strftime(tkg["valid-date"], "%Y-%m-%d %H:%M:%S")
        now_dt = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        if exp_dt > now_dt:
            return tkg["token"]
    except Exception:
        pass
    return None


def _set_trenv(cfg: dict):
    """거래 환경 설정"""
    global _TRENV
    nt = namedtuple(
        "KISEnv",
        ["my_app", "my_sec", "my_acct", "my_prod", "my_htsid", "my_token", "my_url"],
    )
    _TRENV = nt(
        my_app=cfg["my_app"],
        my_sec=cfg["my_sec"],
        my_acct=cfg["my_acct"],
        my_prod=cfg["my_prod"],
        my_htsid=cfg["my_htsid"],
        my_token=cfg["my_token"],
        my_url=cfg["my_url"],
    )


def is_paper_trading() -> bool:
    """모의투자 여부"""
    return _is_paper


def auth(svr: str = "vps", product: str = "01"):
    """
    인증 및 토큰 발급
    svr: "prod"(실전) | "vps"(모의)
    product: "01"(종합계좌)
    """
    global _last_auth_time, _is_paper, _smart_sleep

    cfg = {}
    if svr == "prod":
        cfg["my_app"] = _CFG["my_app"]
        cfg["my_sec"] = _CFG["my_sec"]
        cfg["my_acct"] = _CFG["my_acct_stock"] if product == "01" else _CFG["my_acct_future"]
        _is_paper = False
        _smart_sleep = 0.05
    elif svr == "vps":
        cfg["my_app"] = _CFG["paper_app"]
        cfg["my_sec"] = _CFG["paper_sec"]
        cfg["my_acct"] = _CFG["my_paper_stock"] if product == "01" else _CFG["my_paper_future"]
        _is_paper = True
        _smart_sleep = 0.5
    else:
        raise ValueError("svr은 'prod' 또는 'vps'여야 합니다.")

    cfg["my_prod"] = product
    cfg["my_htsid"] = _CFG["my_htsid"]

    # 기존 토큰 확인
    saved_token = read_token()
    if saved_token is None:
        url = f"{_CFG[svr]}/oauth2/tokenP"
        p = {
            "grant_type": "client_credentials",
            "appkey": cfg["my_app"],
            "appsecret": cfg["my_sec"],
        }
        res = requests.post(url, data=json.dumps(p), headers=_base_headers)
        if res.status_code != 200:
            raise RuntimeError(f"토큰 발급 실패: {res.text}")
        data = res.json()
        saved_token = data["access_token"]
        save_token(saved_token, data["access_token_token_expired"])

    cfg["my_token"] = saved_token
    cfg["my_url"] = _CFG[svr]
    _set_trenv(cfg)

    _base_headers["authorization"] = f"Bearer {saved_token}"
    _base_headers["appkey"] = _TRENV.my_app
    _base_headers["appsecret"] = _TRENV.my_sec
    _last_auth_time = datetime.now()

    logging.info(f"인증 완료 (모드: {'모의투자' if _is_paper else '실전투자'})")


def get_trenv():
    """현재 거래 환경 반환"""
    if _TRENV is None:
        raise RuntimeError("auth()를 먼저 호출하세요.")
    return _TRENV


def smart_sleep():
    """API 호출 간격 조절"""
    time.sleep(_smart_sleep)


class APIResp:
    """API 응답 래퍼 - 한국투자증권 API 응답 구조 지원"""

    def __init__(self, resp: requests.Response):
        self._rescode = resp.status_code
        self._resp = resp
        self._data = resp.json()

    def get_res_code(self):
        return self._rescode

    def get_header(self):
        """헤더 정보 (tr_cont 등) - namedtuple 형태"""
        h = self._resp.headers
        return namedtuple("header", ["tr_cont"])(tr_cont=h.get("tr_cont", ""))

    def get_body(self):
        """바디 - output, output1, output2, ctx_area_fk100, ctx_area_nk100 등 접근 가능"""
        d = self._data
        # 동적 속성 접근을 위한 객체
        class Body:
            pass
        body = Body()
        for k, v in d.items():
            setattr(body, k.lower().replace("-", "_"), v)
        # output, output1, output2 등
        if "output" in d:
            body.output = d["output"]
        else:
            body.output = None
        if "output1" in d:
            body.output1 = d["output1"]
        else:
            body.output1 = None
        if "output2" in d:
            body.output2 = d["output2"]
        else:
            body.output2 = None
        body.ctx_area_fk100 = d.get("ctx_area_fk100", "")
        body.ctx_area_nk100 = d.get("ctx_area_nk100", "")
        body.rt_cd = d.get("rt_cd", "")
        body.msg_cd = d.get("msg_cd", "")
        body.msg1 = d.get("msg1", "")
        return body

    def is_ok(self) -> bool:
        return self._data.get("rt_cd") == "0"

    def get_error_code(self):
        return self._data.get("msg_cd", "")

    def get_error_message(self):
        return self._data.get("msg1", "")

    def print_error(self, url: str = ""):
        logging.error(
            f"API 오류 - code: {self.get_error_code()}, msg: {self.get_error_message()}, url: {url}"
        )


def _url_fetch(api_url: str, tr_id: str, tr_cont: str, params: dict, post_flag: bool = False):
    """
    REST API 호출
    모의투자 시 TR_ID 자동 변환 (T -> V)
    """
    trenv = get_trenv()
    url = f"{trenv.my_url}{api_url}"

    # 모의투자 시 TR_ID 변환
    if tr_id[0] in ("T", "J", "C") and is_paper_trading():
        tr_id = "V" + tr_id[1:]

    headers = copy.deepcopy(_base_headers)
    headers["tr_id"] = tr_id
    headers["custtype"] = "P"
    headers["tr_cont"] = tr_cont

    if post_flag:
        res = requests.post(url, headers=headers, data=json.dumps(params))
    else:
        res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        return APIResp(res)
    logging.error(f"API HTTP 오류: {res.status_code} - {res.text}")
    raise RuntimeError(f"API 호출 실패: {res.text}")
