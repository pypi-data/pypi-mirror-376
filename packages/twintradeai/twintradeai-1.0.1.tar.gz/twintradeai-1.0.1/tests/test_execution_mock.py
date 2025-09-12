import pytest
import numpy as np
import pandas as pd
import twintradeai.engine as engine
import twintradeai.execution as execution
from twintradeai.indicators import add_indicators


# ---------- Helpers ----------
class DummyTick:
    ask = 1.2100
    bid = 1.2095

class DummyAcc:
    balance = 10000.0

class DummyResult:
    def __init__(self, retcode=10009, order=1, deal=1):
        self.retcode = retcode
        self.order = order
        self.deal = deal


last_request = {}


def make_mock_df(rows=120):
    data = {
        "open": np.linspace(1.20, 1.25, rows),
        "high": np.linspace(1.21, 1.26, rows),
        "low": np.linspace(1.19, 1.24, rows),
        "close": np.linspace(1.20, 1.27, rows),
        "tick_volume": np.random.randint(100, 200, rows),
    }
    df = pd.DataFrame(data)
    return add_indicators(df, symbol="EURUSDc")


def mock_symbol_info(symbol):
    class Info:
        point = 0.0001
        digits = 5
        volume_min = 0.01
        volume_max = 100.0
        volume_step = 0.01
        trade_tick_value = 1.0
    return Info()

def mock_symbol_info_tick(symbol):
    return DummyTick()

def mock_order_send(req):
    global last_request
    last_request = req
    return DummyResult()


# ---------- Setup ----------
def setup_mt5(monkeypatch):
    monkeypatch.setattr(engine.mt5, "symbol_info", mock_symbol_info)
    monkeypatch.setattr(engine.mt5, "account_info", lambda : DummyAcc())
    monkeypatch.setattr(execution.mt5, "symbol_info", mock_symbol_info)
    monkeypatch.setattr(execution.mt5, "symbol_info_tick", mock_symbol_info_tick)
    monkeypatch.setattr(execution.mt5, "order_send", mock_order_send)


# ---------- Combined test ----------
symbols = ["EURUSDc", "NZDUSDc", "USDJPYc", "XAUUSDc", "BTCUSDc", "AUDUSDc"]
modes = ["scalp", "day", "swing", "mw", "mbb"]

@pytest.mark.parametrize("symbol", symbols)
@pytest.mark.parametrize("mode", modes)
def test_engine_execution_integration(monkeypatch, symbol, mode):
    setup_mt5(monkeypatch)

    m5, h1, h4 = make_mock_df(), make_mock_df(), make_mock_df()
    tick = DummyTick()

    # build signal
    sig = engine.build_signal(symbol, tick, m5, h1, h4, mode=mode, cfg={"spread_limit": 50})
    assert "decision" in sig
    assert "atr" in sig
    assert "lot" in sig

    if sig["decision"] in ("BUY", "SELL"):
        # try executing
        result = execution.execute_order(
            symbol,
            sig["decision"],
            sig["lot"],
            sig["entry"],
            sig["sl"],
            sig["tp1"],
            sig["tp2"],
            sig["tp3"],
        )
        assert result["success"] is True
        assert isinstance(result["orders"], list)


# ---------- Edge cases ----------
def test_confidence_filter(monkeypatch):
    setup_mt5(monkeypatch)

    m5, h1, h4 = make_mock_df(), make_mock_df(), make_mock_df()
    tick = DummyTick()

    sig = engine.build_signal(
        "EURUSDc",
        tick,
        m5,
        h1,
        h4,
        mode="scalp",
        cfg={"confidence_min": 200},  # impossible threshold
    )
    assert sig["decision"] == "HOLD"
    assert any("Confidence too low" in r for r in sig["reasons"])


def test_trailing_stop(monkeypatch):
    setup_mt5(monkeypatch)

    m5, h1, h4 = make_mock_df(), make_mock_df(), make_mock_df()
    tick = DummyTick()

    sig = engine.build_signal(
        "EURUSDc",
        tick,
        m5,
        h1,
        h4,
        mode="scalp",
        cfg={"trailing_atr_mult": 2.5},
    )
    assert sig["trailing_stop"] is not None
    assert sig["trailing_stop"] > 0
