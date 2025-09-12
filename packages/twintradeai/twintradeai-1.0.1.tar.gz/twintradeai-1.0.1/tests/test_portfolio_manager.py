import pytest
from twintradeai.portfolio_manager import PortfolioManager


def test_max_orders_limit():
    pm = PortfolioManager(max_orders=2, max_loss_day=-500, max_exposure_per_symbol=10)
    pm.register_order("EURUSDc", volume=0.1, profit=-5.0)
    pm.register_order("EURUSDc", volume=0.2, profit=3.0)
    # เปิดครบ 2 orders แล้ว → ต้อง block
    assert not pm.can_open("EURUSDc"), "ควรถูกบล็อกเพราะเกินจำนวน orders"


def test_daily_loss_limit():
    pm = PortfolioManager(max_orders=10, max_loss_day=-100, max_exposure_per_symbol=10)
    o1 = pm.register_order("XAUUSDc", volume=0.1, profit=-20.0)
    pm.close_order(o1, profit=-20.0)
    o2 = pm.register_order("XAUUSDc", volume=0.1, profit=-100.0)
    pm.close_order(o2, profit=-100.0)

    # รวมแล้ว PnL = -120 <= -100 → ต้อง block
    assert not pm.can_open("XAUUSDc"), "ควรถูกบล็อกเพราะเกิน daily loss limit"


def test_exposure_limit_per_symbol():
    pm = PortfolioManager(max_orders=10, max_loss_day=-500, max_exposure_per_symbol=1.0)
    pm.register_order("BTCUSDc", volume=0.5, profit=0.0)
    pm.register_order("BTCUSDc", volume=0.6, profit=0.0)
    # รวม exposure = 1.1 > 1.0 → ต้อง block
    assert not pm.can_open("BTCUSDc"), "ควรถูกบล็อกเพราะ exposure ของ symbol เกิน limit"
