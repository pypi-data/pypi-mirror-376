import pytest
from twintradeai.position_manager import PositionManager
from twintradeai.portfolio_manager import PortfolioManager
from twintradeai.risk_guard import RiskGuard
from twintradeai.lot_sizer import LotSizer
from dotenv import load_dotenv, find_dotenv
import pathlib


@pytest.fixture
def setup_pipeline():
    # โหลด .env production ทุกครั้ง (หาด้วย find_dotenv)
    env_path = find_dotenv()
    if not env_path:
        raise FileNotFoundError("❌ .env file not found. Please ensure it exists in the project root.")
    load_dotenv(env_path, override=True)

    pos_manager = PositionManager(cooldown_minutes=0)
    portfolio_manager = PortfolioManager(
        max_orders=10, max_loss_day=-500, max_exposure_per_symbol=10
    )
    risk_guard = RiskGuard()

    # Debug log — จะโชว์ค่า per_symbol_loss ที่โหลดจาก .env
    print(f"[DEBUG] Loaded per_symbol_loss: {risk_guard.per_symbol_loss}")

    lot_sizer = LotSizer(account_balance=10000, risk_percent=1.0)
    executor = MockExecutionEngine()
    return pos_manager, portfolio_manager, risk_guard, lot_sizer, executor
