import logging
from datetime import date

logger = logging.getLogger("PORTFOLIO_MANAGER")


class PortfolioManager:
    def __init__(self, max_orders=10, max_loss_day=-500.0, max_exposure_per_symbol=10.0):
        self.max_orders = max_orders
        self.max_loss_day = max_loss_day
        self.max_exposure_per_symbol = max_exposure_per_symbol
        self.orders = []  # active orders
        self.daily_pnl = 0.0
        self.daily_pnl_by_symbol = {}
        self.today = str(date.today())
        self._next_order_id = 1

        logger.info(
            f"[PORTFOLIO_MANAGER] Initialized with "
            f"max_orders={max_orders}, max_loss_day={max_loss_day}, max_exposure_per_symbol={max_exposure_per_symbol}"
        )

    # 📥 Register new order
    def register_order(self, symbol, volume, profit=0.0):
        self._reset_if_new_day()
        order = {
            "order_id": self._next_order_id,
            "symbol": symbol,
            "volume": volume,
            "profit": profit,
        }
        self.orders.append(order)
        self._next_order_id += 1
        logger.info(
            f"[PORTFOLIO_MANAGER] 📥 Register order {symbol} vol={volume}, profit={profit}, total_orders={len(self.orders)}"
        )
        return order["order_id"]

    # 📤 Close order by order_id
    def close_order(self, order_id, profit=0.0):
        self._reset_if_new_day()
        order = next((o for o in self.orders if o["order_id"] == order_id), None)
        if not order:
            logger.warning(f"[PORTFOLIO_MANAGER] ❌ Order {order_id} not found")
            return False

        symbol = order["symbol"]
        volume = order["volume"]
        order_profit = profit

        # update PnL
        self.daily_pnl += order_profit
        self.daily_pnl_by_symbol[symbol] = self.daily_pnl_by_symbol.get(symbol, 0.0) + order_profit

        # remove order
        self.orders = [o for o in self.orders if o["order_id"] != order_id]

        logger.info(
            f"[PORTFOLIO_MANAGER] 📤 Close order {symbol} vol={volume}, profit={order_profit}, total_orders={len(self.orders)}"
        )
        return True

    def can_open(self, symbol):
        self._reset_if_new_day()
        reasons = []

        if len(self.orders) >= self.max_orders:
            reasons.append(f"too many orders ({len(self.orders)} >= {self.max_orders})")

        if self.daily_pnl <= self.max_loss_day:
            reasons.append(f"daily loss exceeded {self.daily_pnl:.2f} <= {self.max_loss_day}")

        exposure = sum(o["volume"] for o in self.orders if o["symbol"] == symbol)
        if exposure >= self.max_exposure_per_symbol:
            reasons.append(f"exposure exceeded for {symbol} ({exposure} >= {self.max_exposure_per_symbol})")

        if reasons:
            logger.warning(f"[PORTFOLIO_MANAGER] ❌ Block {symbol}, reasons={reasons}")
            return False
        return True

    def get_summary(self):
        self._reset_if_new_day()
        return {
            "orders": self.orders,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_by_symbol": self.daily_pnl_by_symbol,
        }

    # internal reset if new day
    def _reset_if_new_day(self):
        today = str(date.today())
        if self.today != today:
            self.today = today
            self.orders = []
            self.daily_pnl = 0.0
            self.daily_pnl_by_symbol = {}
