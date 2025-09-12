import pytest
from unittest.mock import patch, MagicMock
from twintradeai.position_manager import PositionManager


@pytest.fixture
def sample_positions():
    return [
        {
            "ticket": 1,
            "symbol": "EURUSDc",
            "type": "BUY",
            "price_open": 1.1000,
            "sl": 1.0980,
            "tp": 1.1020,
            "bid": 1.1035,   # ราคาล่าสุด bid
            "ask": 1.1037,   # ราคาล่าสุด ask
            "point": 0.0001
        },
        {
            "ticket": 2,
            "symbol": "XAUUSDc",
            "type": "SELL",
            "price_open": 1920.0,
            "sl": 1930.0,
            "tp": 1900.0,
            "bid": 1915.0,
            "ask": 1915.2,
            "point": 0.1
        },
    ]


def test_update_trailing_triggers_modify(sample_positions):
    pm = PositionManager(cooldown_minutes=0)

    # mock execution.modify_order
    with patch("twintradeai.position_manager.execution.modify_order") as mock_modify:
        mock_modify.return_value = MagicMock(retcode=10009)  # simulate success

        pm.update_trailing(
            sample_positions,
            tp_step_pips=20,
            trailing_start_pips=10,
            debug=True
        )

        # ✅ ต้องมีการเรียก modify_order อย่างน้อย 1 ครั้ง (เพราะ profit >= 10 pips)
        assert mock_modify.call_count >= 1

        # ตรวจสอบ arguments ของ call แรก
        args, kwargs = mock_modify.call_args
        assert "ticket" in kwargs
        assert "symbol" in kwargs
        assert "sl" in kwargs
        assert "tp" in kwargs


def test_update_trailing_no_trigger_when_profit_low():
    pm = PositionManager(cooldown_minutes=0)
    positions = [
        {
            "ticket": 3,
            "symbol": "GBPUSDc",
            "type": "BUY",
            "price_open": 1.2000,
            "sl": 1.1990,
            "tp": 1.2050,
            "bid": 1.2005,  # กำไรแค่ 5 pips < trailing_start_pips=10
            "ask": 1.2006,
            "point": 0.0001
        }
    ]

    with patch("twintradeai.position_manager.execution.modify_order") as mock_modify:
        pm.update_trailing(positions, tp_step_pips=20, trailing_start_pips=10, debug=True)

        # ✅ ไม่ควรถูกเรียกเพราะ profit ยังไม่ถึง
        mock_modify.assert_not_called()
