import pytest
import pandas as pd
import numpy as np
import logging

from twintradeai import evaluate_scalp, add_indicators

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [TEST][%(levelname)s] %(message)s")


def make_df(prices: list[float], symbol="EURUSDc") -> pd.DataFrame:
    """
    สร้าง DataFrame mock สำหรับทดสอบ
    """
    n = len(prices)
    df = pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=n, freq="M"),
        "open": prices,
        "high": [p * 1.001 for p in prices],
        "low": [p * 0.999 for p in prices],
        "close": prices,
        "tick_volume": np.random.randint(50, 200, size=n),
    })
    return add_indicators(df, symbol)


def log_checks(result: dict):
    """
    พิมพ์รายละเอียด per-check สำหรับ debug
    """
    logging.debug(f"Decision={result['decision']}, Score={result['score']}, Conf={result['confidence']}")
    for check in result.get("checks", []):
        logging.debug(f"  Passed: {check}")
    if not result.get("checks"):
        logging.debug("  No checks passed")


def test_scalp_buy_signal():
    prices = [1.10 + 0.001 * i for i in range(100)]  # แนวโน้มขึ้น
    df = make_df(prices, "EURUSDc")

    result = evaluate_scalp(df, "EURUSDc", threshold=2, min_conf=60)
    log_checks(result)

    assert result["decision"] in ("BUY", "HOLD")
    assert result["score"] >= 0


def test_scalp_sell_signal():
    prices = [1.30 - 0.001 * i for i in range(100)]  # แนวโน้มลง
    df = make_df(prices, "EURUSDc")

    result = evaluate_scalp(df, "EURUSDc", threshold=2, min_conf=60)
    log_checks(result)

    assert result["decision"] in ("SELL", "HOLD")
    assert result["score"] <= 0


def test_scalp_insufficient_data():
    prices = [1.10 + 0.001 * i for i in range(10)]  # ข้อมูลน้อยเกินไป
    df = make_df(prices, "EURUSDc")

    result = evaluate_scalp(df, "EURUSDc", threshold=2, min_conf=60)
    log_checks(result)

    assert result["decision"] == "HOLD"
    assert "insufficient_data" in result["checks"] or result["score"] == 0
