import pytest
from datetime import datetime
import twintradeai.runner as runner


# Fixed datetime สำหรับ snapshot เสถียร
class FixedDatetime(datetime):
    @classmethod
    def utcnow(cls):
        return datetime(2025, 1, 1, 0, 0, 0)


def test_run_engine_cycle_snapshot(monkeypatch, snapshot):
    zmq_pub = runner.DummyPub()

    # mock datetime.utcnow ใน runner
    monkeypatch.setattr(runner, "datetime", FixedDatetime)

    status = runner.run_engine_cycle(zmq_pub=zmq_pub, zmq_topic="signals")

    # ✅ ต้อง publish
    assert zmq_pub.sent, "ZMQ should have published signals"

    # ✅ ตัด last_update ออก (dynamic field)
    status_no_ts = dict(status)
    status_no_ts.pop("last_update", None)

    snapshot.assert_match(status_no_ts, "engine_status")
