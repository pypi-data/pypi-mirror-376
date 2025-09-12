import pytest
import pandas as pd
from twintradeai.engine import evaluate_strategy


@pytest.fixture
def base_df():
    """สร้าง DataFrame 60 rows พร้อม indicators mock"""
    data = {
        "time": pd.date_range("2024-01-01", periods=60, freq="T"),
        "close": [1.10 + i * 0.001 for i in range(60)],
        "open": [1.10 + i * 0.001 for i in range(60)],
        "high": [1.10 + i * 0.0015 for i in range(60)],
        "low": [1.10 + i * 0.0005 for i in range(60)],
        "tick_volume": [100] * 60,
    }
    df = pd.DataFrame(data)

    # ค่า default
    df["ema20"] = df["close"]
    df["ema50"] = df["close"]
    df["macd"] = 0.0
    df["macd_signal"] = 0.0
    df["rsi"] = 50.0
    return df


def test_scalp_buy_signal(base_df):
    df = base_df.copy()
    # Force BUY
    df["ema20"] = df["close"] + 0.05
    df["ema50"] = df["close"] - 0.05
    df["rsi"] = 60.0
    df["macd"] = 2.0
    df["macd_signal"] = 1.0

    cfg = {
        "confidence_min": 55,
        "strategies": {"scalp": {"threshold": 2, "weights": {"ema": 1.0, "macd": 1.0, "rsi": 1.0}}},
    }
    decision, reasons, checks, confidence = evaluate_strategy("TEST", df, cfg, "scalp")

    assert decision == "BUY"
    assert set(checks.keys()) >= {"ema", "rsi", "macd"}
    assert any("EMA" in r or "Price >" in r for r in reasons)
    assert any("RSI" in r for r in reasons)
    assert any("MACD" in r for r in reasons)
    assert confidence >= 55


def test_scalp_sell_signal(base_df):
    df = base_df.copy()
    # Force SELL
    df["ema20"] = df["close"] - 0.05
    df["ema50"] = df["close"] + 0.05
    df["rsi"] = 40.0
    df["macd"] = -2.0
    df["macd_signal"] = -1.0

    cfg = {
        "confidence_min": 55,
        "strategies": {"scalp": {"threshold": 2, "weights": {"ema": 1.0, "macd": 1.0, "rsi": 1.0}}},
    }
    decision, reasons, checks, confidence = evaluate_strategy("TEST", df, cfg, "scalp")

    assert decision == "SELL"
    assert set(checks.keys()) >= {"ema", "rsi", "macd"}
    assert any("EMA" in r or "Price <" in r for r in reasons)
    assert any("RSI" in r for r in reasons)
    assert any("MACD" in r for r in reasons)
    assert confidence >= 55
