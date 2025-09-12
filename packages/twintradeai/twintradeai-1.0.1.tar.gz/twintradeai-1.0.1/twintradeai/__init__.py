"""
TwinTradeAi package initializer.
- preload config.symbols.yaml
- รวมฟังก์ชัน/คลาสหลักให้ import ใช้ง่าย
"""

import os
import yaml
import logging


# =========================
# CONFIG LOADER
# =========================
def load_symbol_cfg():
    """
    โหลด config.symbols.yaml จากโฟลเดอร์ twintradeai
    คืนค่า dict (ถ้าไม่เจอไฟล์จะคืน {})
    """
    config_path = os.path.join(os.path.dirname(__file__), "config.symbols.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"[CONFIG] load_symbol_cfg error: {e}")
            return {}
    else:
        logging.warning(f"[CONFIG] config.symbols.yaml not found at {config_path}")
        return {}


# preload global config
SYM_CFG = load_symbol_cfg()


# =========================
# EXPORT CORE MODULES
# =========================
from .indicators import add_indicators, detect_bos
from .engine import get_tf_data, build_signal, build_all_signals, evaluate_strategy
from .risk_guard import RiskGuard
from .lot_sizer import LotSizer
from .position_manager import PositionManager
from .runner import run_engine_cycle
from .scalp_evaluator import evaluate_scalp
from .execution import execute_order


__all__ = [
    # config
    "SYM_CFG",
    "load_symbol_cfg",

    # indicators
    "add_indicators",
    "detect_bos",

    # engine
    "get_tf_data",
    "build_signal",
    "build_all_signals",
    "evaluate_strategy",

    # evaluators
    "evaluate_scalp",

    # risk & position
    "RiskGuard",
    "LotSizer",
    "PositionManager",

    # runner
    "run_engine_cycle",

    # execution
    "execute_order",
]
