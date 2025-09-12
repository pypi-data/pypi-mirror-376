import pytest
from datetime import datetime, timedelta, timezone
from twintradeai.position_manager import PositionManager
from twintradeai.risk_guard import RiskGuard


def test_cooldown(monkeypatch):
    pm = PositionManager(cooldown_minutes=1)

    # ตั้งค่า cooldown แบบ aware datetime
    past = datetime(2025, 9, 11, 10, 22, 18, 317323, tzinfo=timezone.utc)
    pm.cooldowns["BTCUSDc"] = past

    # mock ปัจจุบันให้เลยเวลาคูลดาวน์ไปแล้ว
    fake_now = past + timedelta(minutes=5)

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_now

    monkeypatch.setattr("twintradeai.position_manager.datetime", FakeDateTime)

    # ควรหมดคูลดาวน์แล้ว
    assert not pm.is_in_cooldown("BTCUSDc")


def test_lock_expired(monkeypatch):
    pm = PositionManager(cooldown_minutes=1)

    # ตั้ง lock เป็น aware datetime ย้อนหลัง 5 นาที
    past = datetime(2025, 9, 11, 10, 0, tzinfo=timezone.utc)
    pm.locks["BTCUSDc"] = {"decision": "BUY", "locked_at": past}

    # mock เวลาปัจจุบันให้ใหม่
    fake_now = past + timedelta(minutes=5)

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_now

    monkeypatch.setattr("twintradeai.position_manager.datetime", FakeDateTime)

    # lock ควรหมดอายุแล้ว
    assert not pm.is_locked("BTCUSDc")


def test_lock_active(monkeypatch):
    pm = PositionManager(cooldown_minutes=5)

    # ตั้ง lock เป็น aware datetime ปัจจุบัน
    t0 = datetime(2025, 9, 11, 12, 0, tzinfo=timezone.utc)
    pm.locks["BTCUSDc"] = {"decision": "SELL", "locked_at": t0}

    # mock เวลาปัจจุบัน = ผ่านไป 2 นาที (ยัง active)
    fake_now = t0 + timedelta(minutes=2)

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_now

    monkeypatch.setattr("twintradeai.position_manager.datetime", FakeDateTime)

    # lock ต้องยัง active
    assert pm.is_locked("BTCUSDc", "SELL")
