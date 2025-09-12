import os
import json
import pytest
from fastapi.testclient import TestClient

from twintradeai.api import app, SIGNALS_FILE


@pytest.fixture(scope="module", autouse=True)
def setup_mock_signals():
    """เตรียมไฟล์ signals mock สำหรับทดสอบ"""
    os.makedirs(os.path.dirname(SIGNALS_FILE), exist_ok=True)

    mock_data = {
        "timestamp": "2025-09-09T15:51:19Z",
        "signals": [
            {"symbol": "BTCUSDc", "decision": "BUY", "confidence": 100.0},
            {"symbol": "XAUUSDc", "decision": "SELL", "confidence": 100.0},
        ],
    }
    with open(SIGNALS_FILE, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)

    yield  # ทดสอบเสร็จแล้วไปต่อ (ถ้าต้อง clean ก็ทำตรงนี้ได้)


client = TestClient(app)


def test_health_endpoint():
    """ตรวจสอบว่า API รันและตอบ health"""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "RiskGuard" in data["components"]


def test_signals_file():
    """ตรวจสอบว่า endpoint /signals อ่านไฟล์ mock แล้วคืนค่ากลับมาได้"""
    resp = client.get("/signals")
    assert resp.status_code == 200

    data = resp.json()
    assert "signals" in data
    assert len(data["signals"]["signals"]) >= 2  # มี BTCUSDc และ XAUUSDc

    btc = data["signals"]["signals"][0]
    assert btc["symbol"] == "BTCUSDc"
    assert btc["decision"] == "BUY"
