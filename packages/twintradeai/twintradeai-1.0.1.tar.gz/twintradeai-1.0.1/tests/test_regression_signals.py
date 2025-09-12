import pytest
import numpy as np
import pandas as pd

from twintradeai.engine import build_signal
from twintradeai.indicators import add_indicators


# ---------- Helpers ----------
class DummyTick:
    ask = 1.2100
    bid = 1.2095


def make_mock_df(rows=120, bias="buy"):
    """Generate synthetic OHLCV + indicators, force BUY/SELL bias"""
    data = {
        "open": np.linspace(1.20, 1.25, rows),
        "high": np.linspace(1.21, 1.26, rows),
        "low": np.linspace(1.19, 1.24, rows),
        "close": np.linspace(1.20, 1.27, rows),
        "tick_volume": np.random.randint(100, 200, rows),
    }
    df = pd.DataFrame(data)
    df = add_indicators(df, symbol="EURUSDc")

    # === Force deterministic signals for evaluator ===
    if bias == "buy":
        df["ema20"] = df["close"] + 0.05
        df["ema50"] = df["close"] - 0.05
        df["rsi"] = 60.0
        df["macd"] = 2.0
        df["macd_signal"] = 1.0
    elif bias == "sell":
        df["ema20"] = df["close"] - 0.05
        df["ema50"] = df["close"] + 0.05
        df["rsi"] = 40.0
        df["macd"] = -2.0
        df["macd_signal"] = -1.0
    else:
        df["ema20"] = df["close"]
        df["ema50"] = df["close"]
        df["rsi"] = 50.0
        df["macd"] = 0.0
        df["macd_signal"] = 0.0

    return df


# ---------- Regression tests ----------
@pytest.mark.parametrize("mode", ["scalp", "day", "swing", "mw", "mbb"])
@pytest.mark.parametrize("symbol", ["BTCUSDc", "XAUUSDc", "EURUSDc", "AUDUSDc", "NZDUSDc", "GBPUSDc"])
def test_build_signal_modes_buy(snapshot, monkeypatch, mode, symbol):
    """Regression test: build_signal works consistently for BUY bias"""

    import twintradeai.engine as engine

    class DummyInfo:
        point = 0.0001
        digits = 5
        volume_min = 0.01
        volume_max = 100.0
        volume_step = 0.01
        trade_tick_value = 1.0

    monkeypatch.setattr(engine.mt5, "symbol_info", lambda s: DummyInfo())
    monkeypatch.setattr(engine.mt5, "account_info", lambda: type("Acc", (), {"balance": 10000.0})())

    # prepare data (force BUY bias)
    m5 = make_mock_df(bias="buy")
    h1 = make_mock_df(bias="buy")
    h4 = make_mock_df(bias="buy")
    tick = DummyTick()

    sig = build_signal(symbol, tick, m5, h1, h4, mode=mode, cfg={"spread_limit": 20})

    snapshot.assert_match(
        {k: sig[k] for k in ["symbol", "mode", "decision", "confidence", "atr", "lot"]},
        f"signal_{symbol}_{mode}_buy.json"
    )

    assert sig["decision"] in ("BUY", "HOLD")
    assert isinstance(sig["reasons"], list)
    assert isinstance(sig["checks"], dict)


@pytest.mark.parametrize("mode", ["scalp", "day", "swing", "mw", "mbb"])
@pytest.mark.parametrize("symbol", ["BTCUSDc", "XAUUSDc", "EURUSDc", "AUDUSDc", "NZDUSDc", "GBPUSDc"])
def test_build_signal_modes_sell(snapshot, monkeypatch, mode, symbol):
    """Regression test: build_signal works consistently for SELL bias"""

    import twintradeai.engine as engine

    class DummyInfo:
        point = 0.0001
        digits = 5
        volume_min = 0.01
        volume_max = 100.0
        volume_step = 0.01
        trade_tick_value = 1.0

    monkeypatch.setattr(engine.mt5, "symbol_info", lambda s: DummyInfo())
    monkeypatch.setattr(engine.mt5, "account_info", lambda: type("Acc", (), {"balance": 10000.0})())

    # prepare data (force SELL bias)
    m5 = make_mock_df(bias="sell")
    h1 = make_mock_df(bias="sell")
    h4 = make_mock_df(bias="sell")
    tick = DummyTick()

    sig = build_signal(symbol, tick, m5, h1, h4, mode=mode, cfg={"spread_limit": 20})

    snapshot.assert_match(
        {k: sig[k] for k in ["symbol", "mode", "decision", "confidence", "atr", "lot"]},
        f"signal_{symbol}_{mode}_sell.json"
    )

    assert sig["decision"] in ("SELL", "HOLD")
    assert isinstance(sig["reasons"], list)
    assert isinstance(sig["checks"], dict)


def test_build_signal_spread_filter(monkeypatch):
    """Check spread filter forces HOLD when exceeded"""

    import twintradeai.engine as engine

    class DummyInfo:
        point = 0.0001
        digits = 5
        volume_min = 0.01
        volume_max = 100.0
        volume_step = 0.01
        trade_tick_value = 1.0

    monkeypatch.setattr(engine.mt5, "symbol_info", lambda s: DummyInfo())
    monkeypatch.setattr(engine.mt5, "account_info", lambda: type("Acc", (), {"balance": 10000.0})())

    class WideTick:
        ask = 1.3000
        bid = 1.2000  # spread = 1000 points!

    m5 = make_mock_df(bias="buy")
    h1 = make_mock_df(bias="buy")
    h4 = make_mock_df(bias="buy")

    sig = build_signal("EURUSDc", WideTick(), m5, h1, h4, mode="scalp", cfg={"spread_limit": 20})

    assert sig["decision"] == "HOLD"
    assert any("Spread too high" in r for r in sig["reasons"])
