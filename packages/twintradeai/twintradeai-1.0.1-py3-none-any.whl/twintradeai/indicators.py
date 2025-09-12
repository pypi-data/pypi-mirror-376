import pandas as pd
import numpy as np
import logging


# ================== ATR ==================
def compute_atr(df: pd.DataFrame, period: int = 14, symbol: str = None) -> pd.Series:
    """คำนวณ ATR (Wilder's EMA) พร้อม safe fallback"""
    try:
        prev_close = df["close"].shift(1)
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs()
        ], axis=1).max(axis=1)

        atr = tr.ewm(alpha=1/period, min_periods=period).mean()

        # Replace invalids
        atr = atr.replace([np.inf, -np.inf], np.nan).ffill().bfill()

        # Symbol-specific safety floor
        if symbol:
            if "XAU" in symbol:   # Gold
                atr = atr.clip(lower=0.1)
            elif "BTC" in symbol:  # Crypto
                atr = atr.clip(lower=10.0)
            elif "EUR" in symbol or "USD" in symbol:  # Forex majors
                atr = atr.clip(lower=0.0001)

        return atr

    except Exception as e:
        logging.error(f"[ATR] calc error: {e}")
        return pd.Series([1.0] * len(df), index=df.index)  # safe default


# ================== BOS ==================
def detect_bos(df: pd.DataFrame, swing_bars: int = 20):
    """
    ตรวจสอบ Break of Structure (BOS)
    - close >= recent_high → BOS_UP
    - close <= recent_low → BOS_DOWN
    """
    if df is None or len(df) < swing_bars:
        return None

    recent_high = df["high"].iloc[-swing_bars:].max()
    recent_low = df["low"].iloc[-swing_bars:].min()
    close = df["close"].iloc[-1]

    if close >= recent_high:   # ✅ แก้จาก > เป็น >=
        return "BOS_UP"
    elif close <= recent_low:  # ✅ แก้จาก < เป็น <=
        return "BOS_DOWN"
    return None


# ================== Indicators ==================
def add_indicators(df: pd.DataFrame, symbol: str = None) -> pd.DataFrame:
    """เพิ่ม indicators หลัก พร้อม safe fallback"""
    try:
        # EMA
        df["ema20"] = df["close"].ewm(span=20, min_periods=20).mean()
        df["ema50"] = df["close"].ewm(span=50, min_periods=50).mean()

        # ATR (safe)
        df["atr"] = compute_atr(df, 14, symbol=symbol)

        # RSI (safe, with extreme case handling)
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, min_periods=14).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.replace(np.inf, 100).replace(-np.inf, 0)  # extreme up/down
        df["rsi"] = rsi.fillna(50).clip(0, 100)

        # MACD (safe)
        ema12 = df["close"].ewm(span=12, min_periods=12).mean()
        ema26 = df["close"].ewm(span=26, min_periods=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, min_periods=9).mean()
        df["macd"] = macd.ffill().bfill()
        df["macd_signal"] = signal.ffill().bfill()
        df["macd_hist"] = (macd - signal).ffill().bfill()

        # Bollinger Bands
        df["bb_mid"] = df["close"].rolling(20, min_periods=20).mean()
        df["bb_std"] = df["close"].rolling(20, min_periods=20).std().fillna(0.0)
        df["bb_upper"] = df["bb_mid"] + 2 * df["bb_std"]
        df["bb_lower"] = df["bb_mid"] - 2 * df["bb_std"]

        # Stochastic Oscillator (safe)
        low_min = df["low"].rolling(14, min_periods=14).min()
        high_max = df["high"].rolling(14, min_periods=14).max()
        stoch_k = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
        df["stoch_k"] = stoch_k.fillna(50)
        df["stoch_d"] = df["stoch_k"].rolling(3, min_periods=3).mean().fillna(50)

        # VWAP (with typical price fallback)
        if "tick_volume" in df.columns:
            cum_vol = df["tick_volume"].cumsum().replace(0, np.nan)
            cum_vp = (df["close"] * df["tick_volume"]).cumsum()
            df["vwap"] = (cum_vp / cum_vol).fillna(df["close"])
        else:
            typical_price = (df["high"] + df["low"] + df["close"]) / 3
            cum_tp = typical_price.cumsum()
            cum_count = pd.Series(range(1, len(df) + 1), index=df.index)
            df["vwap"] = (cum_tp / cum_count).fillna(df["close"])

        # Williams %R (14)
        highest_high = df["high"].rolling(14, min_periods=14).max()
        lowest_low = df["low"].rolling(14, min_periods=14).min()
        willr = -100 * (highest_high - df["close"]) / (highest_high - lowest_low).replace(0, np.nan)
        df["williams_r"] = willr.fillna(0.0).clip(-100, 0)

        return df

    except Exception as e:
        logging.error(f"[INDICATORS] error: {e}")
        return df
