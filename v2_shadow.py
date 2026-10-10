"""PulseCrypto V2: deterministic multi-timeframe SHADOW research only.

Reads already-closed OHLCV and a contemporaneous public order-book snapshot.
Never fetches market data, places orders, changes V1 parameters, persists a
portfolio, accesses secrets, or sends Telegram messages. CANDIDATE != BUY.
"""
from dataclasses import dataclass, asdict
from math import isfinite
from typing import Mapping

from intelligence import SYMBOLS, atr, ema

FIVE = 5 * 60_000
FIFTEEN = 15 * 60_000
HOUR = 60 * 60_000
FOUR_HOURS = 4 * HOUR

INTERVALS = {"5m": FIVE, "15m": FIFTEEN, "1h": HOUR, "4h": FOUR_HOURS}
MIN_BARS = {"5m": 24, "15m": 35, "1h": 55, "4h": 55}

# Starting research parameters, not validated profit-making thresholds.
FEE_PER_SIDE = 0.0026
ADVERSE_SLIPPAGE_PER_SIDE = 0.001
MIN_NET_REWARD_PCT = 0.003
MIN_REWARD_RISK = 2.0


@dataclass(frozen=True)
class DepthResult:
    ok: bool
    reason: str
    best_bid: float | None = None
    best_ask: float | None = None
    spread_bps: float | None = None
    buy_vwap: float | None = None
    impact_bps: float | None = None
    near_ask_depth_usd: float | None = None


@dataclass(frozen=True)
class V2Decision:
    action: str             # WAIT or CANDIDATE. NEVER a trade instruction.
    reason: str
    symbol: str
    evaluated_at_ms: int
    bias: str = "UNCONFIRMED"
    setup: str = "NONE"
    entry_reference: float | None = None
    stop: float | None = None
    target: float | None = None
    reward_risk: float | None = None
    depth: DepthResult | None = None

    def to_dict(self):
        data = asdict(self)
        data["mode"] = "V2_SHADOW_RESEARCH_ONLY"
        return data


def _positive_number(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def _closed_candles(bars, interval, as_of_ms):
    """Refuse incomplete, gap-filled, or lookahead market histories.

    Candle time is its UTC OPEN timestamp; a bar is closed once
    open_time + interval <= as_of_ms. The last bar MUST be the latest
    completely closed bar at the evaluation timestamp.
    """
    step = INTERVALS[interval]
    if not isinstance(bars, list) or len(bars) < MIN_BARS[interval]:
        raise ValueError(f"{interval}: insufficient closed historical candles")
    expected_last = (as_of_ms // step) * step - step
    previous_time = None
    for bar in bars:
        if not isinstance(bar, dict) or set(bar) != {"time", "close", "high", "low", "volume"}:
            raise ValueError(f"{interval}: malformed historical bar")
        t = bar["time"]
        if type(t) is not int or t < 0 or t % step or t + step > as_of_ms:
            raise ValueError(f"{interval}: unclosed or future candle")
        if previous_time is not None and t - previous_time != step:
            raise ValueError(f"{interval}: missing or nonchronological candle")
        previous_time = t
        values = [bar[k] for k in ("close", "high", "low", "volume")]
        if (any(type(v) not in (int, float) or not isfinite(v) for v in values)
                or bar["low"] <= 0 or not bar["low"] <= bar["close"] <= bar["high"]
                or bar["volume"] < 0):
            raise ValueError(f"{interval}: bad OHLCV values")
    if previous_time != expected_last:
        raise ValueError(f"{interval}: newest fully closed candle missing")


def _levels(rows):
    closes = [b["close"] for b in rows]
    return ema(closes, 20), ema(closes, 50)


def _bullish_bias(rows):
    # A higher-timeframe bias is NOT a trade confirmation.
    fast, slow = _levels(rows)
    fast_prev = ema([b["close"] for b in rows[:-3]], 20)
    return rows[-1]["close"] > fast > slow and fast > fast_prev


def _levels_from_book(book):
    if not isinstance(book, dict):
        raise ValueError("Invalid order book")
    bids, asks = book.get("bids"), book.get("asks")
    if not isinstance(bids, list) or not isinstance(asks, list) or not bids or not asks:
        raise ValueError("Empty order book")
    def convert(levels, reverse):
        clean = []
        old = None
        for item in levels:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError("Malformed depth level")
            price, quantity = item
            if not _positive_number(price) or not _positive_number(quantity):
                raise ValueError("Invalid price/quantity in depth")
            if old is not None and ((price >= old) if reverse else (price <= old)):
                raise ValueError("Unsorted or duplicate depth levels")
            clean.append((price, quantity))
            old = price
        return clean
    bid_levels = convert(bids, reverse=True)
    ask_levels = convert(asks, reverse=False)
    if bid_levels[0][0] >= ask_levels[0][0]:
        raise ValueError("Crossed or locked order book")
    return bid_levels, ask_levels


def assess_depth(book, as_of_ms, intended_notional_usd,
                 max_age_ms=10_000, max_spread_bps=12.0,
                 max_impact_bps=10.0, minimum_depth_multiple=5.0):
    """Conservative BUY-side book sweep; public snapshots only, no API calls.

    Distinguishes advertised resting liquidity from actual realized fills.
    Validates snapshot timestamp to prevent using future or stale books.
    """
    if type(as_of_ms) is not int or as_of_ms <= 0 or type(intended_notional_usd) not in (int, float):
        raise ValueError("Invalid evaluation time or intended paper notional")
    if not _positive_number(intended_notional_usd):
        raise ValueError("Paper notional must be positive")
    if book is None:
        return DepthResult(False, "No contemporaneous order-book snapshot")
    if not isinstance(book, Mapping):
        return DepthResult(False, "Malformed order-book snapshot")
    timestamp = book.get("timestamp_ms")
    if type(timestamp) is not int or timestamp > as_of_ms or as_of_ms - timestamp > max_age_ms:
        return DepthResult(False, "Order-book snapshot stale or future-dated")
    try:
        bids, asks = _levels_from_book(book)
    except (ValueError, TypeError):
        return DepthResult(False, "Invalid or unsorted order-book levels")
    bid, ask = bids[0][0], asks[0][0]
    spread = (ask - bid) / ((ask + bid) / 2) * 10_000
    depth = sum(p * q for p, q in asks if p <= ask * 1.0025)
    # We estimate a quantity at the visible best ask, then sweep visible asks.
    # No claim the book will remain in place by the time execution occurs.
    target_quantity = intended_notional_usd / ask
    remaining = target_quantity
    cost = 0.0
    for price, quantity in asks:
        take = min(remaining, quantity)
        cost += take * price
        remaining -= take
        if remaining <= max(target_quantity * 1e-12, 1e-12):
            break
    if remaining > max(target_quantity * 1e-12, 1e-12):
        return DepthResult(False, "Insufficient displayed ask depth", bid, ask, spread,
                           near_ask_depth_usd=depth)
    vwap = cost / target_quantity
    impact = (vwap / ask - 1) * 10_000
    if spread > max_spread_bps:
        reason = "Bid–ask spread too wide"
    elif depth < intended_notional_usd * minimum_depth_multiple:
        reason = "Insufficient liquidity near best ask"
    elif impact > max_impact_bps:
        reason = "Estimated book impact too large"
    else:
        reason = "Displayed execution depth passes research checks"
    return DepthResult(reason.startswith("Displayed"), reason, bid, ask,
                       spread, vwap, impact, depth)


def evaluate_v2(symbol, histories, as_of_ms, order_book=None, intended_notional_usd=50.0):
    """Evaluate a potential setup; no trading or state mutation.

    Bias: 4H + 1H trend; setup: 15M EMA20 pullback / recovery;
    trigger: 5M close breaks the previous three bar highs with volume.
    Execution: fresh, plausible order book + after-cost reward/risk.
    """
    if symbol not in SYMBOLS:
        raise ValueError("Unsupported paper market")
    if type(as_of_ms) is not int or as_of_ms <= 0 or as_of_ms % FIVE:
        raise ValueError("Evaluation must be on a closed 5m UTC boundary")
    if not isinstance(histories, Mapping) or set(histories) != set(INTERVALS):
        raise ValueError("Supply complete 5m/15m/1h/4h histories")
    for tf in INTERVALS:
        _closed_candles(histories[tf], tf, as_of_ms)
    def wait(reason, bias="UNCONFIRMED", setup="NONE", depth=None):
        return V2Decision("WAIT", reason, symbol, as_of_ms, bias, setup, depth=depth)

    if not (_bullish_bias(histories["4h"]) and _bullish_bias(histories["1h"])):
        return wait("4H/1H bullish alignment absent", bias="NOT_BULLISH")
    bias = "BULLISH_4H_1H"

    fifteen = histories["15m"]
    ema20 = ema([bar["close"] for bar in fifteen], 20)
    # A pullback touches EMA20 (within 1.0%) within the PREVIOUS seven bars;
    # current 15m close must recover above EMA20 and improve on prior close.
    near_ema = any(ema20 * 0.990 <= bar["low"] <= ema20 * 1.0035
                   for bar in fifteen[-8:-1])
    if not (near_ema and fifteen[-1]["close"] > ema20
            and fifteen[-1]["close"] > fifteen[-2]["close"]):
        return wait("No confirmed 15M support pullback and recovery", bias=bias)
    setup = "15M_EMA20_PULLBACK"

    five = histories["5m"]
    if five[-1]["close"] <= max(b["high"] for b in five[-4:-1]):
        return wait("5M structure break not confirmed", bias, setup)
    preceding_volume = sum(b["volume"] for b in five[-21:-1]) / 20
    if preceding_volume <= 0 or five[-1]["volume"] < preceding_volume * 1.15:
        return wait("5M relative volume confirmation absent", bias, setup)
    if five[-1]["close"] <= five[-2]["close"]:
        return wait("5M close lacks upward momentum", bias, setup)

    depth = assess_depth(order_book, as_of_ms, intended_notional_usd)
    if not depth.ok:
        return wait(depth.reason, bias, setup, depth)

    # If current book disagrees with closed 5m candle by >0.5%, fail closed.
    if abs(depth.best_ask / five[-1]["close"] - 1) > 0.005:
        return wait("Order book detached from 5M candle close", bias, setup, depth)

    # Entry reference includes modeled adverse BUY-side slippage; exit cost
    # estimates are also considered. This is not a guaranteed execution price.
    entry = depth.buy_vwap * (1 + ADVERSE_SLIPPAGE_PER_SIDE)
    stop = min(b["low"] for b in five[-6:]) - 0.10 * atr(five)
    resistance = max(b["high"] for b in fifteen[-21:-1])
    if stop <= 0 or stop >= entry or resistance <= entry:
        return wait("No valid structural stop / overhead resistance room", bias, setup, depth)
    reward = resistance - entry
    risk = entry - stop
    ratio = reward / risk
    after_cost_reward_pct = (
        (resistance * (1 - ADVERSE_SLIPPAGE_PER_SIDE) * (1 - FEE_PER_SIDE)
         - entry * (1 + FEE_PER_SIDE)) / entry
    )
    if ratio < MIN_REWARD_RISK or after_cost_reward_pct < MIN_NET_REWARD_PCT:
        return wait("Insufficient reward after modeled execution costs", bias, setup, depth)
    return V2Decision(
        "CANDIDATE", "Research-only 4H/1H bias + 15M pullback + 5M breakout + depth",
        symbol, as_of_ms, bias, setup, round(entry, 8),
        round(stop, 8), round(resistance, 8), round(ratio, 3), depth
    )


if __name__ == "__main__":
    print("PulseCrypto V2 SHADOW RESEARCH ONLY. No order execution.")
