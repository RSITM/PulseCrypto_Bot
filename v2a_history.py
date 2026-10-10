"""Offline V2-A research 5m OHLCV history. Public Binance.US market data only.

Collects real bars and records gaps; uses one shared gap-free trailing window for
BTC, ETH, SOL with 72 fully closed 4h bars for reproducible multi-timeframe
warmup. No market orders, portfolio state, tokens, or personal information.
"""
import argparse
from datetime import datetime, timezone
import json
from math import isfinite
from pathlib import Path
import time

import requests
from intelligence import BASE_URL, SYMBOLS
from v2_shadow import FIVE, FIFTEEN, HOUR, FOUR_HOURS

DAY = 24 * HOUR
WARMUP = 72 * FOUR_HOURS  # Also provides the 252h warmup required by V1.
DAYS_ALLOWED = (7, 14, 30)


MINUTE = 60_000
MAX_1M_REBUILDS_PER_SYMBOL = 40


def checked_candle(row, opened, step_ms):
    """Validate real OHLCV; no simulated prices and no future candle content."""
    if not isinstance(row, list) or len(row) < 7:
        raise ValueError("Malformed Binance.US kline")
    if int(row[0]) != opened or int(row[6]) != opened + step_ms - 1:
        raise ValueError("Historical kline lacks a complete aligned interval")
    candle = {"time": opened, "open": float(row[1]),
              "high": float(row[2]), "low": float(row[3]),
              "close": float(row[4]), "volume": float(row[5])}
    prices = [candle[key] for key in ("open", "high", "low", "close")]
    if (not all(isfinite(v) and v > 0 for v in prices)
            or candle["low"] > min(candle["open"], candle["close"])
            or max(candle["open"], candle["close"]) > candle["high"]
            or not isfinite(candle["volume"]) or candle["volume"] < 0):
        raise ValueError("Invalid Binance.US historical OHLCV")
    return candle


def reconstruct_from_real_one_minute_bars(session, symbol, opened):
    """Try recovering a malformed 5m candle from FIVE actual 1m exchange rows.

    No extrapolation, interpolation, forward-filling or synthetic data.
    An incomplete or malformed 1m response is NOT usable and returns None.
    Transport/HTTP errors still fail visibly rather than hiding an outage.
    """
    params = {"symbol": symbol, "interval": "1m", "startTime": opened,
              "endTime": opened + FIVE - 1, "limit": 5}
    response = session.get(BASE_URL, params=params, timeout=25)
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list) or len(rows) != 5:
        return None
    minutes = []
    for index, row in enumerate(rows):
        try:
            minutes.append(checked_candle(row, opened + index * MINUTE, MINUTE))
        except (ValueError, TypeError, OverflowError):
            return None
    return {"time": opened, "open": minutes[0]["open"],
            "high": max(r["high"] for r in minutes),
            "low": min(r["low"] for r in minutes),
            "close": minutes[-1]["close"],
            "volume": sum(r["volume"] for r in minutes)}


def download_5m(session, symbol, start_ms, end_ms, now_ms, *, with_repairs=False):
    if symbol not in SYMBOLS or start_ms < 0 or not 0 < start_ms < end_ms:
        raise ValueError("Invalid symbol/time range")
    if start_ms % FIVE or end_ms % FIVE or end_ms > now_ms - FIVE:
        raise ValueError("History must be aligned and previously closed")
    if (end_ms - start_ms) // FIVE > 13_000:
        raise ValueError("Historical range too large")
    bars, gaps, repairs = [], [], []
    cursor = start_ms
    while cursor < end_ms:
        params = {"symbol": symbol, "interval": "5m", "startTime": cursor,
                  "endTime": end_ms - 1, "limit": 1000}
        response = session.get(BASE_URL, params=params, timeout=25)
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list) or len(rows) > 1000:
            raise ValueError("Invalid Binance.US historical kline response")
        if not rows:
            gaps.append({"start_ms": cursor, "end_exclusive_ms": end_ms,
                         "missing_5m": (end_ms - cursor) // FIVE})
            break
        for row in rows:
            if not isinstance(row, list) or len(row) < 7:
                raise ValueError("Malformed Binance.US 5m kline")
            opened, closed = int(row[0]), int(row[6])
            if opened < cursor or opened >= end_ms or opened % FIVE:
                raise ValueError(f"{symbol}: duplicate, future or unaligned 5m bar "
                                 f"open={opened} cursor={cursor} close={closed}")
            if opened > cursor:
                gaps.append({"start_ms": cursor, "end_exclusive_ms": opened,
                             "missing_5m": (opened - cursor) // FIVE,
                             "reason": "exchange_missing_5m"})
            if closed != opened + FIVE - 1:
                # The exchange sometimes reports a 5m kline whose close
                # timestamp is only ~1 minute after its open. This is NOT a
                # verified full 5-minute candle. Rebuild from FIVE real,
                # continuous, validated Binance.US 1m klines if possible.
                if len(repairs) >= MAX_1M_REBUILDS_PER_SYMBOL:
                    raise ValueError(f"{symbol}: too many malformed five-minute "
                                     "exchange candles; refusing bulk reconstruction")
                reconstructed = reconstruct_from_real_one_minute_bars(
                    session, symbol, opened
                )
                if reconstructed is None:
                    gaps.append({"start_ms": opened,
                                 "end_exclusive_ms": opened + FIVE,
                                 "missing_5m": 1,
                                 "reason": "invalid_5m_close_and_no_complete_1m_rebuild",
                                 "reported_close_ms": closed})
                else:
                    bars.append(reconstructed)
                    repairs.append({"open_ms": opened,
                                    "original_5m_close_ms": closed,
                                    "source": "five complete Binance.US 1m klines"})
            else:
                bars.append(checked_candle(row, opened, FIVE))
            cursor = opened + FIVE
    if with_repairs:
        return bars, gaps, repairs
    return bars, gaps


def contiguous_start(bars, expected_end):
    if not bars or bars[-1]["time"] != expected_end - FIVE:
        raise ValueError("Most recent 5m candles missing; refusing stale V2-A research")
    first = bars[-1]["time"]
    for previous in reversed(bars[:-1]):
        if previous["time"] != first - FIVE:
            break
        first = previous["time"]
    return first


def aggregate(bars, start_ms, end_ms, step_ms):
    """Construct true larger candles from complete consecutive real 5m bars."""
    if (start_ms % step_ms or end_ms % step_ms or
            len(bars) != (end_ms - start_ms) // FIVE):
        raise ValueError("Incomplete or unaligned five-minute history")
    factor = step_ms // FIVE
    if factor < 1 or factor * FIVE != step_ms:
        raise ValueError("Unsupported candle aggregation")
    output = []
    for offset in range(0, len(bars), factor):
        group = bars[offset:offset + factor]
        start = start_ms + offset * FIVE
        if len(group) != factor or any(
                bar["time"] != start + j * FIVE for j, bar in enumerate(group)):
            raise ValueError("Missing five-minute candle in aggregated timeframe")
        output.append({
            "time": start, "high": max(x["high"] for x in group),
            "low": min(x["low"] for x in group),
            "close": group[-1]["close"], "volume": sum(x["volume"] for x in group)
        })
    return output


def history(days=30, session=None, now_ms=None):
    if type(days) is not int or days not in DAYS_ALLOWED:
        raise ValueError("V2-A windows are 7, 14, or 30 days")
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    # Entire trailing 4-hour candle is omitted so all 4H data are settled.
    end = (now_ms // FOUR_HOURS - 1) * FOUR_HOURS
    requested_start = end - days * DAY
    fetch_start = requested_start - WARMUP
    client = session if session is not None else requests.Session()
    all_rows, gaps, repairs, starts = {}, {}, {}, {}
    for symbol in SYMBOLS:
        bars, missing, reconstructed = download_5m(
            client, symbol, fetch_start, end, now_ms, with_repairs=True)
        all_rows[symbol], gaps[symbol], repairs[symbol] = bars, missing, reconstructed
        starts[symbol] = contiguous_start(bars, end)

    latest_start = max(starts.values())
    safe_start = ((latest_start + WARMUP + FOUR_HOURS - 1) // FOUR_HOURS) * FOUR_HOURS
    analysis_start = max(requested_start, safe_start)
    usable_days = (end - analysis_start) / DAY
    if usable_days < days * 0.75:
        raise ValueError(
            f"Insufficient shared uninterrupted V2-A 5m history after 4H warmup: "
            f"requested {days}d, only {usable_days:.2f}d usable; "
            "no gap-filling or invented stops allowed."
        )
    aligned_start = analysis_start - WARMUP
    markets = {}
    for symbol in SYMBOLS:
        bars = [b for b in all_rows[symbol]
                if aligned_start <= b["time"] < end]
        if (not bars or len(bars) != (end - aligned_start) // FIVE
                or bars[0]["time"] != aligned_start or bars[-1]["time"] != end - FIVE):
            raise ValueError(f"{symbol}: missing data within proposed V2-A replay window")
        markets[symbol] = bars

    return {
        "format_version": 2, "source": "Binance.US public spot klines 5m",
        "requested_start_ms": requested_start,
        "analysis_start_ms": analysis_start, "analysis_end_ms": end,
        "warmup_start_ms": aligned_start,
        "coverage": {
            "requested_days": days,
            "actual_days": round(usable_days, 4),
            "retained_pct": round(100 * usable_days / days, 2),
            "trimmed_start_days": round((analysis_start - requested_start) / DAY, 4),
            "selection": "Same shared gap-free 5m trailing segment for all three markets",
            "gaps": gaps,
            "reconstructed_from_verified_1m": repairs
        },
        "as_of_utc": datetime.fromtimestamp(now_ms / 1000, timezone.utc).isoformat(),
        "symbols": markets
    }


def main():
    parser = argparse.ArgumentParser(description="Public 5m Binance.US history; no orders")
    parser.add_argument("--days", type=int, choices=DAYS_ALLOWED, default=30)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data = history(args.days)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(f"V2-A historical data: {data['coverage']['actual_days']} verified days for all markets")


if __name__ == "__main__":
    main()
