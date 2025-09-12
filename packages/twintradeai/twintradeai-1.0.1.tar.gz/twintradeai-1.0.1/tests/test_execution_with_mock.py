import pytest
from twintradeai import execution


# ✅ symbols ที่ใช้ทดสอบ
symbols = ["EURUSDc", "NZDUSDc", "USDJPYc", "XAUUSDc", "BTCUSDc", "AUDUSDc"]

# ✅ BUY/SELL matrix
cases = [(s, d) for s in symbols for d in ["BUY", "SELL"]]


@pytest.mark.parametrize("symbol,decision", cases)
def test_execute_order_all_symbols(dummy_mt5, dummy_execution, symbol, decision):
    """
    ✅ ทดสอบ execute_order() ครอบคลุมทุกสัญลักษณ์
    - mock mt5 ผ่าน dummy_mt5
    - mock order_send ผ่าน dummy_execution
    - ตรวจสอบว่า request ที่ส่งออกไปถูกต้อง
    """
    if decision == "BUY":
        sl, tp1, tp2, tp3 = 1.2000, 1.2200, 1.2300, 1.2400
    else:
        sl, tp1, tp2, tp3 = 1.2200, 1.2000, 1.1900, 1.1800

    result = execution.execute_order(
        symbol=symbol,
        decision=decision,
        lot=0.2,
        entry=1.2100,
        sl=sl,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
    )

    # ✅ ต้อง success
    assert result["success"]
    assert len(result["orders"]) > 0

    # ✅ ตรวจสอบ request ล่าสุด
    req = dummy_execution()
    assert req["symbol"] == symbol
    assert "TwinTradeAi" in req["comment"]

    if decision == "BUY":
        assert req["type"] == execution.mt5.ORDER_TYPE_BUY
    else:
        assert req["type"] == execution.mt5.ORDER_TYPE_SELL
