"""Read-only closed Binance.US spot candles; never includes the forming bar."""
from datetime import datetime, timezone
from math import isfinite
import requests
from intelligence import SYMBOLS, BASE_URL

INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}

def fetch_closed(symbol, interval, limit=250, now_ms=None):
    if symbol not in SYMBOLS or interval not in INTERVAL_MS:
        raise ValueError("Unsupported symbol or interval")
    if not isinstance(limit, int) or not 205 <= limit <= 1000:
        raise ValueError("Invalid candle limit")
    response = requests.get(BASE_URL,
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=20)
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list):
        raise ValueError("Invalid candle response")
    if now_ms is None:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    candles = []
    for item in rows:
        if not isinstance(item, list) or len(item) < 7:
            raise ValueError("Malformed candle")
        opened = int(item[0])
        closing = int(item[6])
        if closing >= now_ms:  # skip any not-yet-closed candle
            continue
        c = {"time": opened, "close": float(item[4]), "high": float(item[2]),
             "low": float(item[3]), "volume": float(item[5])}
        if (not all(isfinite(c[k]) for k in ("close", "high", "low", "volume"))
            or c["close"] <= 0 or c["high"] <= 0 or c["low"] <= 0
            or c["low"] > c["close"] or c["close"] > c["high"]
            or c["volume"] < 0):
            raise ValueError("Invalid candle value")
        if candles and opened <= candles[-1]["time"]:
            raise ValueError("Unordered or duplicate candle")
        if candles and opened - candles[-1]["time"] != INTERVAL_MS[interval]:
            raise ValueError("Missing candle in series")
        candles.append(c)
    if len(candles) < 205:
        raise ValueError("Insufficient closed candles")
    if now_ms - (candles[-1]["time"] + INTERVAL_MS[interval]) > INTERVAL_MS[interval]:
        raise ValueError("Market data is stale")
    return candles
