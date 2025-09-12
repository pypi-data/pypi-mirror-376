import logging
import os
from datetime import datetime, timedelta, timezone
from twintradeai import execution

logger = logging.getLogger("POSITION_MANAGER")


class PositionManager:
    def __init__(self, cooldown_minutes: int = 0):
        """
        จัดการ per-symbol lock, cooldown และ trailing stop
        """
        self.cooldown_minutes = max(0, cooldown_minutes)
        self.locks = {}      # {symbol: {"decision": str, "locked_at": datetime}}
        self.cooldowns = {}  # {symbol: datetime}

        # ✅ ENV Switch สำหรับ debug trailing
        self.debug_trailing = os.getenv("DEBUG_TRAILING", "0") == "1"

        if self.cooldown_minutes == 0:
            logger.info("[POSITION_MANAGER] Initialized with cooldown=DISABLED")
        else:
            logger.info(f"[POSITION_MANAGER] Initialized with cooldown={self.cooldown_minutes} minutes")

    # -----------------------------
    # 🔒 Lock / Unlock
    # -----------------------------
    def lock(self, symbol: str, decision: str, now: datetime = None):
        if now is None:
            now = datetime.now(timezone.utc)
        self.locks[symbol] = {"decision": decision, "locked_at": now}
        logger.info(f"[POSITION_MANAGER] 🔒 Locked {symbol} for decision={decision}")

    def unlock(self, symbol: str, decision: str = None):
        if symbol in self.locks:
            if decision is None or self.locks[symbol]["decision"] == decision:
                del self.locks[symbol]
                logger.info(f"[POSITION_MANAGER] 🔓 Unlocked {symbol} decision={decision}")

    def is_locked(self, symbol: str, decision: str = None, now: datetime = None) -> bool:
        if symbol not in self.locks:
            return False

        if now is None:
            now = datetime.now(timezone.utc)
        lock = self.locks[symbol]
        elapsed = now - lock["locked_at"]

        # 🔓 Auto-expire lock
        if self.cooldown_minutes > 0 and elapsed >= timedelta(minutes=self.cooldown_minutes):
            del self.locks[symbol]
            logger.info(f"[POSITION_MANAGER] 🔓 Auto-unlocked {symbol} after {self.cooldown_minutes} minutes")
            return False

        if decision is None:
            return True
        return lock["decision"] == decision

    # -----------------------------
    # ⏳ Cooldown
    # -----------------------------
    def start_cooldown(self, symbol: str, now: datetime = None):
        if now is None:
            now = datetime.now(timezone.utc)
        self.cooldowns[symbol] = now
        logger.info(f"[POSITION_MANAGER] ⏳ Cooldown started for {symbol}")

    def set_cooldown(self, symbol: str, now: datetime = None):
        return self.start_cooldown(symbol, now=now)

    def is_in_cooldown(self, symbol: str, now: datetime = None) -> bool:
        if symbol not in self.cooldowns:
            return False

        if now is None:
            now = datetime.now(timezone.utc)
        elapsed = now - self.cooldowns[symbol]

        if elapsed >= timedelta(minutes=self.cooldown_minutes):
            del self.cooldowns[symbol]
            return False
        return True

    # -----------------------------
    # ✅ Trade Decision
    # -----------------------------
    def can_trade(self, symbol: str, decision: str, now: datetime = None):
        if self.is_locked(symbol, decision, now=now):
            reason = f"locked for decision={decision}"
            logger.warning(f"[POSITION_MANAGER] ❌ Cannot trade {symbol}, {reason}")
            return False, reason

        if self.is_in_cooldown(symbol, now=now):
            reason = "cooldown active"
            logger.warning(f"[POSITION_MANAGER] ❌ Cannot trade {symbol}, {reason}")
            return False, reason

        return True, "allowed"

    # -----------------------------
    # 📈 Trailing Stop + Follow TP
    # -----------------------------
    def update_trailing(self, positions, tp_step_pips=20, trailing_start_pips=10, debug=None):
        """
        อัปเดต SL ของทุก order:
        - เริ่มขยับเมื่อได้กำไรเกิน trailing_start_pips
        - เมื่อถึง TP ปัจจุบัน → ขยับ SL มาที่ TP และเลื่อน TP ต่อไปอีก tp_step_pips
        """
        if debug is None:
            debug = self.debug_trailing

        now = datetime.now(timezone.utc)
        for pos in positions:
            symbol = pos["symbol"]
            entry = pos["price_open"]
            sl = pos.get("sl", 0)
            tp = pos.get("tp", 0)
            price = pos["bid"] if pos["type"] == "BUY" else pos["ask"]
            point = pos["point"]

            # คำนวณกำไร (pips)
            if pos["type"] == "BUY":
                profit_pips = (price - entry) / point
            else:
                profit_pips = (entry - price) / point

            if debug:
                logger.info(
                    f"[POSITION_MANAGER][DEBUG] {symbol} {pos['type']} "
                    f"entry={entry:.5f} price={price:.5f} "
                    f"profit={profit_pips:.1f} pips SL={sl} TP={tp}"
                )

            # ----------------- Trailing -----------------
            if profit_pips >= trailing_start_pips:
                if pos["type"] == "BUY":
                    new_sl = price - trailing_start_pips * point
                    if new_sl > (sl or 0):
                        self._modify_order(pos, sl=new_sl, tp=tp)
                        logger.info(f"[POSITION_MANAGER] 📈 Trailing {symbol} BUY SL→{new_sl}")
                else:  # SELL
                    new_sl = price + trailing_start_pips * point
                    if sl == 0 or new_sl < sl:
                        self._modify_order(pos, sl=new_sl, tp=tp)
                        logger.info(f"[POSITION_MANAGER] 📈 Trailing {symbol} SELL SL→{new_sl}")

            # ----------------- Follow TP -----------------
            if tp and ((pos["type"] == "BUY" and price >= tp) or (pos["type"] == "SELL" and price <= tp)):
                new_sl = tp
                new_tp = tp + tp_step_pips * point if pos["type"] == "BUY" else tp - tp_step_pips * point
                self._modify_order(pos, sl=new_sl, tp=new_tp)
                logger.info(f"[POSITION_MANAGER] 🎯 {symbol} SL moved→{new_sl}, TP extended→{new_tp}")

    def _modify_order(self, pos, sl=None, tp=None):
        """
        แก้ไข order จริง ผ่าน execution.modify_order()
        """
        try:
            result = execution.modify_order(
                ticket=pos["ticket"],
                symbol=pos["symbol"],
                sl=sl,
                tp=tp
            )
            if result and result.retcode == 10009:  # TRADE_RETCODE_DONE
                logger.info(f"[POSITION_MANAGER] 🔄 Modified {pos['symbol']} ticket={pos['ticket']} SL={sl} TP={tp}")
            else:
                logger.warning(f"[POSITION_MANAGER] ⚠️ Modify fail {pos['symbol']} ticket={pos['ticket']}")
        except Exception as e:
            logger.error(f"[POSITION_MANAGER] ❌ Error modify {pos['symbol']} ticket={pos['ticket']}: {e}")
