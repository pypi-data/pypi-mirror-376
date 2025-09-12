import json
import pytest
from pathlib import Path
import twintradeai.runner as runner

SNAPSHOT_DIR = "tests/snapshots/engine_signals"

@pytest.mark.snapshot
@pytest.mark.parametrize(
    "snapshot_file",
    [
        "scalp_signals.json",
        "scalp_signals_sell.json",
        "scalp_signals_buy.json",
    ],
)
def test_scalp_signals_snapshot_from_engine_status(snapshot, tmp_path, snapshot_file, monkeypatch):
    snapshot_path = Path(SNAPSHOT_DIR) / snapshot_file
    baseline = json.loads(snapshot_path.read_text(encoding="utf-8"))

    # mock ให้ ENGINE_STATUS_FILE point ไปที่ไฟล์ปลอมใน tmp_path
    fake_engine_status = tmp_path / "engine_status.json"
    fake_engine_status.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    monkeypatch.setattr(runner, "ENGINE_STATUS_FILE", str(fake_engine_status))

    # ใช้ load_engine_status() ของ runner
    actual = runner.load_engine_status()

    # snapshot test (ทั้ง list ตรง ๆ)
    snapshot.assert_match(actual, snapshot_file)

    # ต้องตรงกับ baseline
    assert actual == baseline
