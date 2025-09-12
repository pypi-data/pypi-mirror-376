# tests/test_lot_sizer.py
import pytest
from twintradeai.lot_sizer import LotSizer

symbols = ["BTCUSDc", "XAUUSDc", "EURUSDc", "AUDUSDc"]


def test_integration_all_symbols_with_clamps():
    """
    Integration test ครอบคลุมทุก symbol:
    - ATR ถูกคำนวณ
    - lot อยู่ในช่วง min_lot-max_lot
    - balance เพิ่มขึ้น → lot เพิ่มขึ้น (หรือโดน clamp ที่ max_lot)
    - balance เล็กมาก → lot ถูก clamp ขึ้นมาเป็น min_lot
    - balance ใหญ่มาก → lot ถูก clamp ลงมาเป็น max_lot
    """

    highs = [i for i in range(20, 40)]
    lows = [i - 1 for i in range(20, 40)]
    closes = [i - 0.5 for i in range(20, 40)]

    # 1) Case ปกติ → balance ปานกลาง
    ls = LotSizer(account_balance=5000, risk_percent=2.0, min_lot=0.05, max_lot=5.0)
    atr = ls.calculate_atr(highs, lows, closes, period=10)
    assert atr > 0

    for symbol in symbols:
        lot1 = ls.calc_lot(symbol, atr_value=atr, pip_value=5.0)
        assert ls.min_lot <= lot1 <= ls.max_lot

        ls.update_balance(10000)
        lot2 = ls.calc_lot(symbol, atr_value=atr, pip_value=5.0)

        # lot ต้องเพิ่มขึ้น หรือเท่าเดิมถ้าโดน clamp
        assert lot2 >= lot1
        if lot2 == lot1:
            assert lot2 == ls.max_lot

    # 2) Case balance เล็กมาก → clamp ที่ min_lot
    ls_small = LotSizer(account_balance=100, risk_percent=1.0, min_lot=0.05, max_lot=10.0)
    atr_small = ls_small.calculate_atr(highs, lows, closes, period=10)
    assert atr_small > 0

    for symbol in symbols:
        lot_small = ls_small.calc_lot(symbol, atr_value=atr_small, pip_value=50.0)
        assert lot_small == pytest.approx(ls_small.min_lot)

    # 3) Case balance ใหญ่มาก → clamp ที่ max_lot
    ls_big = LotSizer(account_balance=1_000_000, risk_percent=10.0, min_lot=0.01, max_lot=2.0)
    atr_big = ls_big.calculate_atr(highs, lows, closes, period=10)
    assert atr_big > 0

    for symbol in symbols:
        lot_big = ls_big.calc_lot(symbol, atr_value=atr_big, pip_value=0.01)
        assert lot_big == pytest.approx(ls_big.max_lot)
