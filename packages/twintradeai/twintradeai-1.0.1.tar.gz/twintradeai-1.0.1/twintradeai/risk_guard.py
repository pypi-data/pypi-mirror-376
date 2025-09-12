import os
import json
import csv
import yaml
import logging
from datetime import datetime, date
import MetaTrader5 as mt5
from twintradeai import config_loader   # ✅ โหลด config ผ่าน config_loader

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

STATUS_FILE = "status.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RISK_GUARD][%(levelname)s] %(message)s"
)


class RiskGuard:
    def __init__(self, status_file=STATUS_FILE):
        self.status_file = str(status_file)
        self.status_full_file = os.path.abspath(
            os.path.join(os.path.dirname(self.status_file), "risk_guard_status.json")
        )

        # โหลดค่า env ผ่าน config_loader
        self.symbols, self.global_cfg, self.symbol_cfgs = config_loader.load_env_symbols()

        logging.info(f"[RISK_GUARD] Loaded symbols: {self.symbols}")
        logging.info(f"[RISK_GUARD] Global rules: {self.global_cfg}")

        # ✅ Init status ก่อน
        self.status = {
            "today_pnl": 0.0,
            "orders": 0,
            "date": str(date.today()),
            "pnl_per_symbol": {s: 0.0 for s in self.symbols}
        }

        # Map config
        self.spread_limits = {s: cfg.get("spread_limit") for s, cfg in self.symbol_cfgs.items()}
        self.per_symbol_loss = {s: cfg.get("loss_limit") for s, cfg in self.symbol_cfgs.items()}

        # Portfolio manager (default = None)
        self.portfolio_manager = None

        # ✅ export + log flash summary (compact only)
        self.save_flash_summary()
        self.log_flash_summary()

        # status ops
        self.load_status()
        self.reset_if_new_day()
        self.save_status()

    # ---------- Flash summary file ----------
    def save_flash_summary(self):
        """Export compact config summary to logs/flash_summary.yaml"""
        flash_summary = {}
        for sym, cfg in self.symbol_cfgs.items():
            flash_summary[sym] = {
                "spread_limit": cfg.get("spread_limit"),
                "confidence_min": cfg.get("confidence_min"),
                "risk_percent": cfg.get("risk_percent"),
                "loss_limit": cfg.get("loss_limit"),
            }

        try:
            flash_file = os.path.join(LOG_DIR, "flash_summary.yaml")
            with open(flash_file, "w", encoding="utf-8") as f:
                yaml.dump(flash_summary, f, allow_unicode=True, sort_keys=False, indent=2)
        except Exception as e:
            logging.error(f"[RISK_GUARD] Failed to write flash_summary.yaml: {e}")

    # ---------- Flash summary log ----------
    def log_flash_summary(self):
        """Log compact summary (ไม่โชว์ YAML ยาว)"""
        logging.info("[FLASH_SUMMARY] SYMBOLS=" + ",".join(self.symbols))
        for sym, cfg in self.symbol_cfgs.items():
            strategies = cfg.get("strategies", {})
            logging.info(
                f"[FLASH_SUMMARY] {sym} spread={cfg.get('spread_limit')} "
                f"conf={cfg.get('confidence_min')} "
                f"risk%={cfg.get('risk_percent')} "
                f"loss={cfg.get('loss_limit')} "
                f"strats={len(strategies)}"
            )

    # ---------- Reload config ----------
    def reload_config(self):
        """Reload symbol configs from config_loader and refresh flash summary"""
        try:
            self.symbols, self.global_cfg, self.symbol_cfgs = config_loader.load_env_symbols()
            logging.info(f"[RISK_GUARD] Reloaded symbols: {self.symbols}")
            logging.info(f"[RISK_GUARD] Reloaded global rules: {self.global_cfg}")

            # update maps
            self.spread_limits = {s: cfg.get("spread_limit") for s, cfg in self.symbol_cfgs.items()}
            self.per_symbol_loss = {s: cfg.get("loss_limit") for s, cfg in self.symbol_cfgs.items()}

            # ✅ update + log flash summary
            self.save_flash_summary()
            self.log_flash_summary()

        except Exception as e:
            logging.error(f"[RISK_GUARD] reload_config error: {e}")

    # ---------- File Ops ----------
    def save_status(self):
        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(self.status, f, indent=2, ensure_ascii=False)

            acc_info = mt5.account_info()
            account_metrics = {}
            if acc_info:
                account_metrics = {
                    "balance": getattr(acc_info, "balance", None),
                    "equity": getattr(acc_info, "equity", None),
                    "margin": getattr(acc_info, "margin", None),
                    "margin_free": getattr(acc_info, "margin_free", None),
                    "margin_level": getattr(acc_info, "margin_level", None),
                    "currency": getattr(acc_info, "currency", None),
                }

            data = {
                "spread_limits": self.spread_limits,
                "rules": self.global_cfg,
                "per_symbol_loss": self.per_symbol_loss,
                "status": self.status,
                "account": account_metrics,
                "last_update": datetime.utcnow().isoformat(),
            }
            with open(self.status_full_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logging.error(f"[RISK_GUARD] save_status error: {e}")

    def load_status(self):
        """โหลดสถานะจากไฟล์ ถ้าไม่มีให้ใช้ค่า default"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    self.status.update(json.load(f))
            except Exception as e:
                logging.error(f"[RISK_GUARD] load_status error: {e}")

    # ---------- Utils ----------
    def get_spread_limit(self, symbol):
        """Return spread limit per symbol, fallback to global if missing/None"""
        limit = self.spread_limits.get(symbol)
        if limit is None:
            global_limit = self.global_cfg.get("max_spread", 999999)
            logging.warning(
                f"[RISK_GUARD] No spread_limit for {symbol} in config → fallback to global max_spread={global_limit}"
            )
            return global_limit
        return limit

    def reset_if_new_day(self):
        today = str(date.today())
        if self.status.get("date") != today:
            self.status = {
                "today_pnl": 0.0,
                "orders": 0,
                "date": today,
                "pnl_per_symbol": {s: 0.0 for s in self.symbols}
            }
            logging.info("[RISK_GUARD] Reset status for new trading day")
            self.save_status()

    def increment_orders(self, symbol=None):
        """เพิ่ม counter ของ orders (ควรเรียกหลังจากส่ง order สำเร็จ)"""
        self.reset_if_new_day()
        self.status["orders"] += 1
        logging.info(f"[RISK_GUARD] Orders counter incremented → {self.status['orders']} (symbol={symbol})")
        self.save_status()

    # ---------- PnL Update ----------
    def update_pnl(self, symbol: str, profit: float):
        self.reset_if_new_day()
        prev = self.status["pnl_per_symbol"].get(symbol, 0.0)
        self.status["pnl_per_symbol"][symbol] = prev + profit
        self.status["today_pnl"] += profit
        self.save_status()

    # ---------- Logging ----------
    def log_block(self, symbol, reasons, metrics=None):
        log_file = os.path.join(LOG_DIR, f"{symbol}_log.csv")
        exists = os.path.isfile(log_file)
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "action": "BLOCK",
            "reasons": ", ".join(reasons),
            "pnl_symbol": self.status["pnl_per_symbol"].get(symbol, 0.0),
            "loss_limit": self.per_symbol_loss.get(symbol)
        }
        if metrics:
            row.update({f"m_{k}": v for k, v in metrics.items()})

        try:
            with open(log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                if not exists:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            logging.error(f"[RISK_GUARD] log_block error: {e}")

    # ---------- Core Check ----------
    def check(self, symbol, atr=None, spread_pts=None, account=None, daily_pnl=None):
        self.reset_if_new_day()
        reasons, allowed = [], True

        # Spread limit
        spread_limit = self.get_spread_limit(symbol)
        if spread_limit and spread_pts is not None and spread_pts > spread_limit:
            reasons.append(f"Spread too high ({spread_pts} > {spread_limit})")
            allowed = False

        # Global daily loss
        if daily_pnl is not None:
            if daily_pnl <= self.global_cfg["max_loss_day"]:
                reasons.append("Daily loss limit reached")
                allowed = False
        elif self.status["today_pnl"] <= self.global_cfg["max_loss_day"]:
            reasons.append("Internal daily loss limit reached")
            allowed = False

        # Per-symbol daily loss
        sym_loss = self.per_symbol_loss.get(symbol)
        pnl_symbol = self.status["pnl_per_symbol"].get(symbol, 0.0)
        if sym_loss is not None and pnl_symbol <= sym_loss:
            reasons.append("Per-symbol daily loss limit reached")
            allowed = False

        # Margin check
        acc_info = account or mt5.account_info()
        if acc_info:
            margin_level = getattr(acc_info, "margin_level", None)
            equity = getattr(acc_info, "equity", 0)
            margin = getattr(acc_info, "margin", 0)

            if margin_level is not None:
                if margin_level == 0.0:
                    if margin == 0:
                        margin_level = 9999.0
                        logging.warning("[RISK_GUARD] margin=0 → fallback margin_level=9999.0 (no positions)")
                    else:
                        margin_level = (equity / margin * 100) if margin > 0 else 0.0
                        logging.warning(f"[RISK_GUARD] recalculated margin_level={margin_level:.2f}%")

                min_margin = self.global_cfg.get("min_margin_level", 0)
                if margin_level < min_margin:
                    reasons.append(f"Margin level too low {margin_level:.2f}% < {min_margin}%")
                    allowed = False

        # Max orders
        if self.status["orders"] >= self.global_cfg["max_orders"]:
            reasons.append("Max orders exceeded")
            allowed = False

        # PortfolioManager integration
        if hasattr(self, "portfolio_manager") and self.portfolio_manager:
            try:
                if not self.portfolio_manager.can_open(symbol):
                    reasons.append("Orders exceeded or blocked by portfolio manager")
                    allowed = False
            except Exception as e:
                logging.error(f"[RISK_GUARD] portfolio_manager error: {e}")

        metrics = {
            "spread_limit": spread_limit,
            "orders_today": self.status["orders"],
            "today_pnl": self.status["today_pnl"],
            "pnl_per_symbol": self.status.get("pnl_per_symbol", {}),
            "rules": self.global_cfg,
            "atr": atr,
            "spread_pts": spread_pts,
            "loss_limit_symbol": sym_loss,
        }

        if not allowed:
            logging.warning(
                f"[RISK_GUARD] BLOCK {symbol}: {', '.join(reasons)} "
                f"(spread={spread_pts}, orders={self.status['orders']}, pnl={self.status['today_pnl']})"
            )
            self.log_block(symbol, reasons, metrics)
        else:
            logging.info(
                f"[RISK_GUARD] ✅ {symbol} allowed "
                f"(spread={spread_pts}, orders={self.status['orders']}, pnl={self.status['today_pnl']})"
            )

        self.save_status()

        return {
            "allowed": allowed,
            "reasons": reasons,
            "metrics": metrics,
        }


# ========= default instance =========
risk_guard = RiskGuard()
