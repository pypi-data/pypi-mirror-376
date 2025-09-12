import os
import requests
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:9000")
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def fetch_risk_status():
    """ดึง risk status จาก API"""
    try:
        r = requests.get(f"{API_URL}/risk_status", timeout=5)
        if r.status_code == 200:
            return r.json().get("data", {})
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def make_chart(df: pd.DataFrame, symbol: str):
    """สร้าง plotly chart สำหรับ symbol"""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df["timestamp"],
        open=df["entry"],
        high=df["tp3"],
        low=df["sl"],
        close=df["entry"],
        name="Price"
    ))
    if "bb_up" in df and "bb_lo" in df:
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_up"], line=dict(color="blue"), name="BB Upper"))
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_lo"], line=dict(color="blue"), name="BB Lower"))

    if "rsi" in df:
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["rsi"], line=dict(color="purple"), name="RSI"))

    if "atr" in df:
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["atr"], line=dict(color="orange"), name="ATR"))

    if "macd" in df and "macd_signal" in df:
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["macd"], line=dict(color="green"), name="MACD"))
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["macd_signal"], line=dict(color="red"), name="MACD Sig"))

    fig.update_layout(title=f"{symbol} Indicators", height=400, showlegend=True)
    return fig


def save_report(signals_df: pd.DataFrame, pnl_fig, indicator_figs: dict):
    """บันทึก PDF Report รวม signals + PnL + Indicators"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    pdf_path = os.path.join(REPORT_DIR, f"report_{today}.pdf")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, f"TwinTradeAi Report - {today}", ln=True, align="C")

    # --- Signals Summary ---
    pdf.set_font("Arial", size=10)
    if not signals_df.empty:
        for _, row in signals_df.iterrows():
            line = f"{row['symbol']} | {row['final_decision']} | entry={row['entry']} sl={row['sl']} tp1={row['tp1']}"
            pdf.cell(200, 8, line, ln=True)

    # หมายเหตุ: ไม่เซฟรูปจริง เพื่อลด dependency
    pdf.cell(200, 10, "PnL Chart & Indicators (mocked in tests)", ln=True)

    pdf.output(pdf_path)
    return pdf_path
