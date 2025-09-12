# tests/test_trailing_stop.py
import pytest
import pandas as pd
from snapshottest.pytest import PyTestSnapshotTest

import twintradeai.engine as engine


class DummyTick:
    def __init__(self, bid, ask):
        self.bid = bid
        self.ask = ask


class DummySymbolInfo:
    def __init__(self, point=0.0001, digits=5):
        self.point = point
        self.digits = digits


def make_dummy_df():
    """สร้าง DataFrame หลอกสำหรับ indicators"""
    data = {
        "open": [1.1, 1.2, 1.3, 1.25],
        "high": [1.2, 1.25, 1.35, 1.3],
        "low": [1.0, 1.15, 1.25, 1.2],
        "close": [1.15, 1.22, 1.28, 1.27],
        "time": pd.date_range("2024-01-01", periods=4, freq="T"),
    }
    df = pd.DataFrame(data)
    return engine.add_indicators(df, "DUMMY")


@pytest.fixture(autouse=True)
def patch_mt5(monkeypatch):
    """Mock MT5 calls"""
    monkeypatch.setattr(engine.mt5, "symbol_info", lambda sym: DummySymbolInfo())
    monkeypatch.setattr(engine.mt5, "symbol_info_tick", lambda sym: DummyTick(1.21, 1.22))


# ✅ ครอบคลุมครบทั้ง 6 สัญลักษณ์
@pytest.mark.parametrize("symbol", [
    "BTCUSDc", "XAUUSDc", "EURUSDc", "AUDUSDc", "NZDUSDc", "GBPUSDc"
])
def test_trailing_stop_applied(snapshot: PyTestSnapshotTest, symbol):
    """ทดสอบว่า SL/TP key มีเสมอ + snapshot test"""
    m5 = make_dummy_df()
    h1 = make_dummy_df()
    h4 = make_dummy_df()
    tick = DummyTick(1.21, 1.22)

    cfg = {
        "sl_atr": 2.0,
        "tp_atr": [1.0, 2.0, 3.0],
        "enable_trailing_stop": True,
        "trailing_atr_mult": 1.5,
        "strategies": {
            "scalp": {
                "weights": {"ema": 1.0, "atr": 1.0},
                "threshold": 2.0,
            }
        },
    }

    sig = engine.build_signal(symbol, tick, m5, h1, h4, cfg=cfg, mode="scalp")

    # ✅ ต้องมี key SL/TP เสมอ
    for key in ["sl", "tp1", "tp2", "tp3"]:
        assert key in sig

    # ✅ snapshot test (เฉพาะ field สำคัญ)
    snapshot.assert_match(
        {
            "symbol": sig["symbol"],
            "final_decision": sig["final_decision"],
            "sl": sig.get("sl"),
            "tp1": sig.get("tp1"),
            "tp2": sig.get("tp2"),
            "tp3": sig.get("tp3"),
            "confidence": sig.get("confidence"),
        },
        f"signal_snapshot_{symbol}"
    )
