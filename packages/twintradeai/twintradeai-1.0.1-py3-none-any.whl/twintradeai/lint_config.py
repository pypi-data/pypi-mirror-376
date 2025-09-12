import os
import yaml
import sys
import argparse

CONFIG_FILE = "config.symbols.yaml"

REQUIRED_FIELDS = ["confidence_min", "strategies"]
REQUIRED_STRATEGIES = ["scalp", "day", "swing"]
REQUIRED_WEIGHTS = ["ema", "atr", "stoch", "vwap"]

DEFAULT_CONF_MIN = 60.0
DEFAULT_THRESHOLD = 2.0
DEFAULT_WEIGHTS = {w: 1.0 for w in REQUIRED_WEIGHTS}


def lint_config(path=CONFIG_FILE, auto_fix=False):
    if not os.path.exists(path):
        print(f"❌ Config file not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    errors, warnings, fixes = [], [], []

    for sym, scfg in cfg.items():
        # --- confidence_min ---
        if "confidence_min" not in scfg:
            msg = f"[{sym}] missing required field: confidence_min"
            if auto_fix:
                scfg["confidence_min"] = DEFAULT_CONF_MIN
                fixes.append(f"Auto-fixed {msg} → set {DEFAULT_CONF_MIN}")
            else:
                errors.append(msg)

        # --- strategies ---
        strategies = scfg.get("strategies", {})
        if not strategies and auto_fix:
            scfg["strategies"] = {}
            strategies = scfg["strategies"]

        for strat in REQUIRED_STRATEGIES:
            if strat not in strategies:
                msg = f"[{sym}] missing strategy: {strat}"
                if auto_fix:
                    strategies[strat] = {
                        "threshold": DEFAULT_THRESHOLD,
                        "weights": DEFAULT_WEIGHTS.copy(),
                    }
                    fixes.append(f"Auto-fixed {msg}")
                else:
                    errors.append(msg)
                continue

            weights = strategies[strat].get("weights", {})
            if not weights:
                msg = f"[{sym}] {strat} strategy has no weights"
                if auto_fix:
                    strategies[strat]["weights"] = DEFAULT_WEIGHTS.copy()
                    fixes.append(f"Auto-fixed {msg}")
                else:
                    errors.append(msg)
                continue

            for w in REQUIRED_WEIGHTS:
                if w not in weights:
                    msg = f"[{sym}] {strat} strategy missing weight: {w}"
                    if auto_fix:
                        strategies[strat]["weights"][w] = 1.0
                        fixes.append(f"Auto-fixed {msg}")
                    else:
                        warnings.append(msg)

    # --- save if fixed ---
    if auto_fix and fixes:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
        print(f"💾 Auto-fix applied and saved back to {path}")

    # --- report ---
    print("=== Config Lint Report ===")
    if errors:
        print("❌ Errors:")
        for e in errors:
            print("   -", e)
    else:
        print("✅ No critical errors")

    if warnings:
        print("⚠️  Warnings:")
        for w in warnings:
            print("   -", w)
    else:
        print("✅ No warnings")

    if fixes:
        print("🔧 Auto-Fixes:")
        for f in fixes:
            print("   -", f)

    print(f"\nSummary: {len(errors)} errors, {len(warnings)} warnings, {len(fixes)} fixes across {len(cfg)} symbols")

    return errors, warnings, fixes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lint tool for config.symbols.yaml")
    parser.add_argument("--fix", action="store_true", help="Auto-fix missing fields")
    args = parser.parse_args()

    lint_config(CONFIG_FILE, auto_fix=args.fix)
