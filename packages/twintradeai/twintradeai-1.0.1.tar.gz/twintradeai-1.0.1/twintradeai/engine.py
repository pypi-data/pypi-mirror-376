import os
import yaml
import logging
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd

from twintradeai.indicators import add_indicators, detect_bos
from twintradeai.risk_guard import RiskGuard
from twintradeai.lot_sizer import LotSizer
from twintradeai.scalp_evaluator import evaluate_scalp   # ✅ ใช้ evaluator แยก

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ENGINE][%(levelname)s] %(message)s"
)

# =========================
# CONFIG
# =========================
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.symbols.yaml")

def load_symbol_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"[ENGINE] load_symbol_cfg error: {e}")
            return {}
    return {}

SYM_CFG = load_symbol_cfg()

# =========================
# INIT RiskGuard
# =========================
risk_guard = RiskGuard()

# =========================
# HELPERS
# =========================
def round_to_point(symbol, price: float):
    try:
        info = mt5.symbol_info(symbol)
        if not info:
            return float(price)
        p = info.point
        return round(round(float(price) / p) * p, info.digits)
    except Exception:
        return float(price)

def get_tf_data(symbol: str, timeframe, bars: int = 200):
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) < 50:
            logging.warning(f"[ENGINE] Not enough bars for {symbol} tf={timeframe}")
            return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df = add_indicators(df, symbol)
        return df
    except Exception as e:
        logging.error(f"[ENGINE] get_tf_data error {symbol}: {e}")
        return None

# =========================
# STRATEGY EVALUATOR
# =========================
def evaluate_strategy(symbol, df, cfg, mode="scalp"):
    """
    - scalp → ใช้ evaluate_scalp จาก scalp_evaluator.py + normalize checks/reasons
    - mode อื่น → ใช้ evaluator logic เดิม
    Always return 4 values: (decision, reasons, checks, confidence)
    """
    if mode == "scalp":
        strat_cfg = cfg.get("strategies", {}).get("scalp", {})
        threshold = strat_cfg.get("threshold", 2.0)
        min_conf = cfg.get("confidence_min", 0)
        result = evaluate_scalp(df, symbol, threshold, min_conf)

        # === Normalize checks ===
        norm_checks = {}
        for k in result["checks"]:
            if k.startswith("ema"):
                norm_checks["ema"] = True
            elif k.startswith("rsi"):
                norm_checks["rsi"] = True
            elif k.startswith("macd"):
                norm_checks["macd"] = True
            elif k.startswith("bos"):
                norm_checks["bos"] = True
            else:
                norm_checks[k] = True

        # === Normalize reasons ===
        reasons = result["reasons"][:]
        if result["final_decision"] == "HOLD" and f"Score {result['score']}" not in " ".join(reasons):
            reasons.append(f"Score {result['score']} < threshold={result['threshold']}")

        return result["final_decision"], reasons, norm_checks, result["confidence"]

    # === evaluator เดิมสำหรับ day/swing/mw/mbb ===
    strat_cfg = cfg.get("strategies", {}).get(mode, {})
    weights = strat_cfg.get("weights", {})
    threshold = strat_cfg.get("threshold", 2.0)

    score = 0.0
    reasons, checks = [], {}
    decision = "HOLD"

    # === Indicators ===
    ema20 = df["ema20"].iloc[-1] if "ema20" in df else None
    ema50 = df["ema50"].iloc[-1] if "ema50" in df else None
    atr_val = float(df["atr"].iloc[-1]) if "atr" in df else None
    stoch_k = df["stoch_k"].iloc[-1] if "stoch_k" in df else None
    stoch_d = df["stoch_d"].iloc[-1] if "stoch_d" in df else None
    vwap_val = df["vwap"].iloc[-1] if "vwap" in df else None
    wr_val = df["williams_r"].iloc[-1] if "williams_r" in df else None
    bos_val = detect_bos(df, cfg.get("swing_bars", 20)) if "bos" in weights else None
    bb_upper = df["bb_upper"].iloc[-1] if "bb_upper" in df else None
    bb_lower = df["bb_lower"].iloc[-1] if "bb_lower" in df else None
    price = df["close"].iloc[-1]

    # === EMA trend ===
    if "ema" in weights and ema20 is not None and ema50 is not None:
        if ema20 > ema50:
            decision = "BUY"; checks["ema"] = True; reasons.append("EMA20 > EMA50")
            score += 1
        elif ema20 < ema50:
            decision = "SELL"; checks["ema"] = True; reasons.append("EMA20 < EMA50")
            score -= 1

    # === ATR ===
    if "atr" in weights and atr_val is not None and atr_val > 0:
        checks["atr"] = True; reasons.append(f"ATR {atr_val:.2f}")
        score += 1

    # === Stochastic ===
    if "stoch" in weights and stoch_k is not None and stoch_d is not None:
        if decision == "BUY" and stoch_k > stoch_d:
            checks["stoch"] = True; reasons.append("Stoch bullish"); score += 1
        elif decision == "SELL" and stoch_k < stoch_d:
            checks["stoch"] = True; reasons.append("Stoch bearish"); score -= 1

    # === VWAP ===
    if "vwap" in weights and vwap_val is not None:
        if decision == "BUY" and price > vwap_val:
            checks["vwap"] = True; reasons.append("Price > VWAP"); score += 1
        elif decision == "SELL" and price < vwap_val:
            checks["vwap"] = True; reasons.append("Price < VWAP"); score -= 1

    # === Williams %R ===
    if "williams_r" in weights and wr_val is not None:
        if decision == "BUY" and wr_val > -80:
            checks["williams_r"] = True; reasons.append("W%R bullish"); score += 1
        elif decision == "SELL" and wr_val < -20:
            checks["williams_r"] = True; reasons.append("W%R bearish"); score -= 1

    # === BOS ===
    if "bos" in weights and bos_val is not None:
        if decision == "BUY" and bos_val == "BOS_UP":
            checks["bos"] = True; reasons.append("BOS_UP"); score += 1
        elif decision == "SELL" and bos_val == "BOS_DOWN":
            checks["bos"] = True; reasons.append("BOS_DOWN"); score -= 1

    # === Bollinger Bands ===
    if "bb" in weights and bb_upper is not None and bb_lower is not None:
        if decision == "BUY" and price <= bb_lower:
            checks["bb"] = True; reasons.append("Price near BB lower"); score += 1
        elif decision == "SELL" and price >= bb_upper:
            checks["bb"] = True; reasons.append("Price near BB upper"); score -= 1

    # === Threshold ===
    if -threshold < score < threshold:
        decision = "HOLD"
        reasons.append(f"Score {score:.1f} < threshold={threshold}")

    # === Fallback EMA cross ===
    if score == 0 and ema20 is not None and ema50 is not None:
        if ema20 > ema50:
            decision = "BUY"; checks["ema"] = True; score += 1
            reasons.append(f"{mode.upper()}: EMA20 > EMA50 (fallback)")
        elif ema20 < ema50:
            decision = "SELL"; checks["ema"] = True; score -= 1
            reasons.append(f"{mode.upper()}: EMA20 < EMA50 (fallback)")

    # === Confidence ===
    total_weight = sum(weights.values()) or 1.0
    conf_raw = 0.0
    for k, w in weights.items():
        if k in checks:
            conf_raw += w
    confidence = (conf_raw / total_weight) * 100.0
    confidence_min = cfg.get("confidence_min", 0)

    final_decision = decision
    if confidence < confidence_min:
        reasons.append(f"Confidence too low: {confidence:.1f} < {confidence_min}")
        final_decision = "HOLD"

    logging.info(
        f"[EVAL][{symbol}][{mode}] {final_decision} | "
        f"Score={score:.1f} | Threshold={threshold} | "
        f"Confidence={confidence:.1f}% (min={confidence_min}%) | checks: {list(checks.keys()) or '-'}"
    )

    return final_decision, reasons, checks, confidence

# =========================
# LOT SIZE
# =========================
def compute_dynamic_lot(symbol, entry, sl, atr, cfg):
    acc = mt5.account_info()
    balance = getattr(acc, "balance", 1000.0)
    return LotSizer(balance).compute(symbol, entry, sl, atr, cfg)

# =========================
# BUILD SIGNAL
# =========================
def build_signal(symbol, tick, m5, h1, h4, cfg=None, mode="scalp"):
    cfg = cfg or SYM_CFG.get(symbol, {})
    reasons, checks = [], {}
    decision = "HOLD"
    trailing_stop_points = trailing_stop_price = None

    df = m5
    if mode == "day":
        df = h1
    elif mode == "swing":
        df = h4

    if df is None:
        return {"symbol": symbol, "mode": mode, "decision": "HOLD", "reasons": ["No data"]}

    decision, reasons, checks, confidence = evaluate_strategy(symbol, df, cfg, mode)
    atr = float(df["atr"].iloc[-1]) if "atr" in df else 0.0

    entry = sl = tp1 = tp2 = tp3 = None
    if decision in ("BUY", "SELL"):
        entry = tick.ask if decision == "BUY" else tick.bid
        sl_mult = cfg.get("sl_atr", 2.0)
        tp_mults = cfg.get("tp_atr", [1.0, 2.0, 3.0])
        recent_low = df["low"].iloc[-20:].min()
        recent_high = df["high"].iloc[-20:].max()

        if decision == "BUY":
            sl = min(entry - atr * sl_mult, recent_low)
            tps = [entry + atr * m for m in tp_mults]
            tps[0] = max(tps[0], recent_high)
        else:
            sl = max(entry + atr * sl_mult, recent_high)
            tps = [entry - atr * m for m in tp_mults]
            tps[0] = min(tps[0], recent_low)

        entry = round_to_point(symbol, entry)
        sl = round_to_point(symbol, sl)
        tp1, tp2, tp3 = [round_to_point(symbol, t) for t in tps]

    # === Lot sizing ===
    lot = 0.01
    if decision in ("BUY", "SELL"):
        lot = compute_dynamic_lot(symbol, entry, sl, atr, cfg)

    spread_pts = (tick.ask - tick.bid) / mt5.symbol_info(symbol).point if mt5.symbol_info(symbol) else None
    spread_limit = cfg.get("spread_limit", None)

    if spread_limit is not None and spread_pts is not None and spread_pts > spread_limit:
        logging.info(f"[BUILD_SIGNAL] {symbol} skipped: spread={spread_pts:.1f} > limit={spread_limit}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "mode": mode,
            "decision": "HOLD",
            "final_decision": "HOLD",
            "confidence": confidence,
            "reasons": reasons + [f"Spread too high: {spread_pts:.1f} > {spread_limit}"],
            "entry": None, "sl": None, "tp1": None, "tp2": None, "tp3": None,
            "atr": atr, "lot": lot, "checks": checks,
            "spread_pts": spread_pts, "spread_limit": spread_limit,
        }

    # === Trailing stop ===
    trailing_mult = cfg.get("trailing_atr_mult", None)
    if trailing_mult:
        trailing_stop_points = round_to_point(symbol, atr * trailing_mult)
        if decision == "BUY":
            trailing_stop_price = entry - trailing_stop_points
        elif decision == "SELL":
            trailing_stop_price = entry + trailing_stop_points

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "mode": mode,
        "decision": decision,
        "final_decision": decision,
        "confidence": confidence,
        "reasons": reasons,
        "entry": entry, "sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3,
        "atr": atr, "lot": lot, "checks": checks,
        "spread_pts": spread_pts, "spread_limit": spread_limit,
        "trailing_stop": trailing_stop_points,
        "trailing_stop_price": trailing_stop_price,
    }

# =========================
# BUILD ALL SIGNALS
# =========================
def build_all_signals(symbol, tick, m5, h1, h4, cfg=None):
    cfg = cfg or SYM_CFG.get(symbol, {})
    signals = []
    for mode in cfg.get("strategies", {}).keys():
        sig = build_signal(symbol, tick, m5, h1, h4, cfg, mode)
        signals.append(sig)
    return signals
