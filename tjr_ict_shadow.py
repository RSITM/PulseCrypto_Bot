"""PulseCrypto TJR-INSPIRED ICT public-method research, NOT TJR proprietary code.

Public educational concepts: sweeps of known liquidity, candle-close MSS/BOS,
displacement, three-bar FVGs, opposing-candle order blocks, 50% equilibrium,
higher-timeframe context, session liquidity and stop/opposing-pool targets.

This is a deterministic, parameterized INTERPRETATION, not TJR's exact private
2026 algorithm. Only fully closed 5m, 1h, 4h candle histories are accepted.
No networking, order placement, Telegram, state persistence or account writes.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from math import isfinite
from zoneinfo import ZoneInfo

from intelligence import SYMBOLS, ema
from v2_shadow import FIVE, HOUR, FOUR_HOURS, FEE_PER_SIDE, ADVERSE_SLIPPAGE_PER_SIDE

ET = ZoneInfo("America/New_York")
# Prespecified exploratory parameters; NOT claimed as TJR's settings.
REQUIRED_BARS = 60
MAX_SWEEP_AGE_BARS = 7
MAX_MSS_TO_ZONE_BARS = 4
ORDER_EXPIRY_BARS = 12
MIN_DISPLACEMENT_ATR = .65
MIN_BODY_ATR = .35
MIN_GAP_ATR = .035
MIN_RR = 1.33
FALLBACK_RR = 2.0
MIN_AFTER_COST_TARGET_PCT = .002

@dataclass(frozen=True)
class TJRVariant:
    name: str
    zone_kind: str                # FVG, ORDER_BLOCK, EQUILIBRIUM, or FVG_OR_OB
    session: str                  # NY or ALL
    bias: str                     # CONTEXT, ONE_HOUR, or FOUR_HOUR_AND_ONE_HOUR
    min_rr: float = MIN_RR

VARIANTS = (
    TJRVariant("PUBLIC_NY_FVG", "FVG", "NY", "CONTEXT"),
    TJRVariant("PUBLIC_NY_ORDER_BLOCK", "ORDER_BLOCK", "NY", "CONTEXT"),
    TJRVariant("PUBLIC_NY_EQUILIBRIUM", "EQUILIBRIUM", "NY", "CONTEXT"),
    TJRVariant("CRYPTO_24H_FVG", "FVG", "ALL", "ONE_HOUR"),
    TJRVariant("CRYPTO_24H_ORDER_BLOCK", "ORDER_BLOCK", "ALL", "ONE_HOUR"),
    TJRVariant("CRYPTO_24H_FVG_OR_OB", "FVG_OR_OB", "ALL", "ONE_HOUR"),
)
VARIANT_BY_NAME = {x.name: x for x in VARIANTS}

@dataclass(frozen=True)
class Liquidity:
    label: str
    high: float
    low: float

@dataclass(frozen=True)
class ResearchSignal:
    action: str                   # WAIT, SWEEP, SHIFT, or RESEARCH_LIMIT_ORDER
    reason: str
    symbol: str
    as_of_ms: int
    side: str = "NONE"            # LONG or THEORETICAL_SHORT; never executable
    swept_pool: str = "NONE"
    zone_kind: str = "NONE"
    zone_low: float | None = None
    zone_high: float | None = None
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    rr: float | None = None
    target_source: str = "NONE"
    context: str = "UNCONFIRMED"

    def to_dict(self):
        return {**asdict(self), "mode": "TJR_PUBLIC_INSPIRED_PRICE_ONLY_RESEARCH"}

def _checked_closed(bars, step, at, minimum=REQUIRED_BARS):
    if not isinstance(bars, list) or len(bars) < minimum:
        raise ValueError("Insufficient validated closed market history")
    if type(at) is not int or at < step or at % FIVE:
        raise ValueError("Invalid evaluation timestamp")
    if bars[-1]["time"] != (at // step) * step - step:
        raise ValueError("Missing most recent CLOSED history candle")
    prev = None
    for b in bars:
        if not isinstance(b, dict):
            raise ValueError("Malformed candle")
        if set(b) != {"time", "open", "high", "low", "close", "volume"} and set(b) != {
                "time", "high", "low", "close", "volume"}:
            raise ValueError("Unexpected candle fields")
        t = b["time"]
        vals = [b[k] for k in ("high", "low", "close", "volume")]
        if "open" in b: vals.append(b["open"])
        if (type(t) is not int or t < 0 or t % step
                or any(type(x) not in (int, float) or not isfinite(x) for x in vals)
                or b["low"] <= 0 or b["low"] > b["close"]
                or b["close"] > b["high"] or b["volume"] < 0
                or ("open" in b and not b["low"] <= b["open"] <= b["high"])):
            raise ValueError("Invalid candle OHLCV/timestamp")
        if prev is not None and t != prev + step:
            raise ValueError("Unverified historical candle gap")
        if t + step > at:
            raise ValueError("Future or unclosed candle")
        prev = t

def true_range_atr(rows, periods=14):
    if len(rows) < periods + 1:
        raise ValueError("Insufficient bars for ATR")
    return sum(max(x["high"] - x["low"], abs(x["high"] - old["close"]),
                   abs(x["low"] - old["close"]))
               for old, x in zip(rows[-periods-1:-1], rows[-periods:])) / periods

def ny_session(as_of_ms):
    return datetime.fromtimestamp(as_of_ms / 1000, timezone.utc).astimezone(ET)

def is_ny_window(as_of_ms):
    local = ny_session(as_of_ms)
    minute = local.hour * 60 + local.minute
    return 9 * 60 + 30 <= minute <= 16 * 60

def _levels_from_completed_session(rows, current_ny_day, low_minute, high_minute,
                                   day_offset, label):
    from_date = current_ny_day + timedelta(days=day_offset)
    selected = []
    for b in rows:
        t = ny_session(b["time"])
        minutes = t.hour * 60 + t.minute
        if t.date() == from_date and low_minute <= minutes < high_minute:
            selected.append(b)
    # Reject gaps / partial history instead of making up session boundaries.
    expected = (high_minute - low_minute) // 5
    if len(selected) != expected:
        return None
    return Liquidity(label, max(b["high"] for b in selected),
                     min(b["low"] for b in selected))

def known_liquidity(rows, h1, h4, as_of_ms):
    """Only PREVIOUSLY CLOSED liquidity ranges; current candle excluded."""
    if len(rows) < 61:
        return []
    earlier = rows[:-1]
    ny = ny_session(as_of_ms)
    day = ny.date()
    pools = []
    previous_day = [b for b in earlier if ny_session(b["time"]).date()
                    == day - timedelta(days=1)]
    # Previous NY calendar day must have completed with plausible full data;
    # DST transitions can change 24h count by 12 bars.
    if 276 <= len(previous_day) <= 300:
        pools.append(Liquidity("PREVIOUS_NY_DAY", max(b["high"] for b in previous_day),
                               min(b["low"] for b in previous_day)))
    asia = _levels_from_completed_session(
        earlier, day, 20 * 60, 24 * 60, -1, "ASIA_ET_20_TO_00")
    if asia is not None: pools.append(asia)
    if ny.hour >= 5:
        london = _levels_from_completed_session(
            earlier, day, 2 * 60, 5 * 60, 0, "LONDON_PROXY_ET_02_TO_05")
        if london is not None: pools.append(london)
    # Completed HTF candles and local swing structure are available to both
    # all-hours crypto and NY-specific modes.
    if len(h1) >= 2:
        pools.append(Liquidity("PREVIOUS_1H", h1[-2]["high"], h1[-2]["low"]))
    if len(h4) >= 2:
        pools.append(Liquidity("PREVIOUS_4H", h4[-2]["high"], h4[-2]["low"]))
    pools.append(Liquidity("PRIOR_3H_SWING",
                           max(b["high"] for b in earlier[-36:]),
                           min(b["low"] for b in earlier[-36:])))
    return pools

def context_bias(rows, side):
    closes = [r["close"] for r in rows]
    fast, slow = ema(closes, 20), ema(closes, 50)
    return (rows[-1]["close"] > fast > slow) if side == "LONG" else (
        rows[-1]["close"] < fast < slow)

def candidate_sweep(rows, h1, h4, at):
    """Sweep of a level KNOWN before the current fully closed 5m bar."""
    bar = rows[-1]
    pools = known_liquidity(rows, h1, h4, at)
    long_pools = [p for p in pools if bar["low"] < p.low and bar["close"] > p.low]
    short_pools = [p for p in pools if bar["high"] > p.high and bar["close"] < p.high]
    if long_pools and short_pools:
        return None  # Ambiguous two-sided raid in one bar.
    if long_pools:
        best = min(long_pools, key=lambda p: p.low)
        side, level = "LONG", best.low
    elif short_pools:
        best = max(short_pools, key=lambda p: p.high)
        side, level = "THEORETICAL_SHORT", best.high
    else:
        return None
    prior = rows[-5:-1]
    if len(prior) != 4:
        return None
    structure = max(b["high"] for b in prior) if side == "LONG" else min(
        b["low"] for b in prior)
    return {"side": side, "level": level, "pool": best.label,
            "at": at, "extreme": bar["low"] if side == "LONG" else bar["high"],
            "structure": structure, "stage": "SWEEP", "mss_at": None,
            "mss_extreme": None}

def fair_value_gap(rows, side, atr5):
    """Three fully CLOSED consecutive 5m candles."""
    a, _, c = rows[-3:]
    if side == "LONG":
        bottom, top = a["high"], c["low"]
    else:
        bottom, top = c["high"], a["low"]
    return (bottom, top) if top - bottom >= MIN_GAP_ATR * atr5 else None

def order_block(rows, side, at_sweep, at_shift):
    """Last opposing candle from sweep through confirmed break (max 10 bars)."""
    for b in reversed(rows[-11:-1]):
        if b["time"] + FIVE < at_sweep - 3 * FIVE or b["time"] >= at_shift:
            continue
        if ((side == "LONG" and b["close"] < b["open"])
                or (side != "LONG" and b["close"] > b["open"])):
            return b["low"], b["high"]
    return None

def execution_room(entry, stop, target, side, rr_floor):
    risk = entry - stop if side == "LONG" else stop - entry
    reward = target - entry if side == "LONG" else entry - target
    if risk <= 0 or reward <= 0 or reward / risk < rr_floor:
        return False
    # Hypothetical round-trip spread/fees and adverse slippage on BOTH sides.
    fee, slip = FEE_PER_SIDE, ADVERSE_SLIPPAGE_PER_SIDE
    if side == "LONG":
        buy = entry * (1 + slip)
        sell = target * (1 - slip)
        net_pct = (sell * (1 - fee) - buy * (1 + fee)) / buy
    else:
        sell = entry * (1 - slip)
        buy = target * (1 + slip)
        net_pct = (sell * (1 - fee) - buy * (1 + fee)) / sell
    return net_pct >= MIN_AFTER_COST_TARGET_PCT

class TJRScanner:
    """Per-symbol finite-state detector. Every transition is candle-close only."""

    def __init__(self, variant):
        if variant not in VARIANTS:
            raise ValueError("Unsupported frozen TJR research variant")
        self.variant = variant
        self.state = {symbol: None for symbol in SYMBOLS}
        self.last_time = {symbol: None for symbol in SYMBOLS}

    def on_closed_candle(self, symbol, five, h1, h4, as_of_ms):
        if symbol not in SYMBOLS:
            raise ValueError("Unsupported market")
        # Public market data and aggregation validated before replay. Verify
        # the latest bar, correct 5m chronology, and only closed HTF bars.
        if not isinstance(five, list) or len(five) < REQUIRED_BARS:
            raise ValueError("Insufficient five-minute history")
        if any(set(r) != {"time", "open", "high", "low", "close", "volume"} for r in five[-60:]):
            raise ValueError("Five-minute OHLCV with OPEN is required")
        _checked_closed(five[-60:], FIVE, as_of_ms)
        _checked_closed(h1[-60:], HOUR, as_of_ms, 55)
        _checked_closed(h4[-60:], FOUR_HOURS, as_of_ms, 55)
        previous = self.last_time[symbol]
        if previous is not None and as_of_ms != previous + FIVE:
            raise ValueError("Missing or nonchronological TJR evaluation time")
        self.last_time[symbol] = as_of_ms
        def decision(action, reason, state=None, **kwargs):
            return ResearchSignal(action, reason, symbol, as_of_ms,
                                  side=(state or {}).get("side", "NONE"),
                                  swept_pool=(state or {}).get("pool", "NONE"),
                                  **kwargs)

        if self.variant.session == "NY" and not is_ny_window(as_of_ms):
            self.state[symbol] = None
            return decision("WAIT", "Outside prespecified New York session")
        current = self.state[symbol]
        bar = five[-1]
        atr5 = true_range_atr(five)
        if current is not None:
            age = (as_of_ms - current["at"]) // FIVE
            invalidated = (bar["close"] < current["extreme"] if current["side"] == "LONG"
                           else bar["close"] > current["extreme"])
            if age > MAX_SWEEP_AGE_BARS + MAX_MSS_TO_ZONE_BARS or invalidated:
                self.state[symbol] = None
                current = None
            elif current["stage"] == "SWEEP":
                broken = (bar["close"] > current["structure"] if current["side"] == "LONG"
                          else bar["close"] < current["structure"])
                displacement = (bar["high"] - bar["low"] >= MIN_DISPLACEMENT_ATR * atr5
                                and abs(bar["close"] - bar["open"]) >= MIN_BODY_ATR * atr5)
                if broken and displacement:
                    current["stage"] = "MSS"
                    current["mss_at"] = as_of_ms
                    current["mss_extreme"] = (bar["high"] if current["side"] == "LONG"
                                              else bar["low"])
                elif age > MAX_SWEEP_AGE_BARS:
                    self.state[symbol] = None
                    current = None
                else:
                    return decision("SWEEP", "Sweep waiting for candle-close MSS/BOS", current)
            elif current["stage"] == "MSS" and as_of_ms - current["mss_at"] > MAX_MSS_TO_ZONE_BARS * FIVE:
                self.state[symbol] = None
                current = None

        if current is None:
            maybe = candidate_sweep(five, h1, h4, as_of_ms)
            if maybe is None:
                return decision("WAIT", "No confirmed raid of known liquidity")
            if self.variant.bias != "CONTEXT":
                bullish_1h = context_bias(h1, maybe["side"])
                bullish_4h = context_bias(h4, maybe["side"])
                if not bullish_1h or (self.variant.bias == "FOUR_HOUR_AND_ONE_HOUR"
                                       and not bullish_4h):
                    return decision("WAIT", "Higher-timeframe bias not aligned")
            self.state[symbol] = maybe
            return decision("SWEEP", "Sweep known; wait for opposite structure break", maybe)

        # There can be a newly confirmed MSS on this candle or a pending zone
        # after MSS. Zone formation must not use any later, unclosed candle.
        if current["stage"] != "MSS":
            return decision("SWEEP", "Awaiting displacement and structure break", current)
        side = current["side"]
        if self.variant.zone_kind in ("FVG", "FVG_OR_OB"):
            zone = fair_value_gap(five, side, atr5)
            zone_kind = "FVG"
        else:
            zone = None
            zone_kind = "NONE"
        if zone is None and self.variant.zone_kind in ("ORDER_BLOCK", "FVG_OR_OB"):
            zone = order_block(five, side, current["at"], current["mss_at"])
            zone_kind = "ORDER_BLOCK"
        if self.variant.zone_kind == "EQUILIBRIUM":
            other = bar["high"] if side == "LONG" else bar["low"]
            center = (other + current["extreme"]) / 2
            zone = (center, center)
            zone_kind = "EQUILIBRIUM"
        if zone is None:
            return decision("SHIFT", "MSS formed; waiting for matching FVG/order block", current)

        lower, upper = zone
        entry = (lower + upper) / 2
        sweep_extreme = current["extreme"]
        stop = sweep_extreme - .1 * atr5 if side == "LONG" else sweep_extreme + .1 * atr5
        if not ((side == "LONG" and 0 < stop < entry < bar["close"])
                or (side != "LONG" and 0 < bar["close"] < entry < stop)):
            return decision("WAIT", "Zone/stop invalid or price not displaced beyond entry", current)
        # Opposing existing (already-observed) liquidity first; only use a
        # static 2R fallback when no suitable unswept opposing range exists.
        min_goal = entry + self.variant.min_rr * (entry - stop) if side == "LONG" else (
            entry - self.variant.min_rr * (stop - entry))
        pools = known_liquidity(five, h1, h4, as_of_ms)
        opposite = (
            sorted({p.high for p in pools if p.high >= min_goal})
            if side == "LONG" else
            sorted({p.low for p in pools if 0 < p.low <= min_goal}, reverse=True)
        )
        if opposite:
            target, target_source = opposite[0], "KNOWN_OPPOSING_LIQUIDITY"
        else:
            target = entry + FALLBACK_RR * (entry - stop) if side == "LONG" else (
                entry - FALLBACK_RR * (stop - entry))
            target_source = "EXPLICIT_2R_FALLBACK"
        if not execution_room(entry, stop, target, side, self.variant.min_rr):
            return decision("WAIT", "Post-cost target and reward/risk do not qualify", current)
        ctx = ("ALIGNED_1H_4H" if context_bias(h1, side) and context_bias(h4, side)
               else "UNALIGNED_OR_CONTEXT_ONLY")
        self.state[symbol] = None  # One and only one zone per sweep.
        return decision(
            "RESEARCH_LIMIT_ORDER", "Public-method sweep → close MSS → retracement zone",
            current, zone_kind=zone_kind, zone_low=round(lower, 8),
            zone_high=round(upper, 8), entry=round(entry, 8),
            stop=round(stop, 8), target=round(target, 8),
            rr=round(abs(target-entry)/abs(entry-stop), 3),
            target_source=target_source, context=ctx,
        )

def depth_gate_for_research(signal, book, observed_at_ms, intended_notional=50):
    """Optional *forward-only* depth check; never invent historical snapshots."""
    from v2_shadow import assess_depth
    if signal.action != "RESEARCH_LIMIT_ORDER":
        return {"accepted": False, "reason": "No research entry to gate"}
    if type(observed_at_ms) is not int or observed_at_ms < signal.as_of_ms:
        return {"accepted": False, "reason": "No timely observation receipt"}
    if observed_at_ms - signal.as_of_ms > 150_000:
        return {"accepted": False, "reason": "Observation collected too late"}
    if signal.side != "LONG":
        return {"accepted": False, "reason": "Spot short not executable; theoretical only"}
    assessment = assess_depth(book, observed_at_ms, intended_notional)
    return {"accepted": assessment.ok, "reason": assessment.reason,
            "spread_bps": assessment.spread_bps,
            "impact_bps": assessment.impact_bps,
            "observed_at_ms": observed_at_ms}
