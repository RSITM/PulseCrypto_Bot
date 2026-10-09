"""Research-only, closed-candle spot signal evaluator. No order execution."""
from dataclasses import dataclass, asdict
from intelligence import analyze, ema

@dataclass(frozen=True)
class Signal:
    action: str
    reason: str
    entry: float | None = None
    stop: float | None = None
    target: float | None = None

def evaluate(candles, higher_timeframe=None):
    """Evaluate completed 15m candles; optional completed 1h candles confirm trend.

    Returns BUY or WAIT. SELL is reserved for a future position-aware exit engine.
    """
    if len(candles) < 205:
        raise ValueError("At least 205 closed 15m candles required")
    metrics = analyze(candles)
    price = metrics["price"]
    atr = metrics["atr14"]
    if atr <= 0 or metrics["atr_pct"] < 0.15:
        return Signal("WAIT", "Insufficient volatility")
    if metrics["regime"] != "BULLISH":
        return Signal("WAIT", "15m trend not bullish")
    if higher_timeframe is None:
        return Signal("WAIT", "1h trend confirmation unavailable")
    if len(higher_timeframe) < 205:
        raise ValueError("At least 205 closed 1h candles required")
    higher = analyze(higher_timeframe)
    if higher["regime"] != "BULLISH":
        return Signal("WAIT", "1h trend not bullish")
    if not (45 <= metrics["rsi14"] <= 65):
        return Signal("WAIT", "Momentum outside entry range")
    if (metrics["relative_volume"] or 0) < 1.2:
        return Signal("WAIT", "Volume confirmation absent")
    if price <= metrics["ema20"]:
        return Signal("WAIT", "Price below fast trend average")
    # Candidate rules only; not validated as profitable.
    stop = price - 1.5 * atr
    if stop <= 0:
        return Signal("WAIT", "Invalid stop distance")
    target = price + 2 * (price - stop)
    return Signal("BUY", "Bullish 15m/1h trends with momentum and volume", price, stop, target)

if __name__ == "__main__":
    print("PulseCrypto signal engine is research-only. No live orders.")
