import logging
import time
import json
from datetime import datetime
import os
from pathlib import Path

import MetaTrader5 as mt5
import zmq

from twintradeai.engine import get_tf_data, build_signal, SYM_CFG
from twintradeai.risk_guard import RiskGuard
from twintradeai.execution import execute_order
from twintradeai.position_manager import PositionManager

# ========= CONFIG =========
SYMBOLS = ["BTCUSDc", "XAUUSDc", "EURUSDc", "AUDUSDc", "NZDUSDc", "GBPUSDc"]
ENGINE_STATUS_FILE = "engine_status.json"

ZMQ_PUB_URL = os.getenv("ZMQ_PUB_URL", "tcp://127.0.0.1:7000")
ZMQ_TOPIC = os.getenv("ZMQ_TOPIC", "signals")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RUNNER][%(levelname)s] %(message)s"
)

# ========= TEST-FRIENDLY PUB =========
class DummyPub:
    def __init__(self):
        self.sent = []

    def send_multipart(self, data):
        self.sent.append(data)


if os.getenv("REAL_MODE") == "1":
    zmq_ctx = zmq.Context()
    zmq_pub = zmq_ctx.socket(zmq.PUB)
else:
    zmq_pub = DummyPub()

# ========= Helpers =========
def write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        logging.error(f"[RUNNER] write_json error: {e}")


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_engine_status(path: str = None):
    target = path or ENGINE_STATUS_FILE
    return read_json(target, default={"last_update": None, "count": 0, "signals": []})


# ========= MAIN ENGINE CYCLE =========
def run_engine_cycle(risk_guard=None, pos_manager=None, zmq_pub=None, zmq_topic=None):
    risk_guard = risk_guard or RiskGuard()
    pos_manager = pos_manager or PositionManager(cooldown_minutes=15)

    all_signals = []
    for sym in SYMBOLS:
        tick = mt5.symbol_info_tick(sym)
        if not tick:
            logging.warning(f"[{sym}] No tick data")
            continue

        m5 = get_tf_data(sym, mt5.TIMEFRAME_M5)
        h1 = get_tf_data(sym, mt5.TIMEFRAME_H1)
        h4 = get_tf_data(sym, mt5.TIMEFRAME_H4)

        # ✅ ป้องกัน error DataFrame truth value
        if (
            m5 is None or getattr(m5, "empty", True)
            or h1 is None or getattr(h1, "empty", True)
            or h4 is None or getattr(h4, "empty", True)
        ):
            logging.warning(f"[{sym}] Missing timeframe data (skip)")
            continue

        cfg = SYM_CFG.get(sym, {})
        mode = cfg.get("mode", "scalp")
        sig = build_signal(sym, tick, m5, h1, h4, cfg=cfg, mode=mode)

        if sig is None:
            continue

        logging.info(
            f"[{sym}] mode={mode} final={sig.get('final_decision')} "
            f"confidence={sig.get('confidence', 0)}% "
            f"spread={sig.get('spread_pts')} pts "
            f"(limit={sig.get('spread_limit')}) "
            f"reason={','.join(sig.get('reasons', [])) or 'ok'}"
        )

        check_result = risk_guard.check(
            sym, sig.get("atr", 0), sig.get("spread_pts", 0), account=mt5.account_info()
        )

        if not check_result.get("allowed", False):
            sig["final_decision"] = "BLOCKED"
            sig.setdefault("reasons", []).extend([f"RISK: {r}" for r in check_result.get("reasons", [])])

        if sig["final_decision"] in ("BUY", "SELL") and check_result.get("allowed", False):
            allowed, reason = pos_manager.can_trade(sym, sig["final_decision"])
            if not allowed:
                sig["final_decision"] = "BLOCKED"
                sig.setdefault("reasons", []).append(f"PM: {reason}")

        if sig["final_decision"] in ("BUY", "SELL"):
            result = execute_order(
                sym, sig["final_decision"], sig["lot"],
                sig["entry"], sig["sl"], sig["tp1"], sig["tp2"], sig["tp3"]
            )
            if result.get("success", False):
                pos_manager.lock(sym, sig["final_decision"])
                pos_manager.set_cooldown(sym)

        all_signals.append(sig)

    engine_status = {
        "last_update": datetime.utcnow().isoformat(),
        "count": len(all_signals),
        "signals": all_signals,
    }

    if zmq_pub and zmq_topic:
        msg = json.dumps(engine_status, ensure_ascii=False, default=str).encode()
        zmq_pub.send_multipart([zmq_topic.encode(), msg])
        logging.info(f"[ZMQ] Published {len(all_signals)} signals to {zmq_topic}")

    return engine_status


# ========= ENTRY POINT =========
if __name__ == "__main__":
    logging.info("🔧 Booting TwinTradeAi runner ...")

    if not mt5.initialize():
        code, msg = mt5.last_error()
        logging.error(f"❌ MT5 initialize failed: code={code}, msg={msg}")
        exit(1)

    risk_guard = RiskGuard()
    pos_manager = PositionManager(cooldown_minutes=15)

    if isinstance(zmq_pub, DummyPub) is False:
        zmq_pub.connect(ZMQ_PUB_URL)

    while True:
        engine_status = run_engine_cycle(risk_guard, pos_manager, zmq_pub, ZMQ_TOPIC)
        write_json(ENGINE_STATUS_FILE, engine_status)
        logging.info(f"[RUNNER] Updated {ENGINE_STATUS_FILE} with {engine_status['count']} signals")

        # ✅ เรียก update_trailing ทุก loop
        positions = []
        raw_positions = mt5.positions_get()
        if raw_positions:
            for pos in raw_positions:
                info = mt5.symbol_info(pos.symbol)
                tick = mt5.symbol_info_tick(pos.symbol)
                if not info or not tick:
                    continue
                positions.append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL",
                    "price_open": pos.price_open,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "point": info.point,
                })
        if positions:
            pos_manager.update_trailing(
                positions,
                tp_step_pips=20,
                trailing_start_pips=10
            )

        time.sleep(60)
