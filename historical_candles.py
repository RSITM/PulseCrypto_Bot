"""Download ONLY public Binance.US historical OHLCV candles for an offline audit.

No API keys, trading endpoints, private balances, account state writes or Telegram.
Historical dataset is a standalone GitHub Actions artifact, never written to paper-state.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import math
import time

import requests

from intelligence import BASE_URL, SYMBOLS

M15 = 900_000
H1 = 3_600_000
DAY = 86_400_000
INTERVAL_MS = {"15m": M15, "1h": H1}


def bars_for_range(session, symbol, interval, start, end, now_ms):
    if symbol not in SYMBOLS or interval not in INTERVAL_MS:
        raise ValueError("Unknown market or interval")
    step = INTERVAL_MS[interval]
    if start < 0 or end <= start or start % step or end % step:
        raise ValueError("Invalid interval boundaries")
    if end > now_ms - step:
        raise ValueError("Historical series must end at a previously closed candle")
    if (end - start) // step > 13_000:
        raise ValueError("Historical request too large")
    result = []
    cursor = start
    while cursor < end:
        params = {"symbol": symbol, "interval": interval, "startTime": cursor,
                  "endTime": end - 1, "limit": 1000}
        response = session.get(BASE_URL, params=params, timeout=25)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            raise ValueError(f"{symbol} {interval}: no candles from exchange")
        for row in payload:
            if not isinstance(row, list) or len(row) < 7:
                raise ValueError(f"{symbol} {interval}: invalid Binance.US kline")
            opened = int(row[0])
            closed = int(row[6])
            if opened != cursor or closed < opened + step - 2 or closed >= opened + step:
                raise ValueError(f"{symbol} {interval}: missing, unclosed or misaligned candle")
            candle = {
                "time": opened, "close": float(row[4]), "high": float(row[2]),
                "low": float(row[3]), "volume": float(row[5])
            }
            numbers = [candle[k] for k in ("close", "high", "low", "volume")]
            if (any(not math.isfinite(v) for v in numbers) or candle["low"] <= 0
                    or not candle["low"] <= candle["close"] <= candle["high"]
                    or candle["volume"] < 0):
                raise ValueError(f"{symbol} {interval}: invalid OHLCV values")
            result.append(candle)
            cursor += step
            if cursor >= end:
                break
        # Binance.US returns at most 1000 bars. This must progress, even on errors.
        if len(payload) > 1000:
            raise ValueError("Exchange exceeded max page size")
    if len(result) != (end - start) // step:
        raise ValueError(f"{symbol} {interval}: incomplete history")
    return result


def download(days=30, session=None, now_ms=None):
    if type(days) is not int or days not in (7, 14, 30, 60, 90):
        raise ValueError("Historical days must be 7, 14, 30, 60 or 90")
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    # Lag one entire hour so even Binance.US lagged market data is fully closed.
    end = (now_ms // H1 - 1) * H1
    start = end - days * DAY
    market = {}
    client = session if session is not None else requests.Session()
    for symbol in SYMBOLS:
        # 250 15m and 255 closed 1h bars, required for EMA-200 calculations.
        # Endpoints are exclusive; overlap of the final hourly candle is unnecessary.
        market[symbol] = {
            "15m": bars_for_range(client, symbol, "15m", start - 255 * M15, end, now_ms),
            "1h": bars_for_range(client, symbol, "1h", start - 255 * H1, end, now_ms)
        }
    return {
        "format_version": 1,
        "source": "Binance.US public spot klines",
        "analysis_start_ms": start,
        "analysis_end_ms": end,
        "as_of_utc": datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc).isoformat(),
        "symbols": market
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only historical Binance.US OHLCV snapshot")
    parser.add_argument("--days", type=int, default=30, choices=(7, 14, 30, 60, 90))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = download(days=args.days)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(f"Saved {args.days} closed-day historical dataset for BTC, ETH, SOL: {output}")


if __name__ == "__main__":
    main()
