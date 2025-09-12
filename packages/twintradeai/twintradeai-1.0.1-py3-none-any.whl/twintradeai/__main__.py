import logging
import time
import MetaTrader5 as mt5
from twintradeai.risk_guard import RiskGuard
from twintradeai.position_manager import PositionManager
from twintradeai.runner import run_engine_cycle, write_json, zmq_pub, ZMQ_PUB_URL, ZMQ_TOPIC, DummyPub, ENGINE_STATUS_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MAIN][%(levelname)s] %(message)s"
)

def main():
    logging.info("🔧 Booting TwinTradeAi ...")

    if not mt5.initialize():
        code, msg = mt5.last_error()
        logging.error(f"❌ MT5 initialize failed: code={code}, msg={msg}")
        exit(1)

    risk_guard = RiskGuard()
    pos_manager = PositionManager(cooldown_minutes=15)

    if isinstance(zmq_pub, DummyPub) is False:
        zmq_pub.connect(ZMQ_PUB_URL)

    while True:
        engine_status = run_engine_cycle(risk_guard, pos_manager, zmq_pub, ZMQ_TOPIC)
        write_json(ENGINE_STATUS_FILE, engine_status)
        logging.info(f"[MAIN] Updated {ENGINE_STATUS_FILE} with {engine_status['count']} signals")
        time.sleep(60)

if __name__ == "__main__":
    main()
