import logging
import time
import os
import threading
import MetaTrader5 as mt5
from twintradeai.lot_sizer import LotSizer

# ========= Registry =========
TRAILING_THREADS = {}
PARTIAL_THREADS = {}

# ========= Load from env =========
DEVIATION_POINTS = int(os.getenv("DEVIATION_POINTS", "50"))
ORDER_MAGIC = int(os.getenv("ORDER_MAGIC", "123456"))
ORDER_FILLING = getattr(mt5, os.getenv("ORDER_FILLING", "ORDER_FILLING_IOC"))
ORDER_MAX_RETRIES = int(os.getenv("ORDER_MAX_RETRIES", "3"))
ORDER_RETRY_SLEEP = float(os.getenv("ORDER_RETRY_SLEEP", "0.25"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EXEC][%(levelname)s] %(message)s"
)

# ========= Helpers =========
def round_to_point(symbol, price):
    """ปรับราคาให้ตรงกับจำนวนทศนิยมของ symbol"""
    try:
        info = mt5.symbol_info(symbol)
        if not info:
            return float(price)
        p = getattr(info, "point", 0.00001)
        digits = getattr(info, "digits", 5)
        return round(round(float(price) / p) * p, digits)
    except Exception as e:
        logging.error(f"[EXEC] round_to_point error: {e}")
        return float(price)


def has_open_position(symbol, decision):
    """ตรวจสอบว่า symbol มี position เดิมอยู่หรือไม่"""
    try:
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return False
        for pos in positions:
            if pos.type == mt5.POSITION_TYPE_BUY and decision == "BUY":
                return True
            if pos.type == mt5.POSITION_TYPE_SELL and decision == "SELL":
                return True
        return False
    except Exception as e:
        logging.error(f"[EXEC] has_open_position error: {e}")
        return False


# ========= Modify SL/TP =========
def modify_order(ticket, symbol, sl=None, tp=None):
    """
    แก้ไข Stop Loss / Take Profit ของ order ที่มีอยู่
    """
    try:
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logging.error(f"[EXEC MODIFY] No position found ticket={ticket} {symbol}")
            return None

        pos = positions[0]
        sl_new = round_to_point(symbol, sl) if sl else pos.sl
        tp_new = round_to_point(symbol, tp) if tp else pos.tp

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": symbol,
            "sl": sl_new,
            "tp": tp_new,
            "magic": ORDER_MAGIC,
            "comment": "TwinTradeAi Modify SLTP",
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"[EXEC MODIFY OK] {symbol} ticket={ticket} sl={sl_new} tp={tp_new}")
        else:
            logging.error(f"[EXEC MODIFY FAIL] {symbol} ticket={ticket} retcode={getattr(result, 'retcode', None)}")
        return result

    except Exception as e:
        logging.error(f"[EXEC MODIFY ERROR] {symbol} ticket={ticket}: {e}")
        return None


# ========= Trailing Stop Thread =========
def manage_trailing_stop(symbol, decision, initial_sl, trailing_atr):
    """
    รัน background thread สำหรับปรับ SL ตาม ATR (Trailing Stop)
    """
    logging.info(f"[EXEC TRAIL] Start trailing stop for {symbol} ({decision}), step={trailing_atr}")
    while True:
        try:
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                logging.info(f"[EXEC TRAIL] {symbol} no open position, stop trailing")
                break

            pos = positions[0]  # MT5 netting mode: 1 position per symbol
            price = mt5.symbol_info_tick(symbol)
            if not price:
                time.sleep(2)
                continue

            current_price = price.bid if decision == "SELL" else price.ask
            base_sl = initial_sl or getattr(pos, "sl", None)
            new_sl = None

            if decision == "BUY":
                candidate = current_price - trailing_atr
                if base_sl is None or candidate > base_sl:
                    new_sl = candidate
            elif decision == "SELL":
                candidate = current_price + trailing_atr
                if base_sl is None or candidate < base_sl:
                    new_sl = candidate

            if new_sl:
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "sl": round_to_point(symbol, new_sl),
                    "tp": getattr(pos, "tp", 0.0),
                    "position": pos.ticket,
                }
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    initial_sl = new_sl
                    logging.info(f"[EXEC TRAIL] Updated SL for {symbol} → {new_sl}")
            time.sleep(5)

        except Exception as e:
            logging.error(f"[EXEC TRAIL] {symbol} error: {e}")
            break


# ========= Execution =========
def execute_order(symbol, decision, lot, entry, sl, tp1, tp2, tp3,
                  ratios=(0.5, 0.3, 0.2), trailing_stop=None):
    """
    เปิดออเดอร์ 3 ไม้ (TP1, TP2, TP3)
    - รองรับ partial lot
    - duplicate check
    - retry mechanism
    - normalize lot ด้วย LotSizer
    - ถ้า sl=None → trailing stop fallback ใช้ SL ปัจจุบันของ position
    """
    info = mt5.symbol_info(symbol)
    if not info:
        logging.error(f"[EXEC] {symbol} not found in MT5")
        return {"success": False, "orders": [], "reason": "Symbol not found"}

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logging.error(f"[EXEC] No tick for {symbol}")
        return {"success": False, "orders": [], "reason": "No tick"}

    if decision == "BUY":
        price = tick.ask
        order_type = mt5.ORDER_TYPE_BUY
    elif decision == "SELL":
        price = tick.bid
        order_type = mt5.ORDER_TYPE_SELL
    else:
        return {"success": False, "orders": [], "reason": f"Invalid decision {decision}"}

    # Duplicate check
    if has_open_position(symbol, decision):
        logging.warning(f"[EXEC] Duplicate {decision} blocked for {symbol}")
        return {"success": False, "orders": [], "reason": "Duplicate position blocked"}

    # Round numbers
    price = round_to_point(symbol, price)
    sl = round_to_point(symbol, sl) if sl else None
    tp1 = round_to_point(symbol, tp1) if tp1 else None
    tp2 = round_to_point(symbol, tp2) if tp2 else None
    tp3 = round_to_point(symbol, tp3) if tp3 else None

    # LotSizer
    min_lot = getattr(info, "volume_min", 0.01)
    max_lot = getattr(info, "volume_max", 100.0)
    step    = getattr(info, "volume_step", 0.01)

    acc = mt5.account_info()
    balance = getattr(acc, "balance", 1000)

    lot_sizer = LotSizer(account_balance=balance,
                         min_lot=min_lot,
                         max_lot=max_lot,
                         lot_step=step)

    results, success = [], True

    for tp, tag, ratio in [(tp1, "TP1", ratios[0]),
                           (tp2, "TP2", ratios[1]),
                           (tp3, "TP3", ratios[2])]:
        if not tp or ratio <= 0:
            continue

        volume_raw = lot * ratio
        volume = lot_sizer.normalize_lot(volume_raw,
                                         symbol=symbol,
                                         min_lot=min_lot,
                                         max_lot=max_lot,
                                         step=step)

        if volume <= 0:
            logging.warning(f"[EXEC SKIP] {symbol} {decision} {tag} volume={volume_raw} < min_lot={min_lot}, skipped")
            continue

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": DEVIATION_POINTS,
            "magic": ORDER_MAGIC,
            "comment": f"TwinTradeAi {tag}",
            "type_filling": ORDER_FILLING,
        }

        result = None
        for attempt in range(ORDER_MAX_RETRIES):
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                break
            logging.warning(
                f"[EXEC RETRY] {symbol} {decision} {tag} attempt {attempt+1}/{ORDER_MAX_RETRIES} "
                f"retcode={result.retcode if result else 'N/A'}"
            )
            time.sleep(ORDER_RETRY_SLEEP)

        if not result:
            logging.error(f"[EXEC FAIL] {symbol} {decision} {tag} - no response")
            success = False
        elif result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error(
                f"[EXEC FAIL] {symbol} {decision} {tag} lot={volume} entry={price} sl={sl} tp={tp} "
                f"retcode={result.retcode} comment={getattr(result, 'comment', None)}"
            )
            success = False
        else:
            logging.info(
                f"[EXEC OK] {symbol} {decision} {tag} lot={volume} entry={price} sl={sl} tp={tp} "
                f"order_id={result.order} deal_id={result.deal}"
            )
        results.append(result)

    # Start trailing stop thread
    if success and trailing_stop:
        if symbol not in TRAILING_THREADS or not TRAILING_THREADS[symbol].is_alive():
            th = threading.Thread(
                target=manage_trailing_stop,
                args=(symbol, decision, sl, trailing_stop),
                daemon=True,
            )
            th.start()
            TRAILING_THREADS[symbol] = th
            logging.info(f"[EXEC TRAIL] Thread started for {symbol}")

    return {"success": success, "orders": results}


# ========= Partial Close =========
def execute_order_partial(symbol, decision, lot, price, ratio=0.5):
    """
    ปิดบางส่วน (partial close)
    """
    info = mt5.symbol_info(symbol)
    if not info:
        logging.error(f"[EXEC PARTIAL] {symbol} not found in MT5")
        return None

    min_lot = getattr(info, "volume_min", 0.01)
    max_lot = getattr(info, "volume_max", 100.0)
    step    = getattr(info, "volume_step", 0.01)

    lot_sizer = LotSizer(account_balance=1000,
                         min_lot=min_lot,
                         max_lot=max_lot,
                         lot_step=step)

    volume_raw = lot * ratio
    volume = lot_sizer.normalize_lot(volume_raw, symbol=symbol,
                                     min_lot=min_lot,
                                     max_lot=max_lot,
                                     step=step)

    if volume <= 0:
        logging.warning(f"[EXEC PARTIAL SKIP] {symbol} {decision} lot={volume_raw} < min_lot={min_lot}, skipped")
        return None

    order_type = mt5.ORDER_TYPE_SELL if decision == "BUY" else mt5.ORDER_TYPE_BUY

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": round_to_point(symbol, price),
        "deviation": DEVIATION_POINTS,
        "magic": ORDER_MAGIC,
        "comment": "TwinTradeAi Partial Close",
        "type_filling": ORDER_FILLING,
    }

    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(
            f"[EXEC PARTIAL OK] {symbol} {decision} partial lot={volume} price={price} "
            f"order_id={result.order} deal_id={result.deal}"
        )
    else:
        logging.error(
            f"[EXEC PARTIAL FAIL] {symbol} {decision} lot={volume} price={price} "
            f"retcode={getattr(result, 'retcode', None)}"
        )
    return result


def execute_order_partial_async(symbol, decision, lot, price, ratio=0.5):
    """
    Async partial close (background thread)
    """
    def worker():
        execute_order_partial(symbol, decision, lot, price, ratio)

    t = threading.Thread(target=worker, daemon=True)
    PARTIAL_THREADS[symbol] = t
    t.start()
    return t
