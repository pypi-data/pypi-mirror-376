import logging
import pandas as pd
from twintradeai.indicators import add_indicators, detect_bos


def scalp_score(df: pd.DataFrame, symbol: str, idx: int = -1):
    """
    คำนวณคะแนนสัญญาณสำหรับกลยุทธ์ scalp
    ใช้ indicators หลัก: EMA, RSI, MACD, BOS
    """
    score = 0
    checks = []
    reasons = []

    if len(df) < 50:
        return 0, ["insufficient_data"], ["Not enough bars"]

    row = df.iloc[idx]

    # === EMA Trend ===
    if row["ema20"] > row["ema50"]:
        score += 1
        checks.append("ema_up")
        reasons.append(f"EMA20 {row['ema20']:.5f} > EMA50 {row['ema50']:.5f}")
        logging.debug(f"[SCALP_DEBUG][{symbol}] EMA20={row['ema20']:.5f} > EMA50={row['ema50']:.5f} → ema_up")
    elif row["ema20"] < row["ema50"]:
        score -= 1
        checks.append("ema_down")
        reasons.append(f"EMA20 {row['ema20']:.5f} < EMA50 {row['ema50']:.5f}")
        logging.debug(f"[SCALP_DEBUG][{symbol}] EMA20={row['ema20']:.5f} < EMA50={row['ema50']:.5f} → ema_down")
    else:
        logging.debug(f"[SCALP_DEBUG][{symbol}] EMA neutral: EMA20={row['ema20']:.5f}, EMA50={row['ema50']:.5f}")

    # === RSI ===
    if row["rsi"] > 55:
        score += 1
        checks.append("rsi_bull")
        reasons.append(f"RSI bullish {row['rsi']:.1f} > 55")
    elif row["rsi"] < 45:
        score -= 1
        checks.append("rsi_bear")
        reasons.append(f"RSI bearish {row['rsi']:.1f} < 45")

    # === MACD ===
    if row["macd"] > row["macd_signal"]:
        score += 1
        checks.append("macd_bull")
        reasons.append(f"MACD bullish {row['macd']:.2f} > signal {row['macd_signal']:.2f}")
    elif row["macd"] < row["macd_signal"]:
        score -= 1
        checks.append("macd_bear")
        reasons.append(f"MACD bearish {row['macd']:.2f} < signal {row['macd_signal']:.2f}")

    # === Break of Structure (BOS) ===
    bos = detect_bos(df, swing_bars=20)
    if bos == "BOS_UP":
        score += 1
        checks.append("bos_up")
        reasons.append("Break of Structure UP")
    elif bos == "BOS_DOWN":
        score -= 1
        checks.append("bos_down")
        reasons.append("Break of Structure DOWN")

    return score, checks, reasons


def evaluate_scalp(df: pd.DataFrame, symbol: str,
                   threshold: int = 2,
                   min_conf: float = 60.0) -> dict:
    """
    ประเมินสัญญาณ scalp โดยใช้ scoring system
    คืนค่า dict: decision, score, confidence, reasons, checks
    """
    try:
        if "ema20" not in df.columns or "ema50" not in df.columns:
            df = add_indicators(df, symbol)

        score, checks, reasons = scalp_score(df, symbol, -1)
        last_price = float(df["close"].iloc[-1])

        # === ตัดสินใจเบื้องต้น ===
        decision = "HOLD"
        if score >= threshold:
            decision = "BUY"
        elif score <= -threshold:
            decision = "SELL"
        else:
            reasons.append(f"Score {score} < threshold={threshold}")

        # === Confidence ===
        conf = min(100.0, (abs(score) / threshold) * 100.0)

        # === Confidence gate ===
        final_decision = decision
        if conf < min_conf:
            final_decision = "HOLD"
            reasons.append(f"Confidence too low: {conf:.1f} < {min_conf}")

        logging.info(
            f"[SCALP_EVAL][{symbol}] {final_decision} | "
            f"Score={score} | Threshold={threshold} | "
            f"Confidence={conf:.1f}% (min={min_conf}%) | checks={checks}"
        )

        return {
            "symbol": symbol,
            "decision": decision,
            "final_decision": final_decision,
            "score": score,
            "threshold": threshold,
            "confidence": conf,
            "checks": checks,
            "price": last_price,
            "reasons": reasons,
        }

    except Exception as e:
        logging.error(f"[EVAL][{symbol}][scalp] error: {e}")
        return {
            "symbol": symbol,
            "decision": "HOLD",
            "final_decision": "HOLD",
            "score": 0,
            "threshold": threshold,
            "confidence": 0.0,
            "checks": ["error"],
            "price": None,
            "reasons": [str(e)],
        }
