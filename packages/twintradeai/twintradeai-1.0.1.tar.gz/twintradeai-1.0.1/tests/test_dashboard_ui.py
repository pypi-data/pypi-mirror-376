import os
import pandas as pd
import pytest


def test_fetch_risk_status_success(monkeypatch):
    import twintradeai.dashboard_ui as dashboard_ui

    class DummyResp:
        status_code = 200
        def json(self): return {"data": {"ok": True}}

    monkeypatch.setattr(dashboard_ui.requests, "get", lambda *a, **kw: DummyResp())

    result = dashboard_ui.fetch_risk_status()
    assert result == {"ok": True}


def test_fetch_risk_status_http_error(monkeypatch):
    import twintradeai.dashboard_ui as dashboard_ui

    class DummyResp:
        status_code = 500
        def json(self): return {}

    monkeypatch.setattr(dashboard_ui.requests, "get", lambda *a, **kw: DummyResp())

    result = dashboard_ui.fetch_risk_status()
    assert "error" in result


def test_make_chart_returns_plotly_figure():
    import twintradeai.dashboard_ui as dashboard_ui

    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=3, freq="D"),
        "entry": [1.1, 1.2, 1.3],
        "sl": [1.0, 1.1, 1.2],
        "tp3": [1.2, 1.3, 1.4],
        "bb_up": [1.3, 1.4, 1.5],
        "bb_lo": [1.0, 1.1, 1.2],
        "rsi": [30, 40, 50],
        "atr": [0.01, 0.02, 0.03],
        "macd": [0.1, 0.2, 0.3],
        "macd_signal": [0.05, 0.15, 0.25],
    })

    fig = dashboard_ui.make_chart(df, "EURUSDc")
    assert fig.layout.title.text == "EURUSDc Indicators"
    assert len(fig.data) > 0


def test_save_report_creates_pdf(tmp_path, monkeypatch):
    import twintradeai.dashboard_ui as dashboard_ui
    import plotly.graph_objects as go

    # เปลี่ยน REPORT_DIR ให้ไปที่ tmp_path (ไม่เขียนทับของจริง)
    monkeypatch.setattr(dashboard_ui, "REPORT_DIR", str(tmp_path))

    signals_df = pd.DataFrame({
        "symbol": ["EURUSDc"],
        "final_decision": ["BUY"],
        "entry": [1.1],
        "sl": [1.0],
        "tp1": [1.2],
    })

    pnl_fig = go.Figure()
    indicator_figs = {"EURUSDc": go.Figure()}

    pdf_path = dashboard_ui.save_report(signals_df, pnl_fig, indicator_figs)
    assert os.path.exists(pdf_path)
    assert pdf_path.endswith(".pdf")
