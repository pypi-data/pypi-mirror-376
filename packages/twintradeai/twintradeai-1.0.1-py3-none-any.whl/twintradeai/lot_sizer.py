import logging
import numpy as np

logger = logging.getLogger("LOT_SIZER")


class LotSizer:
    def __init__(
        self,
        account_balance: float,
        risk_percent: float = 1.0,
        min_lot: float = 0.01,
        max_lot: float = 0.5,
        lot_step: float = 0.01,
    ):
        """
        Dynamic Lot Sizing engine

        Args:
            account_balance (float): ยอด balance ปัจจุบันของบัญชี
            risk_percent (float): % ความเสี่ยงต่อ trade (default=1.0%)
            min_lot (float): ขนาด lot ขั้นต่ำ (default=0.01)
            max_lot (float): ขนาด lot สูงสุด (default=0.5)
            lot_step (float): step ของ lot ที่ broker อนุญาต (default=0.01)
        """
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.min_lot = min_lot
        self.max_lot = max_lot
        self.lot_step = lot_step
        logger.info(
            f"[LOT_SIZER] Initialized with balance={account_balance}, "
            f"risk={risk_percent}%, min_lot={min_lot}, max_lot={max_lot}, step={lot_step}"
        )

    def update_balance(self, new_balance: float):
        """อัปเดต balance เวลามีกำไร/ขาดทุน"""
        self.account_balance = new_balance
        logger.info(f"[LOT_SIZER] Balance updated → {new_balance}")

    def calculate_atr(self, highs, lows, closes, period: int = 14) -> float:
        """
        คำนวณ Average True Range (ATR)
        """
        if len(highs) < period + 1:
            logger.warning("[LOT_SIZER] Not enough data to calculate ATR")
            return 0.0

        trs = []
        for i in range(1, len(highs)):
            high, low, prev_close = highs[i], lows[i], closes[i - 1]
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            trs.append(tr)

        if not trs:
            return 0.0

        atr = float(np.mean(trs[-period:]))
        logger.debug(f"[LOT_SIZER] ATR({period}) = {atr}")
        return atr

    def calc_lot(
        self,
        symbol: str,
        atr_value: float,
        pip_value: float,
        contract_size: float = 100000,
        min_lot: float = None,
        max_lot: float = None,
    ) -> float:
        """
        คำนวณขนาด lot ตาม ATR และ risk percent
        """
        min_lot = min_lot if min_lot is not None else self.min_lot
        max_lot = max_lot if max_lot is not None else self.max_lot

        if atr_value <= 0 or pip_value <= 0:
            logger.warning(f"[LOT_SIZER] Invalid ATR/pip_value for {symbol}")
            return min_lot

        risk_amount = self.account_balance * (self.risk_percent / 100.0)
        lot = risk_amount / (atr_value * pip_value)

        lot = self.normalize_lot(lot, symbol=symbol, min_lot=min_lot, max_lot=max_lot)

        logger.info(
            f"[LOT_SIZER] {symbol} → Balance={self.account_balance}, Risk={risk_amount:.2f}, "
            f"ATR={atr_value:.5f}, PipVal={pip_value:.5f}, Lot={lot:.2f}"
        )
        return lot

    def normalize_lot(
        self,
        lot: float,
        symbol: str = None,
        min_lot: float = None,
        max_lot: float = None,
        step: float = None,
    ) -> float:
        """
        Normalize lot ให้สอดคล้องกับ min/max และ step ของ broker
        """
        min_lot = min_lot if min_lot is not None else self.min_lot
        max_lot = max_lot if max_lot is not None else self.max_lot
        step = step if step is not None else self.lot_step

        if lot < min_lot:
            lot = min_lot
        elif lot > max_lot:
            lot = max_lot

        lot = round(lot / step) * step
        return lot

    def compute(self, symbol, entry, sl, atr, cfg):
        """
        Wrapper สำหรับ engine → ใช้ ATR และ pip_value จาก config/symbol info
        รองรับ symbol: BTCUSDc, XAUUSDc, EURUSDc, AUDUSDc, NZDUSDc, GBPUSDc
        """
        # ค่า default pip_value / contract_size ต่อ symbol
        pip_values = {
            "BTCUSDc": 1.0,
            "XAUUSDc": 1.0,
            "EURUSDc": 10.0,
            "AUDUSDc": 10.0,
            "NZDUSDc": 10.0,
            "GBPUSDc": 10.0,
        }
        contract_sizes = {
            "BTCUSDc": 1,
            "XAUUSDc": 100,
            "EURUSDc": 100000,
            "AUDUSDc": 100000,
            "NZDUSDc": 100000,
            "GBPUSDc": 100000,
        }

        pip_value = cfg.get("pip_value", pip_values.get(symbol, 1.0))
        contract_size = cfg.get("contract_size", contract_sizes.get(symbol, 100000))
        min_lot = cfg.get("min_lot", self.min_lot)
        max_lot = cfg.get("max_lot", self.max_lot)

        return self.calc_lot(
            symbol,
            atr_value=atr,
            pip_value=pip_value,
            contract_size=contract_size,
            min_lot=min_lot,
            max_lot=max_lot,
        )
