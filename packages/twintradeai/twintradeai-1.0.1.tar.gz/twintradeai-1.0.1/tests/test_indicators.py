import pytest
import pandas as pd
import numpy as np
from twintradeai.indicators import add_indicators, compute_atr
from twintradeai.scalp_evaluator import evaluate_scalp   # ✅ เพิ่มตรงนี้


# -----------------------------
# Helper: สร้าง dummy DataFrame
# -----------------------------
def make_dummy_df(prices: list[float]) -> pd.DataFrame:
    n = len(prices)
    df = pd.DataFrame({
        "open": prices,
        "high": [p * 1.01 for p in prices],
        "low": [p * 0.99 for p in prices],
        "close": prices,
        "tick_volume": np.random.randint(100, 200, n)
    })
    return add_indicators(df, symbol="EURUSDc")


# -----------------------------
# Tests
# -----------------------------
def test_buy_signal():
    # สร้างราคาขึ้น → EMA20 > EMA50, RSI สูง, MACD bullish
    prices = np.linspace(1.1000, 1.1200, 100)  # ขึ้นชัดเจน
    df = make_dummy_df(prices)

    signal = evaluate_scalp(df, "EURUSDc", threshold=2)
    assert signal["decision"] == "BUY"
    assert signal["score"] >= 2
    assert "ema_up" in signal["checks"]
    assert "rsi_bull" in signal["checks"]


def test_sell_signal():
    # สร้างราคาลง → EMA20 < EMA50, RSI ต่ำ, MACD bearish
    prices = np.linspace(1.1200, 1.1000, 100)  # ลงชัดเจน
    df = make_dummy_df(prices)

    signal = evaluate_scalp(df, "EURUSDc", threshold=2)
    assert signal["decision"] == "SELL"
    assert signal["score"] <= -2
    assert "ema_down" in signal["checks"]
    assert "rsi_bear" in signal["checks"]


def test_hold_signal():
    # สร้างราคาคงที่ → ไม่มี indicator ไหนแรงพอ
    prices = [1.1100] * 100  # sideway
    df = make_dummy_df(prices)

    signal = evaluate_scalp(df, "EURUSDc", threshold=2)
    assert signal["decision"] == "HOLD"
    assert abs(signal["score"]) < 2
