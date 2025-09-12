import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from twintradeai.runner import run_engine_cycle, SYMBOLS
from twintradeai.risk_guard import RiskGuard
from twintradeai.position_manager import PositionManager


@pytest.fixture
def sample_df():
    """คืน DataFrame เล็ก ๆ ที่ไม่ empty"""
    return pd.DataFrame({"open": [1, 2], "close": [2, 3]})


class FakeAccountInfo:
    balance = 1000.0
    equity = 1000.0
    margin = 100.0
    margin_level = 200.0


def test_run_engine_cycle_skips_when_get_tf_data_none(sample_df):
    with patch("twintradeai.runner.get_tf_data", return_value=None):
        status = run_engine_cycle(RiskGuard(), PositionManager())
        assert status["count"] == 0


def test_run_engine_cycle_skips_when_get_tf_data_empty_df():
    empty_df = pd.DataFrame()
    with patch("twintradeai.runner.get_tf_data", return_value=empty_df):
        status = run_engine_cycle(RiskGuard(), PositionManager())
        assert status["count"] == 0


def test_run_engine_cycle_process_with_valid_df(sample_df):
    fake_sig = {
        "final_decision": "BLOCKED",
        "confidence": 50,
        "spread_pts": 10,
        "spread_limit": 20,
        "reasons": ["test"],
        "lot": 0.1,
        "entry": 1.2345,
        "sl": 1.2300,
        "tp1": 1.2400,
        "tp2": 1.2500,
        "tp3": 1.2600,
        "atr": 0.001,
    }

    with patch("twintradeai.runner.get_tf_data", return_value=sample_df), \
         patch("twintradeai.runner.build_signal", return_value=fake_sig), \
         patch("twintradeai.runner.mt5.symbol_info_tick", return_value=MagicMock()), \
         patch("twintradeai.runner.mt5.account_info", return_value=FakeAccountInfo()), \
         patch("twintradeai.runner.execute_order", return_value={"success": True, "orders": []}):
        status = run_engine_cycle(RiskGuard(), PositionManager())
        assert status["count"] == len(SYMBOLS)
        assert all("final_decision" in sig for sig in status["signals"])


def test_run_engine_cycle_triggers_execute_order_on_buy(sample_df):
    """
    ถ้า signal = BUY → ต้องเรียก execute_order อย่างน้อย 1 ครั้ง
    """
    fake_sig = {
        "final_decision": "BUY",
        "confidence": 90,
        "spread_pts": 5,
        "spread_limit": 20,
        "reasons": [],
        "lot": 0.1,
        "entry": 1.2345,
        "sl": 1.2300,
        "tp1": 1.2400,
        "tp2": 1.2500,
        "tp3": 1.2600,
        "atr": 0.001,
    }

    with patch("twintradeai.runner.get_tf_data", return_value=sample_df), \
         patch("twintradeai.runner.build_signal", return_value=fake_sig), \
         patch("twintradeai.runner.mt5.symbol_info_tick", return_value=MagicMock()), \
         patch("twintradeai.runner.mt5.account_info", return_value=FakeAccountInfo()), \
         patch("twintradeai.runner.execute_order", return_value={"success": True, "orders": []}) as mock_exec:

        run_engine_cycle(RiskGuard(), PositionManager())
        # ✅ ต้องถูกเรียกอย่างน้อย 1 ครั้ง
        assert mock_exec.called
