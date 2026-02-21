# -*- coding: utf-8 -*-
"""
Trading 봇 HTTP API 서버
- Retrodiction 화면에서 상태/설정/백테스트 조회 및 제어
"""

import logging
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime, timedelta

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Flask는 api_server 전용이므로 여기서만 import
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

# 로그 버퍼 (최근 200줄)
LOG_BUFFER = deque(maxlen=200)


class BufferHandler(logging.Handler):
    """로그를 메모리에 저장하는 핸들러"""

    def emit(self, record):
        try:
            msg = self.format(record)
            LOG_BUFFER.append({"time": datetime.now().isoformat(), "level": record.levelname, "msg": msg})
        except Exception:
            pass


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
root_logger = logging.getLogger()
handler = BufferHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)

# 트레이딩 루프 제어
_trading_running = False
_trading_thread = None
_trading_stop_flag = threading.Event()


def get_config_path():
    return os.path.join(os.path.dirname(__file__), "config", "settings.yaml")


def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return None
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_trading_loop():
    """백그라운드에서 트레이딩 루프 실행"""
    global _trading_running
    try:
        from src.api import kis_auth
        from src.scheduler.market_scheduler import is_market_closing_soon, is_market_open

        config = load_config()
        if not config:
            logger.error("설정 파일 없음")
            return

        mode = config.get("mode", "vps")
        kis_auth.auth(svr=mode, product="01")
        logger.info("트레이딩 루프 시작 (모드: %s)", "모의투자" if kis_auth.is_paper_trading() else "실전투자")

        from main import run_trading_cycle

        interval = config["risk"].get("check_interval_seconds", 60)

        while _trading_running and not _trading_stop_flag.is_set():
            try:
                run_trading_cycle(config)
            except Exception as e:
                logger.exception("사이클 오류: %s", e)
            for _ in range(interval):
                if not _trading_running or _trading_stop_flag.is_set():
                    break
                time.sleep(1)
    except Exception as e:
        logger.exception("트레이딩 루프 오류: %s", e)
    finally:
        _trading_running = False
        logger.info("트레이딩 루프 종료")


# === API 엔드포인트 ===


@app.route("/health")
def health():
    """헬스체크"""
    return jsonify({"status": "ok", "service": "trading-bot", "timestamp": datetime.now().isoformat()})


@app.route("/status")
def status():
    """상태 조회 (설정 요약, 민감정보 제외)"""
    config = load_config()
    if not config:
        return jsonify({"error": "설정 파일 없음"}), 500

    return jsonify({
        "mode": config.get("mode", "vps"),
        "modeLabel": "모의투자" if config.get("mode") == "vps" else "실전투자",
        "stocks": config.get("stocks", []),
        "strategy": config.get("strategy", {}),
        "risk": {
            "max_position_per_stock": config.get("risk", {}).get("max_position_per_stock"),
            "check_interval_seconds": config.get("risk", {}).get("check_interval_seconds"),
        },
        "tradingRunning": _trading_running,
    })


@app.route("/config", methods=["GET"])
def get_config():
    """설정 조회"""
    config = load_config()
    if not config:
        return jsonify({"error": "설정 파일 없음"}), 500
    return jsonify(config)


@app.route("/config", methods=["POST"])
def update_config():
    """설정 업데이트 (일부 필드만)"""
    config = load_config()
    if not config:
        return jsonify({"error": "설정 파일 없음"}), 500

    data = request.get_json() or {}
    for key in ["strategy", "stocks", "risk", "mode"]:
        if key in data:
            config[key] = data[key]

    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    return jsonify({"ok": True, "config": config})


@app.route("/backtest", methods=["POST"])
def run_backtest():
    """백테스트 실행"""
    try:
        from src.api import kis_auth
        from src.api import korea_investment as api
        from src.backtest.engine import run_backtest as _run_backtest
        from src.strategy.rsi_strategy import StrategyConfig

        config = load_config()
        if not config:
            return jsonify({"error": "설정 파일 없음"}), 500

        mode = config.get("mode", "vps")
        kis_auth.auth(svr=mode, product="01")

        strategy_cfg = StrategyConfig(
            rsi_period=config["strategy"]["rsi_period"],
            buy_threshold=config["strategy"]["buy_threshold"],
            sell_threshold=config["strategy"]["sell_threshold"],
            stop_loss=config["strategy"]["stop_loss"],
            take_profit=config["strategy"]["take_profit"],
        )
        bt_cfg = config.get("backtest", {})
        initial_cash = bt_cfg.get("initial_cash", 10_000_000)
        max_position_pct = bt_cfg.get("max_position_pct", 0.2)
        commission_rate = bt_cfg.get("commission_rate", 0.00015)
        days = bt_cfg.get("days", 100)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)
        start_str = start_dt.strftime("%Y%m%d")
        end_str = end_dt.strftime("%Y%m%d")

        STOCK_NAMES = {"005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", "051910": "LG화학", "006400": "삼성SDI"}

        results = []
        for stock_code in config["stocks"]:
            try:
                price_df = api.inquire_daily_itemchartprice(stock_code, start_str, end_str)
                if price_df is None or price_df.empty:
                    continue
                result = _run_backtest(
                    price_df=price_df,
                    initial_cash=initial_cash,
                    config=strategy_cfg,
                    max_position_pct=max_position_pct,
                    commission_rate=commission_rate,
                )
                name = STOCK_NAMES.get(stock_code, stock_code)
                results.append({
                    "stockCode": stock_code,
                    "stockName": name,
                    "totalReturnPct": result.total_return_pct,
                    "winRate": result.win_rate,
                    "numTrades": result.num_trades,
                    "maxDrawdownPct": result.max_drawdown_pct,
                })
                kis_auth.smart_sleep()
            except Exception as e:
                logger.warning("백테스트 %s 실패: %s", stock_code, e)

        return jsonify({"ok": True, "results": results})
    except Exception as e:
        logger.exception("백테스트 오류: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/logs")
def get_logs():
    """최근 로그 조회"""
    limit = request.args.get("limit", 100, type=int)
    limit = min(limit, 200)
    logs = list(LOG_BUFFER)[-limit:]
    return jsonify({"logs": logs})


@app.route("/trading/start", methods=["POST"])
def trading_start():
    """트레이딩 루프 시작"""
    global _trading_running, _trading_thread
    if _trading_running:
        return jsonify({"ok": False, "message": "이미 실행 중입니다"}), 400
    _trading_stop_flag.clear()
    _trading_running = True
    _trading_thread = threading.Thread(target=run_trading_loop, daemon=True)
    _trading_thread.start()
    return jsonify({"ok": True, "message": "트레이딩 시작됨"})


@app.route("/trading/stop", methods=["POST"])
def trading_stop():
    """트레이딩 루프 중지"""
    global _trading_running
    _trading_stop_flag.set()
    _trading_running = False
    return jsonify({"ok": True, "message": "트레이딩 중지 요청됨"})


@app.route("/charts/<path:filename>")
def serve_chart(filename):
    """차트 이미지 제공"""
    charts_dir = os.path.join(os.path.dirname(__file__), "charts_output")
    if not os.path.exists(charts_dir):
        return jsonify({"error": "charts_output 없음"}), 404
    return send_from_directory(charts_dir, filename)


@app.route("/charts")
def list_charts():
    """저장된 차트 목록"""
    charts_dir = os.path.join(os.path.dirname(__file__), "charts_output")
    if not os.path.exists(charts_dir):
        return jsonify({"charts": []})
    files = [f for f in os.listdir(charts_dir) if f.endswith(".png")]
    return jsonify({"charts": files})


if __name__ == "__main__":
    port = int(os.environ.get("TRADING_API_PORT", 5000))
    logger.info("Trading API 서버 시작: http://localhost:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
