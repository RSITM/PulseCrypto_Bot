"""PulseCrypto V2-B — PUBLIC Binance.US snapshot collector, SHADOW RESEARCH ONLY.

Runs one bounded observation of BTC/ETH/SOL closed market candles, current
depth, and sampled public market trades. No order execution, no account state,
no personal credentials, no Telegram messages. Historical order books are
never fabricated. Every sampling delay is recorded. Safe to execute manually.
"""
import argparse
from datetime import datetime, timezone
import json
from math import isfinite
from pathlib import Path
import time

import requests

from intelligence import SYMBOLS, BASE_URL
from v2_shadow import (
    FIVE, FIFTEEN, HOUR, FOUR_HOURS, evaluate_v2,
    evaluate_v2_price_only, assess_depth,
)

FETCH_TIMEOUT = 12
FORWARD_LAG_MAX_MS = 150_000  # 2.5m from the last completed 5m bar
NEAR_BOOK_PCT = 0.0025
PAPER_NOTIONAL = 50.0
FIVE_BARS = 45
FOUR_HOUR_BARS = 55
RECENT_TRADES_LIMIT = 200
KEEP_BOOK_LEVELS = 20


def now_ms():
    return int(time.time() * 1000)


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()


def fetch(session, endpoint, params):
    # Explicit public GET endpoints only, never /order or SIGNED routes.
    if endpoint not in ("/api/v3/depth", "/api/v3/klines", "/api/v3/trades"):
        raise ValueError("Unsupported public market-data API route")
    response = session.get("https://api.binance.us" + endpoint,
                           params=params, timeout=FETCH_TIMEOUT)
    response.raise_for_status()
    return response.json()


def valid_kline(row, expected_open, step):
    if not isinstance(row, list) or len(row) < 7:
        raise ValueError("Malformed spot kline")
    opened, closed = int(row[0]), int(row[6])
    if opened != expected_open or closed != expected_open + step - 1:
        raise ValueError("Missing, unclosed, or abnormal exchange kline")
    candle = {"time": opened, "close": float(row[4]),
              "high": float(row[2]), "low": float(row[3]),
              "volume": float(row[5])}
    if (any(not isfinite(candle[k]) for k in ("close", "high", "low", "volume"))
            or candle["low"] <= 0 or candle["high"] < candle["close"]
            or candle["close"] < candle["low"] or candle["volume"] < 0):
        raise ValueError("Invalid market candle prices or volume")
    return candle


def fetch_closed_candles(session, symbol, interval, start, end, step):
    if (symbol not in SYMBOLS or interval not in ("5m", "15m")
            or type(start) is not int or type(end) is not int
            or start < 0 or end <= start or start % step or end % step):
        raise ValueError("Invalid candle request boundaries")
    count = (end - start) // step
    if count > 1000:
        raise ValueError("Too many candles for a single public request")
    raw = fetch(session, "/api/v3/klines", {
        "symbol": symbol, "interval": interval,
        "startTime": start, "endTime": end - 1, "limit": count
    })
    if not isinstance(raw, list) or len(raw) != count:
        raise ValueError(f"{symbol} {interval}: incomplete historical response")
    # Preserve UTC OPEN timestamps, fail closed on missing, duplicate,
    # non-sequential, unclosed, or truncated candles. No interpolation.
    return [valid_kline(row, start + i * step, step) for i, row in enumerate(raw)]


def aggregate_from_15m(rows, start, end, group_step):
    if (group_step not in (HOUR, FOUR_HOURS)
            or start % group_step or end % group_step or start >= end):
        raise ValueError("Unaligned higher-timeframe aggregation")
    factor = group_step // FIFTEEN
    selected = [row for row in rows if start <= row["time"] < end]
    if len(selected) != (end - start) // FIFTEEN:
        raise ValueError("Insufficient continuous 15m bars for higher timeframe")
    output = []
    for i in range(0, len(selected), factor):
        group = selected[i:i + factor]
        begin = start + i * FIFTEEN
        if len(group) != factor or any(
                bar["time"] != begin + j * FIFTEEN for j, bar in enumerate(group)):
            raise ValueError("15m gap inside aggregated higher-timeframe candle")
        output.append({
            "time": begin, "close": group[-1]["close"],
            "high": max(x["high"] for x in group),
            "low": min(x["low"] for x in group),
            "volume": sum(x["volume"] for x in group),
        })
    return output


def load_closed_four_timeframes(session, symbol, as_of_ms):
    """Require 55 full 4h bars derived from actual contiguous 15m history."""
    last_4h_end = as_of_ms // FOUR_HOURS * FOUR_HOURS
    last_15m_end = as_of_ms // FIFTEEN * FIFTEEN
    first_15m = last_4h_end - FOUR_HOUR_BARS * FOUR_HOURS
    quarters = fetch_closed_candles(
        session, symbol, "15m", first_15m, last_15m_end, FIFTEEN
    )
    fives = fetch_closed_candles(
        session, symbol, "5m", as_of_ms - FIVE_BARS * FIVE,
        as_of_ms, FIVE
    )
    return {
        "5m": fives,
        "15m": quarters[-80:],
        "1h": aggregate_from_15m(
            quarters, last_4h_end - FOUR_HOUR_BARS * HOUR,
            as_of_ms // HOUR * HOUR, HOUR)[-80:],
        "4h": aggregate_from_15m(
            quarters, first_15m, last_4h_end, FOUR_HOURS),
    }


def depth_snapshot(session, symbol, clock=now_ms):
    payload = fetch(session, "/api/v3/depth", {"symbol": symbol, "limit": 100})
    received_at = clock()  # REST book has NO exchange capture timestamp
    if not isinstance(payload, dict) or not isinstance(payload.get("lastUpdateId"), int):
        raise ValueError("Binance.US depth payload lacks update ID")
    raw_bids, raw_asks = payload.get("bids"), payload.get("asks")
    if not isinstance(raw_bids, list) or not isinstance(raw_asks, list):
        raise ValueError("Binance.US depth payload has no valid levels")
    def parse(levels):
        if len(levels) < 1:
            raise ValueError("Empty public order book")
        parsed = []
        for row in levels:
            if not isinstance(row, list) or len(row) != 2:
                raise ValueError("Invalid depth level")
            price, qty = float(row[0]), float(row[1])
            if (not isfinite(price) or not isfinite(qty)
                    or price <= 0 or qty <= 0):
                raise ValueError("Invalid public depth price or quantity")
            parsed.append([price, qty])
        return parsed
    bids, asks = parse(raw_bids), parse(raw_asks)
    if any(bids[i][0] <= bids[i + 1][0] for i in range(len(bids) - 1)):
        raise ValueError("Misordered public bids")
    if any(asks[i][0] >= asks[i + 1][0] for i in range(len(asks) - 1)):
        raise ValueError("Misordered public asks")
    if bids[0][0] >= asks[0][0]:
        raise ValueError("Crossed or locked spot order book")
    reference_bid, reference_ask = bids[0][0], asks[0][0]
    bid_notional = sum(p * q for p, q in bids if p >= reference_bid * (1 - NEAR_BOOK_PCT))
    ask_notional = sum(p * q for p, q in asks if p <= reference_ask * (1 + NEAR_BOOK_PCT))
    denominator = ask_notional + bid_notional
    book = {"timestamp_ms": received_at, "bids": bids, "asks": asks}
    impact = assess_depth(book, received_at, PAPER_NOTIONAL)
    return {
        "source": "Binance.US public REST /api/v3/depth, limit 100",
        "timestamp_kind": "client_REST_response_receipt_not_exchange_event",
        "received_at_ms": received_at,
        "received_at_utc": iso(received_at),
        "update_id": payload["lastUpdateId"],
        "best_bid": reference_bid, "best_ask": reference_ask,
        "spread_bps": impact.spread_bps,
        "near_bid_notional_usd": round(bid_notional, 4),
        "near_ask_notional_usd": round(ask_notional, 4),
        "depth_imbalance": round((bid_notional - ask_notional) / denominator, 6)
        if denominator > 0 else None,
        "paper_buy_vwap": impact.buy_vwap,
        "paper_buy_impact_bps": impact.impact_bps,
        "paper_liquidity_pass": impact.ok,
        "paper_liquidity_reason": impact.reason,
        "top_bids": bids[:KEEP_BOOK_LEVELS],
        "top_asks": asks[:KEEP_BOOK_LEVELS],
    }, book


def sample_recent_public_trades(session, symbol, clock=now_ms):
    """Sample ONLY last 200 public trades; not a continuous order-flow feed."""
    raw = fetch(session, "/api/v3/trades", {
        "symbol": symbol, "limit": RECENT_TRADES_LIMIT
    })
    received_at = clock()
    if not isinstance(raw, list) or len(raw) > RECENT_TRADES_LIMIT:
        raise ValueError("Invalid public recent-trade payload")
    buy_notional = sell_notional = 0.0
    buys = sells = 0
    cutoff = received_at - 60_000
    earliest = None
    latest = None
    for trade in raw:
        if not isinstance(trade, dict):
            raise ValueError("Malformed public recent-trade event")
        t = trade.get("time")
        p, q, maker = trade.get("price"), trade.get("qty"), trade.get("isBuyerMaker")
        if type(t) is not int or type(maker) is not bool:
            raise ValueError("Invalid recent-trade timestamp or maker side")
        if t > received_at + 2000 or t < 0:
            raise ValueError("Future/invalid public trade timestamp")
        price, quantity = float(p), float(q)
        if not isfinite(price) or price <= 0 or not isfinite(quantity) or quantity <= 0:
            raise ValueError("Invalid public trade price/quantity")
        earliest = t if earliest is None else min(earliest, t)
        latest = t if latest is None else max(latest, t)
        if t >= cutoff and t <= received_at:
            if maker:  # buyer was resting maker -> seller-aggressor
                sells += 1
                sell_notional += price * quantity
            else:
                buys += 1
                buy_notional += price * quantity
    denominator = buy_notional + sell_notional
    return {
        "source": "Binance.US public last 200 /api/v3/trades",
        "received_at_ms": received_at,
        "last_60s_buyer_aggressor_count": buys,
        "last_60s_seller_aggressor_count": sells,
        "last_60s_buyer_aggressor_notional_usd": round(buy_notional, 4),
        "last_60s_seller_aggressor_notional_usd": round(sell_notional, 4),
        "last_60s_imbalance": round((buy_notional - sell_notional) / denominator, 6)
        if denominator else None,
        "last_60s_window_coverage": (
            "older_trade_confirms_window_start"
            if earliest is not None and earliest <= cutoff
            else "PARTIAL_OR_UNVERIFIED_recent_200_only"
        ),
        "latest_trade_time_ms": latest,
        "sampled_trades": len(raw),
        "note": "Snapshot of recent trades; not streaming CVD or a complete trade tape",
    }


def collect_once(session=None, clock=now_ms):
    """Capture ONE observation. All errors are explicit; no trading side effects."""
    session = session if session is not None else requests.Session()
    started = clock()
    # Snapshot timing never assumed equal to candle close.
    as_of_ms = started // FIVE * FIVE
    record = {
        "schema": "pulsecrypto-v2b-forward-observation-v1",
        "mode": "RESEARCH_SHADOW_NO_ORDERS",
        "started_at_ms": started, "started_at_utc": iso(started),
        "signal_closed_at_ms": as_of_ms,
        "signal_closed_at_utc": iso(as_of_ms),
        "exchange": "Binance.US public BTCUSDT ETHUSDT SOLUSDT spot",
        "paper_notional_usd": PAPER_NOTIONAL,
        "simulation": "observations only; no entries, exits or balance mutations",
        "symbols": {},
    }
    for symbol in SYMBOLS:
        result = {"symbol": symbol, "signal_closed_at_ms": as_of_ms}
        history = None
        try:
            history = load_closed_four_timeframes(session, symbol, as_of_ms)
            result["candles_status"] = "verified_contiguous_closed"
            result["candle_last_5m_open_ms"] = history["5m"][-1]["time"]
            result["candle_last_4h_open_ms"] = history["4h"][-1]["time"]
            # Signal candidate does not assume or fabricate historic order books.
            result["price_only"] = evaluate_v2_price_only(
                symbol, history, as_of_ms).to_dict()
        except (ValueError, TypeError, KeyError, OverflowError,
                requests.RequestException) as err:
            result["candles_status"] = "UNAVAILABLE"
            result["candles_error"] = type(err).__name__ + ": " + str(err)[:160]
            result["price_only"] = None

        try:
            book_public, raw_book = depth_snapshot(session, symbol, clock)
            result["order_book"] = book_public
            elapsed = book_public["received_at_ms"] - as_of_ms
            result["observation_lag_ms"] = elapsed
            if elapsed < 0 or elapsed > FORWARD_LAG_MAX_MS:
                result["observation_status"] = "DELAYED_NOT_AN_EXECUTION_TIME_SIGNAL"
                result["full_v2"] = None
            elif history is None:
                result["observation_status"] = "CANDLES_UNAVAILABLE"
                result["full_v2"] = None
            else:
                result["observation_status"] = "ON_TIME_SHADOW_RESEARCH"
                result["full_v2"] = evaluate_v2(
                    symbol, history, as_of_ms, order_book=raw_book,
                    intended_notional_usd=PAPER_NOTIONAL,
                    observed_at_ms=book_public["received_at_ms"],
                ).to_dict()
        except (ValueError, TypeError, KeyError, OverflowError,
                requests.RequestException) as err:
            result["order_book"] = None
            result["observation_status"] = "DEPTH_UNAVAILABLE"
            result["depth_error"] = type(err).__name__ + ": " + str(err)[:160]
            result["full_v2"] = None

        try:
            result["recent_trades"] = sample_recent_public_trades(
                session, symbol, clock)
        except (ValueError, TypeError, KeyError, OverflowError,
                requests.RequestException) as err:
            result["recent_trades"] = None
            result["flow_status"] = "UNAVAILABLE"
            result["flow_error"] = type(err).__name__ + ": " + str(err)[:160]
        record["symbols"][symbol] = result
    record["finished_at_ms"] = clock()
    record["finished_at_utc"] = iso(record["finished_at_ms"])
    return record


def summarize(record):
    lines = [
        "## PulseCrypto V2-B — forward public depth research",
        "",
        "**OBSERVATION ONLY. NO live or paper orders, no account updates, "
        "no Telegram or Turso writes.**",
        "",
        f'**Started:** {record["started_at_utc"]}',
        f'**Last fully closed 5M boundary:** {record["signal_closed_at_utc"]}',
        "",
        "| Market | Price-only setup | Full depth-gated V2 | Sample lag | Spot spread | Depth imbalance | Recent trade sample |",
        "|---|---|---|---|---|---|---|",
    ]
    for symbol, sample in record["symbols"].items():
        price = sample.get("price_only")
        gated = sample.get("full_v2")
        book = sample.get("order_book") or {}
        trades = sample.get("recent_trades") or {}
        lag = sample.get("observation_lag_ms")
        lines.append(
            f'| {symbol} | {price["action"] if price else "NO_DATA"} '
            f'| {gated["action"] if gated else sample.get("observation_status", "NO_DATA")} '
            f'| {f"{lag/1000:.1f}s" if lag is not None else "N/A"} '
            f'| {f"{book["spread_bps"]:.2f} bps" if book.get("spread_bps") is not None else "N/A"} '
            f'| {f"{book["depth_imbalance"]:.3f}" if book.get("depth_imbalance") is not None else "N/A"} '
            f'| {trades.get("sampled_trades", "N/A")} |'
        )
    lines += [
        "", "**Book time is client REST response receipt, not an exchange event timestamp.**",
        "Depth is resting visible liquidity, which can be canceled or spoofed; "
        "last 200 public trades cannot reproduce continuous order flow.",
        "GitHub scheduled runs can arrive late or be skipped. Delayed observations "
        "are kept as data and NEVER relabeled as timely trade entries.",
        "All setup thresholds are unvalidated and research-only.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Read-only public BTC/ETH/SOL depth and 5m forward sampler")
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = collect_once()
    for output in (args.out, args.markdown):
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(
        json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )
    if args.markdown:
        Path(args.markdown).write_text(summarize(result), encoding="utf-8")
    print("V2-B PUBLIC RESEARCH SNAPSHOT. No orders or portfolio writes. "
          + ", ".join(f'{sym}: {data.get("observation_status")}'
                      for sym, data in result["symbols"].items()))


if __name__ == "__main__":
    main()
