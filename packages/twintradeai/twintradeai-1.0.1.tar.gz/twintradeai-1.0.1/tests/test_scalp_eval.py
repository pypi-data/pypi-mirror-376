import pandas as pd
from twintradeai.scalp_evaluator import evaluate_scalp

# ==============================
# Mock DataFrame
# ==============================
def make_mock_df(ema20, ema50, rsi, macd, macd_signal, close=100, bos=None):
    """สร้าง DataFrame mock 50 rows โดย row สุดท้ายมีค่าที่เรากำหนด"""
    rows = 50
    data = {
        "close": [close] * rows,
        "ema20": [ema20] * rows,
        "ema50": [ema50] * rows,
        "rsi": [rsi] * rows,
        "macd": [macd] * rows,
        "macd_signal": [macd_signal] * rows,
        "high": [close + 1] * rows,
        "low": [close - 1] * rows,
    }
    df = pd.DataFrame(data)
    return df

# ==============================
# Run test cases
# ==============================
def run_tests():
    cases = [
        # Expect BUY: EMA20 > EMA50, RSI > 55, MACD > Signal
        ("BUY case", make_mock_df(ema20=105, ema50=100, rsi=70, macd=1.2, macd_signal=0.8)),

        # Expect SELL: EMA20 < EMA50, RSI < 45, MACD < Signal
        ("SELL case", make_mock_df(ema20=95, ema50=100, rsi=30, macd=-1.0, macd_signal=-0.5)),

        # Expect HOLD: mixed signals (RSI neutral, MACD neutral)
        ("HOLD case", make_mock_df(ema20=100, ema50=100, rsi=50, macd=0.5, macd_signal=0.5)),
    ]

    for name, df in cases:
        result = evaluate_scalp(df, "MOCK", threshold=2, min_conf=60)
        print(f"\n{name}:")
        print(f"  decision={result['decision']} final={result['final_decision']} "
              f"score={result['score']} conf={result['confidence']:.1f}% checks={result['checks']}")

if __name__ == "__main__":
    run_tests()
