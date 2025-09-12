import pandas as pd
from twintradeai.indicators import detect_bos


def test_bos_up():
    # last close ทะลุ recent high → BOS_UP
    prices = [1, 1, 1, 1.2, 1.3, 1.4, 1.6]
    df = pd.DataFrame({
        "high": prices,
        "low": [p - 0.05 for p in prices],
        "close": prices,
    })
    bos = detect_bos(df, swing_bars=5)
    assert bos == "BOS_UP"


def test_bos_down():
    # last close ทะลุ recent low → BOS_DOWN
    prices = [1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 0.8]
    df = pd.DataFrame({
        "high": [p + 0.05 for p in prices],
        "low": prices,
        "close": prices,
    })
    bos = detect_bos(df, swing_bars=5)
    assert bos == "BOS_DOWN"


def test_bos_none():
    # ไม่มี break → None
    prices = [1.1] * 30
    df = pd.DataFrame({
        "high": [p + 0.05 for p in prices],
        "low": [p - 0.05 for p in prices],
        "close": prices,
    })
    bos = detect_bos(df, swing_bars=10)
    assert bos is None
