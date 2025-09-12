# tests/test_lot_sizer.py
import pytest
from twintradeai.lot_sizer import LotSizer


def test_calculate_atr_and_lot_size():
    # สร้าง OHLC จำลอง (20 แท่ง)
    highs = [1.1200, 1.1210, 1.1220, 1.1230, 1.1240,
             1.1250, 1.1260, 1.1270, 1.1280, 1.1290,
             1.1300, 1.1310, 1.1320, 1.1330, 1.1340,
             1.1350, 1.1360, 1.1370, 1.1380, 1.1390]

    lows = [1.1180, 1.1190, 1.1200, 1.1210, 1.1220,
            1.1230, 1.1240, 1.1250, 1.1260, 1.1270,
            1.1280, 1.1290, 1.1300, 1.1310, 1.1320,
            1.1330, 1.1340, 1.1350, 1.1360, 1.1370]

    closes = [1.1190, 1.1200, 1.1210, 1.1220, 1.1230,
              1.1240, 1.1250, 1.1260, 1.1270, 1.1280,
              1.1290, 1.1300, 1.1310, 1.1320, 1.1330,
              1.1340, 1.1350, 1.1360, 1.1370, 1.1380]

    ls = LotSizer(account_balance=10000, risk_percent=1.0)

    atr = ls.calculate_atr(highs, lows, closes, period=14)
    assert atr > 0, "ATR should be positive"

    lot = ls.calc_lot("EURUSDc", atr_value=atr, pip_value=10.0)
    assert 0.01 <= lot <= 10.0, f"Lot {lot} out of range"

    # ความเสี่ยงสูงขึ้น → lot ไม่ควรลดลง
    ls_high_risk = LotSizer(account_balance=10000, risk_percent=5.0)
    lot_high = ls_high_risk.calc_lot("EURUSDc", atr_value=atr, pip_value=10.0)
    assert lot_high >= lot, "Higher risk_percent should not reduce lot size"

    # Balance สูงขึ้น → lot ไม่ควรลดลง
    ls.update_balance(20000)
    lot_bigger_balance = ls.calc_lot("EURUSDc", atr_value=atr, pip_value=10.0)
    assert lot_bigger_balance >= lot, "Bigger balance should not reduce lot size"


def test_invalid_inputs_return_min_lot():
    ls = LotSizer(account_balance=10000, risk_percent=1.0)

    # ATR = 0 → ต้อง return min_lot
    lot_atr0 = ls.calc_lot("EURUSDc", atr_value=0, pip_value=10.0, min_lot=0.01)
    assert lot_atr0 == 0.01

    # pip_value = 0 → ต้อง return min_lot
    lot_pip0 = ls.calc_lot("EURUSDc", atr_value=1.0, pip_value=0, min_lot=0.01)
    assert lot_pip0 == 0.01

    # ทั้ง ATR=0 และ pip=0 → ต้อง return min_lot
    lot_both0 = ls.calc_lot("EURUSDc", atr_value=0, pip_value=0, min_lot=0.01)
    assert lot_both0 == 0.01
