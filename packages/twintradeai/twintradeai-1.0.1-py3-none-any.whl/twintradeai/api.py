# twintradeai/api.py
import os
import json
import logging
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from twintradeai.position_manager import PositionManager
from twintradeai.portfolio_manager import PortfolioManager
from twintradeai.risk_guard import RiskGuard

logger = logging.getLogger("API")

# -----------------------------
# ⚙️ Core Components
# -----------------------------
pos_manager = PositionManager(cooldown_minutes=15)
portfolio_manager = PortfolioManager(max_orders=10, max_loss_day=-500.0, max_exposure_per_symbol=5.0)
risk_guard = RiskGuard()  # ✅ โหลด config จาก .env

# -----------------------------
# 📂 Signals file path (ใช้ใน test)
# -----------------------------
STATUS_DIR = "status"
os.makedirs(STATUS_DIR, exist_ok=True)

SIGNALS_FILE = os.path.join(STATUS_DIR, "engine_status.json")


# -----------------------------
# 🚀 FastAPI App Factory
# -----------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title="TwinTradeAi API",
        version="1.0.0",
        description="""
        TwinTradeAi API — Manage trading risk, positions, and portfolio exposure.
        
        - **Position Manager** → ป้องกันการเปิดซ้ำ, cooldown  
        - **Portfolio Manager** → คุม exposure และ daily risk  
        - **Risk Guard** → ตรวจสอบ spread, margin, daily loss limit  
        - **Signals File** → อ่านไฟล์ engine_status.json ล่าสุด
        """,
    )

    # -----------------------------
    # 🩺 Health Check
    # -----------------------------
    @app.get(
        "/health",
        tags=["System"],
        summary="Health check",
        description="ตรวจสอบสถานะการทำงานของ API และ components หลัก",
    )
    def health():
        return {"status": "ok", "components": ["PositionManager", "PortfolioManager", "RiskGuard"]}

    # -----------------------------
    # 📑 Signals
    # -----------------------------
    @app.get(
        "/signals",
        tags=["Signals"],
        summary="Get latest signals",
        description="อ่านไฟล์ engine_status.json ล่าสุดแล้วส่งกลับ (ใช้สำหรับ test/test_api.py::test_signals_file)",
    )
    def get_signals():
        if not os.path.exists(SIGNALS_FILE):
            return JSONResponse(status_code=404, content={"error": "signals file not found"})
        try:
            with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"signals": data}
        except Exception as e:
            logger.error(f"[API] ❌ Error reading signals file: {e}")
            return JSONResponse(status_code=500, content={"error": "failed to read signals"})

    # -----------------------------
    # 🔒 Position Manager
    # -----------------------------
    @app.get("/position/lock", tags=["Position Manager"])
    def lock(symbol: str, decision: str):
        pos_manager.lock(symbol, decision)
        return {"locked": True, "symbol": symbol, "decision": decision}

    @app.get("/position/unlock", tags=["Position Manager"])
    def unlock(symbol: str, decision: str = None):
        pos_manager.unlock(symbol, decision)
        return {"unlocked": True, "symbol": symbol, "decision": decision}

    @app.get("/position/status", tags=["Position Manager"])
    def position_status(symbol: str, decision: str = None):
        return {
            "symbol": symbol,
            "locked": pos_manager.is_locked(symbol, decision),
            "cooldown": pos_manager.is_in_cooldown(symbol),
            "can_trade": pos_manager.can_trade(symbol, decision or "BUY"),
        }

    # -----------------------------
    # 📊 Portfolio Manager
    # -----------------------------
    @app.post("/portfolio/order", tags=["Portfolio Manager"])
    def register_order(symbol: str, volume: float, profit: float = 0.0):
        portfolio_manager.register_order(symbol, volume, profit)
        return {"registered": True, "summary": portfolio_manager.get_summary()}

    @app.get("/portfolio/can_open", tags=["Portfolio Manager"])
    def portfolio_can_open(symbol: str):
        return {"symbol": symbol, "can_open": portfolio_manager.can_open(symbol)}

    @app.get("/portfolio/summary", tags=["Portfolio Manager"])
    def portfolio_summary():
        return portfolio_manager.get_summary()

    # -----------------------------
    # 🛡 Risk Guard
    # -----------------------------
    @app.get("/risk/check", tags=["Risk Guard"])
    def risk_check(symbol: str, spread: float = Query(..., description="Spread in points")):
        result = risk_guard.check(symbol, atr=None, spread_pts=spread)
        return {"symbol": symbol, **result}

    @app.get("/risk/rules", tags=["Risk Guard"])
    def risk_rules():
        return {
            "global_rules": risk_guard.global_cfg,
            "per_symbol": risk_guard.symbol_cfgs,
        }

    return app


# สำหรับ uvicorn และ test frameworks
api_app = create_app()
app = api_app  # ✅ alias
