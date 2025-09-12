import pytest
import types
import twintradeai.risk_guard as rg_mod


@pytest.fixture
def setup_risk_guard(monkeypatch, tmp_path):
    """Fixture สำหรับสร้าง RiskGuard ที่ deterministic"""

    # --- Mock config_loader ---
    def fake_load_env_symbols():
        symbols = ["BTCUSDc", "XAUUSDc", "EURUSDc", "AUDUSDc"]
        global_cfg = {
            "max_spread": 50.0,
            "max_loss_day": -200.0,
            "max_orders": 20,
            "risk_percent": 0.02,
            "loss_limit_default": -100.0,
            "min_margin_level": 150.0,
            "reset_daily": True,
        }
        symbol_cfgs = {
            s: {
                "spread_limit": 50.0,
                "confidence_min": 55,
                "risk_percent": 0.5,
                "loss_limit": -100.0,
                "strategies": {},
            }
            for s in symbols
        }
        return symbols, global_cfg, symbol_cfgs

    monkeypatch.setattr(rg_mod.config_loader, "load_env_symbols", fake_load_env_symbols)

    # --- Mock MetaTrader5 ---
    class FakeAcc:
        balance = 1000
        equity = 1000
        margin = 500
        margin_free = 500
        margin_level = 200
        currency = "USD"

    monkeypatch.setattr(rg_mod.mt5, "account_info", lambda: FakeAcc)

    # --- Temp status file ---
    status_file = tmp_path / "status.json"
    rg = rg_mod.RiskGuard(status_file=status_file)

    return rg


@pytest.mark.parametrize(
    ("symbol", "profit_loss_daily", "profit_loss_symbol", "spread_high"),
    [
        ("BTCUSDc", -250, -120, 4000),
        ("XAUUSDc", -300, -200, 500),
        ("EURUSDc", -220, -150, 100),
        ("AUDUSDc", -210, -110, 100),
    ],
)
def test_risk_guard_all_cases(setup_risk_guard, symbol, profit_loss_daily, profit_loss_symbol, spread_high):
    rg = setup_risk_guard

    # --- Daily loss ---
    res = rg.check(symbol, atr=1.0, spread_pts=10)
    assert res["allowed"]

    rg.update_pnl(symbol, profit_loss_daily)
    res2 = rg.check(symbol, atr=1.0, spread_pts=10)
    assert not res2["allowed"]
    assert any("daily loss" in r.lower() for r in res2["reasons"])

    # reset status สำหรับ per-symbol test
    rg.status["today_pnl"] = 0
    rg.status["pnl_per_symbol"][symbol] = 0

    # --- Per-symbol loss ---
    res = rg.check(symbol, atr=1.0, spread_pts=10)
    assert res["allowed"]

    rg.update_pnl(symbol, profit_loss_symbol)
    res2 = rg.check(symbol, atr=1.0, spread_pts=10)
    assert not res2["allowed"]
    assert any("per-symbol" in r.lower() for r in res2["reasons"])

    # --- Margin too low ---
    class LowMarginAcc:
        balance = 1000
        equity = 1000
        margin = 500
        margin_free = 500
        margin_level = 100
        currency = "USD"

    res3 = rg.check(symbol, atr=1.0, spread_pts=10, account=LowMarginAcc)
    assert not res3["allowed"]
    assert any("margin" in r.lower() for r in res3["reasons"])

    # --- Margin None (should allow) ---
    rg.status["today_pnl"] = 0
    rg.status["pnl_per_symbol"][symbol] = 0

    class NoneMarginAcc:
        balance = 1000
        equity = 1000
        margin = 0
        margin_free = 1000
        margin_level = None
        currency = "USD"

    res4 = rg.check(symbol, atr=1.0, spread_pts=10, account=NoneMarginAcc)
    assert res4["allowed"]

    # --- Spread high ---
    res5 = rg.check(symbol, atr=1.0, spread_pts=spread_high)
    assert not res5["allowed"]
    assert any("spread" in r.lower() for r in res5["reasons"])

    # --- Spread None → fallback global ---
    rg.spread_limits[symbol] = None
    res7 = rg.check(symbol, atr=1.0, spread_pts=9999)
    assert not res7["allowed"]
    assert any("spread" in r.lower() for r in res7["reasons"])

    # --- Orders exceeded by PortfolioManager ---
    class DummyPM:
        def can_open(self, sym):
            return False

    rg.portfolio_manager = DummyPM()
    res6 = rg.check(symbol, atr=1.0, spread_pts=10)
    assert not res6["allowed"]
    assert any("orders" in r.lower() for r in res6["reasons"])
