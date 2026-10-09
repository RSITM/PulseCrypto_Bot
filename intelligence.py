"""Research-only 15-minute market indicators. No orders or trade signals."""
import math
import requests

BASE_URL = "https://api.binance.us/api/v3/klines"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def fetch_candles(symbol, limit=250):
    if symbol not in SYMBOLS:
        raise ValueError("Unsupported symbol")
    response = requests.get(BASE_URL, params={"symbol": symbol, "interval": "15m", "limit": limit}, timeout=20)
    response.raise_for_status()
    raw = response.json()
    if not isinstance(raw, list) or len(raw) < 205:
        raise ValueError("Insufficient candle history")
    # Binance's most recent candle can still be forming; exclude it.
    candles = [{"close": float(x[4]), "high": float(x[2]), "low": float(x[3]), "volume": float(x[5])} for x in raw[:-1]]
    if any(not all(math.isfinite(v) for v in c.values()) or c["close"] <= 0 or c["volume"] < 0 or c["low"] > c["high"] for c in candles):
        raise ValueError("Invalid candle data")
    return candles


def ema(values, period):
    if len(values) < period:
        raise ValueError("Insufficient history")
    average = sum(values[:period]) / period
    multiplier = 2 / (period + 1)
    for value in values[period:]:
        average = value * multiplier + average * (1 - multiplier)
    return average


def rsi(values, period=14):
    if len(values) <= period:
        raise ValueError("Insufficient history")
    differences = [b - a for a, b in zip(values, values[1:])]
    gain = sum(max(d, 0) for d in differences[:period]) / period
    loss = sum(max(-d, 0) for d in differences[:period]) / period
    for d in differences[period:]:
        gain = (gain * (period - 1) + max(d, 0)) / period
        loss = (loss * (period - 1) + max(-d, 0)) / period
    if loss == 0:
        return 100.0 if gain > 0 else 50.0
    return 100 - 100 / (1 + gain / loss)


def atr(candles, period=14):
    if len(candles) <= period:
        raise ValueError("Insufficient history")
    ranges = []
    for previous, current in zip(candles, candles[1:]):
        ranges.append(max(current["high"] - current["low"], abs(current["high"] - previous["close"]), abs(current["low"] - previous["close"])))
    value = sum(ranges[:period]) / period
    for tr in ranges[period:]:
        value = (value * (period - 1) + tr) / period
    return value


def analyze(candles):
    if len(candles) < 205:
        raise ValueError("At least 205 closed candles required")
    closes = [c["close"] for c in candles]
    volumes = [c["volume"] for c in candles]
    e20, e50, e200 = (ema(closes, n) for n in (20, 50, 200))
    price = closes[-1]
    momentum = rsi(closes)
    volatility = atr(candles)
    baseline = sum(volumes[-21:-1]) / 20
    relative_volume = volumes[-1] / baseline if baseline > 0 else None
    if price > e20 > e50 > e200:
        regime = "BULLISH"
    elif price < e20 < e50 < e200:
        regime = "BEARISH"
    else:
        regime = "NEUTRAL"
    return {"price": price, "ema20": e20, "ema50": e50, "ema200": e200,
            "rsi14": momentum, "atr14": volatility, "atr_pct": volatility / price * 100,
            "relative_volume": relative_volume, "regime": regime}


if __name__ == "__main__":
    for symbol in SYMBOLS:
        print(symbol, analyze(fetch_candles(symbol)))
