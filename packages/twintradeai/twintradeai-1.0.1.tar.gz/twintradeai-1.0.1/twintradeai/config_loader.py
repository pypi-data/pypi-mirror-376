# twintradeai/config_loader.py
import os
import sys
import yaml
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("CONFIG")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONFIG] %(message)s")


def safe_float(val, default=None):
    try:
        if val is None or val == "":
            return default
        if isinstance(val, str) and val.endswith("%"):
            return float(val.strip("%")) / 100.0
        return float(val)
    except Exception:
        return default


def safe_int(val, default=None):
    try:
        if val is None or val == "":
            return default
        return int(val)
    except Exception:
        return default


def load_env_symbols():
    """โหลด global/per-symbol risk จาก .env + รวม strategy.yaml"""

    # --- Global defaults ---
    global_cfg = {
        "max_spread": safe_float(os.getenv("RISK_MAX_SPREAD"), 9999),
        "max_loss_day": safe_float(os.getenv("RISK_MAX_LOSS_DAY"), -100.0),
        "max_orders": safe_int(os.getenv("RISK_MAX_ORDERS"), 10),
        "risk_percent": safe_float(os.getenv("RISK_PERCENT"), 0.01),
        "loss_limit_default": safe_float(os.getenv("LOSS_LIMIT_DEFAULT"), -100),
        "min_margin_level": safe_float(os.getenv("RISK_MIN_MARGIN_LEVEL"), 150.0),
        "reset_daily": os.getenv("RESET_DAILY", "false").lower()
        in ("1", "true", "yes"),
    }

    # --- Symbols list ---
    symbols = [
        s.strip() for s in os.getenv("SYMBOLS", "").split(",") if s.strip()
    ]
    if not symbols:
        logger.warning("No SYMBOLS defined in .env, fallback to []")

    # --- Per-symbol risk configs from .env ---
    symbol_cfgs = {}
    for sym in symbols:
        spread = safe_float(os.getenv(f"SPREAD_LIMIT_{sym}"))
        loss_limit = safe_float(
            os.getenv(f"LOSS_LIMIT_{sym}"), global_cfg["loss_limit_default"]
        )
        risk_percent = safe_float(
            os.getenv(f"RISK_PERCENT_{sym}"), global_cfg["risk_percent"]
        )

        if spread is None:
            spread = global_cfg["max_spread"]

        symbol_cfgs[sym] = {
            "spread_limit": spread,
            "loss_limit": loss_limit,
            "risk_percent": risk_percent,
        }

    # --- Load strategies.yaml or strategies_min.yaml ---
    strategy_cfgs = {}
    strat_file = (
        "strategies_min.yaml" if "--minimal" in sys.argv else "strategies.yaml"
    )
    strat_path = os.path.join(os.path.dirname(__file__), "..", "config", strat_file)
    if os.path.exists(strat_path):
        with open(strat_path, "r", encoding="utf-8") as f:
            strategy_cfgs = yaml.safe_load(f) or {}
    else:
        logger.warning(f"{strat_file} not found at {strat_path}")

    # --- Merge strategy + env (env overrides strategy) ---
    merged_cfgs = {}
    for sym in symbols:
        merged_cfgs[sym] = {
            **(strategy_cfgs.get(sym, {}) or {}),  # base
            **(symbol_cfgs.get(sym, {}) or {}),   # env override
        }

        # 🔎 per-symbol config log → DEBUG only
        spread = merged_cfgs[sym].get("spread_limit")
        conf_min = merged_cfgs[sym].get("confidence_min")
        trailing = merged_cfgs[sym].get("trailing_atr_mult")
        logger.debug(
            f"{sym} spread={spread}, confidence_min={conf_min}, trailing={trailing}"
        )

        # check strategies completeness
        strategies = merged_cfgs[sym].get("strategies", {})
        missing_modes = [m for m in ["scalp", "day", "swing"] if m not in strategies]
        if missing_modes:
            logger.warning(f"{sym} missing strategies: {missing_modes}")
        else:
            for mode, cfg in strategies.items():
                if "threshold" not in cfg or "weights" not in cfg:
                    logger.warning(f"{sym}.{mode} missing threshold/weights")

    logger.info(f"Loaded symbols: {symbols}")
    logger.info(f"Global risk cfg: {global_cfg}")

    return symbols, global_cfg, merged_cfgs
