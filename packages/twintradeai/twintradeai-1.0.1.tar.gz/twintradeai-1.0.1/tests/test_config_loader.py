import pytest
import json
from twintradeai import config_loader


def test_load_env_symbols_snapshot(snapshot):
    """
    Snapshot test สำหรับ config_loader.load_env_symbols()

    ตรวจสอบว่า symbols, global_cfg, และ merged_cfgs
    ถูกโหลด/merge จาก .env + symbols.yaml + strategies.yaml ตรงตามที่คาด
    """
    symbols, global_cfg, merged_cfgs = config_loader.load_env_symbols()

    # export เฉพาะที่ snapshot-friendly (dict/json serializable)
    snapshot_data = {
        "symbols": symbols,
        "global_cfg": global_cfg,
        "merged_cfgs": merged_cfgs,
    }

    # แปลงเป็น JSON เพื่อ snapshot (ทำให้ diff อ่านง่าย)
    snapshot.assert_match(
        json.dumps(snapshot_data, indent=2, sort_keys=True, ensure_ascii=False),
        "config_loader.json"
    )
