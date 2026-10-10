"""PulseCrypto V2-A offline historical PRICE-ACTION ONLY benchmark vs V1.

Uses the same real gap-free 5-minute data and matching dates for BTC/ETH/SOL.
V2-A: 4H/1H bias, 15M pullback, 5M breakout, no historical order book.
No real trades, no production paper state, no connected app writes.
"""
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path

from historical_backtest import replay as replay_v1
from intelligence import SYMBOLS
from paper_trading import PaperAccount
from v2_shadow import (FIVE, FIFTEEN, HOUR, FOUR_HOURS, INTERVALS,
                       FEE_PER_SIDE, ADVERSE_SLIPPAGE_PER_SIDE,
                       MIN_REWARD_RISK, MIN_NET_REWARD_PCT,
                       evaluate_v2_price_only)
from v2a_history import WARMUP, DAY, aggregate


def stamp(t):
    return datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def validate(data):
    if not isinstance(data, dict) or data.get("format_version") != 2:
        raise ValueError("Unsupported V2-A dataset")
    if data.get("source") != "Binance.US public spot klines 5m":
        raise ValueError("Unexpected V2-A market history")
    start, end, warmup = (data.get(k) for k in
                          ("analysis_start_ms", "analysis_end_ms", "warmup_start_ms"))
    if any(type(t) is not int for t in (start, end, warmup)):
        raise ValueError("Invalid V2-A historical timestamps")
    if (start % FOUR_HOURS or end % FOUR_HOURS or warmup % FOUR_HOURS
            or warmup != start - WARMUP or not warmup < start < end
            or end - start > 30 * DAY):
        raise ValueError("Invalid V2-A historical coverage")
    coverage = data.get("coverage")
    requested = data.get("requested_start_ms")
    if (not isinstance(coverage, dict) or type(requested) is not int
            or coverage.get("requested_days") not in (7, 14, 30)
            or type(coverage["requested_days"]) is not int
            or end - requested != coverage["requested_days"] * DAY
            or start < requested or (end - start) < (end - requested) * .75):
        raise ValueError("V2-A backtest has incomplete or invalid coverage")
    markets = data.get("symbols")
    if not isinstance(markets, dict) or set(markets) != set(SYMBOLS):
        raise ValueError("All BTC/ETH/SOL histories are required")
    expected = (end - warmup) // FIVE
    for symbol, bars in markets.items():
        if not isinstance(bars, list) or len(bars) != expected:
            raise ValueError(f"{symbol}: incomplete five-minute history")
        for index, bar in enumerate(bars):
            if not isinstance(bar, dict) or set(bar) != {
                    "time", "open", "high", "low", "close", "volume"}:
                raise ValueError(f"{symbol}: malformed historical five-minute bar")
            if bar["time"] != warmup + index * FIVE:
                raise ValueError(f"{symbol}: missing or unordered five-minute candles")
            prices = [bar[k] for k in ("open", "high", "low", "close")]
            from math import isfinite
            if (any(type(v) not in (int, float) or not isfinite(v) or v <= 0 for v in prices)
                    or not bar["low"] <= min(bar["open"], bar["close"])
                    or max(bar["open"], bar["close"]) > bar["high"]
                    or type(bar["volume"]) not in (int, float)
                    or not isfinite(bar["volume"]) or bar["volume"] < 0):
                raise ValueError(f"{symbol}: invalid five-minute OHLCV")
    return start, end, warmup


def build_frames(data, warmup, end):
    """No data is synthesized: every candle is constructed from real 5m bars."""
    markets = {}
    for symbol, source in data["symbols"].items():
        markets[symbol] = {
            "5m": [{k: value for k, value in bar.items() if k != "open"}
                   for bar in source],
            "15m": aggregate(source, warmup, end, FIFTEEN),
            "1h": aggregate(source, warmup, end, HOUR),
            "4h": aggregate(source, warmup, end, FOUR_HOURS),
        }
    return markets


def fill_is_valid(pending, market_open, fee, slip):
    """Risk and after-cost reward must survive repricing at NEXT bar open."""
    if any(v is None for v in (pending.stop, pending.target)):
        return False
    fill = market_open * (1 + slip)
    stop, target = pending.stop, pending.target
    if not (0 < stop < market_open and fill < target):
        return False
    risk = fill - stop
    if (target - fill) / risk < MIN_REWARD_RISK:
        return False
    exit_net = target * (1 - slip) * (1 - fee)
    buy_cost = fill * (1 + fee)
    return (exit_net - buy_cost) / fill >= MIN_NET_REWARD_PCT


def simulate_v2a(data, evaluator=evaluate_v2_price_only):
    start, end, warmup = validate(data)
    frames = build_frames(data, warmup, end)
    timestamp_maps = {
        symbol: {tf: [x["time"] for x in rows]
                 for tf, rows in symbol_frames.items()}
        for symbol, symbol_frames in frames.items()
    }
    cash = PaperAccount()
    pending = {}
    decisions = Counter()
    individual = {symbol: Counter() for symbol in SYMBOLS}
    positions_opened = 0
    first_entry = None
    first_entry_market_open = None
    equity_peak = cash.starting_equity
    maximum_drawdown_pct = 0.0
    equity = cash.starting_equity

    for bar_time in range(start, end, FIVE):
        index = (bar_time - warmup) // FIVE
        source_bars = {symbol: data["symbols"][symbol][index] for symbol in SYMBOLS}
        day = datetime.fromtimestamp(bar_time / 1000, timezone.utc).date().isoformat()
        cash.roll_day(day, {symbol: source_bars[symbol]["open"]
                            for symbol in cash.positions}
                      if cash.positions else None)
        closed_here = set()

        # Prior-candle signals may enter at the NEXT candle OPEN, never
        # with knowledge of this candle's high/low/closing price.
        for symbol, candidate in tuple(pending.items()):
            market_open = source_bars[symbol]["open"]
            if symbol in cash.positions:
                reason = "ENTRY_BLOCKED: already in position"
            elif not fill_is_valid(candidate, market_open, cash.fee_rate,
                                   cash.slippage_rate):
                reason = "ENTRY_BLOCKED: next-open invalidates after-cost R:R"
            else:
                outcome = cash.open_long(symbol, market_open,
                                         candidate.stop, candidate.target)
                if outcome == "PAPER_BUY":
                    positions_opened += 1
                    if first_entry is None:
                        first_entry = stamp(bar_time)
                        first_entry_market_open = market_open
                    reason = "PAPER_BUY"
                else:
                    reason = "ENTRY_BLOCKED: " + outcome
            decisions[reason] += 1
            individual[symbol][reason] += 1
            del pending[symbol]

        # Stops and targets are simulated on the next 5m high/low. If both
        # touch within one bar, PaperAccount conservatively chooses the stop.
        for symbol in SYMBOLS:
            if symbol in cash.positions:
                row = source_bars[symbol]
                if cash.on_candle(symbol, row["low"], row["high"]) == "PAPER_SELL":
                    closed_here.add(symbol)
                    decisions["PAPER_SELL"] += 1
                    individual[symbol]["PAPER_SELL"] += 1

        # Only now the bar is closed. Reconstruct the latest fully CLOSED bar
        # in each higher timeframe, without leaking incomplete 15m/1h/4h bars.
        as_of = bar_time + FIVE
        for symbol in SYMBOLS:
            if symbol in cash.positions or symbol in closed_here:
                continue
            history = {}
            for timeframe, step in INTERVALS.items():
                times = timestamp_maps[symbol][timeframe]
                cutoff = bisect_right(times, as_of - step)
                history[timeframe] = frames[symbol][timeframe][max(0, cutoff - 100):cutoff]
            decision = evaluator(symbol, history, as_of)
            decisions[decision.reason] += 1
            individual[symbol][decision.reason] += 1
            if decision.action == "CANDIDATE_PRICE_ONLY":
                pending[symbol] = decision

        equity = cash.equity({symbol: source_bars[symbol]["close"]
                              for symbol in cash.positions})
        equity_peak = max(equity_peak, equity)
        maximum_drawdown_pct = max(
            maximum_drawdown_pct, (equity_peak - equity) / equity_peak * 100)

    if pending:
        # Last candle has no following OPEN in the dataset: no phantom fills.
        decisions["PENDING_AT_END_UNFILLED"] = len(pending)
    trades = cash.trades
    wins = [t["net_pnl"] for t in trades if t["net_pnl"] > 0]
    losses = [t["net_pnl"] for t in trades if t["net_pnl"] < 0]
    return {
        "mode": "V2A_HISTORICAL_CANDLE_ONLY_RESEARCH",
        "order_book_history": "UNAVAILABLE: not simulated or inferred",
        "first_entry": first_entry,
        "first_entry_actual_next_bar_open": first_entry_market_open,
        "paper_entries": positions_opened, "closed_trades": len(trades),
        "open_positions": len(cash.positions),
        "wins": len(wins), "losses": len(losses),
        "win_rate_pct": 100 * len(wins) / len(trades) if trades else None,
        "profit_factor": (sum(wins) / -sum(losses) if losses else None),
        "net_realized_pnl_usd": round(sum(t["net_pnl"] for t in trades), 4),
        "closed_trade_fees_usd": round(
            sum(t["entry_fee"] + t["exit_fee"] for t in trades), 4),
        "ending_marked_equity_usd": round(equity, 4),
        "total_return_pct": round(100 * (equity / cash.starting_equity - 1), 4),
        "max_drawdown_pct": round(maximum_drawdown_pct, 4),
        "rejections": dict(decisions),
        "by_symbol": {sym: dict(counts) for sym, counts in individual.items()},
        "trades": trades,
    }


def compare(data, evaluator=evaluate_v2_price_only):
    start, end, warmup = validate(data)
    frames = build_frames(data, warmup, end)
    v1_dataset = {
        "format_version": 1, "source": "Binance.US public spot klines",
        "hourly_source": "Constructed from complete common five-minute candles",
        "analysis_start_ms": start, "analysis_end_ms": end,
        "requested_start_ms": data["requested_start_ms"],
        "coverage": {
            "requested_days": data["coverage"]["requested_days"],
            "gaps_in_requested_fetch": data["coverage"]["gaps"],
            "retained_pct": data["coverage"]["retained_pct"],
            "trimmed_start_days": data["coverage"]["trimmed_start_days"],
            "actual_days": data["coverage"]["actual_days"],
        },
        "symbols": {
            sym: {"15m": frames[sym]["15m"], "1h": frames[sym]["1h"]}
            for sym in SYMBOLS
        }
    }
    return {
        "mode": "MATCHED_PERIOD_V1_V2A_HISTORICAL_RESEARCH",
        "source": data["source"],
        "market_period": {
            "start": stamp(start), "end_exclusive": stamp(end),
            "actual_days": (end-start) / DAY,
            "requested_days": data["coverage"]["requested_days"]
        },
        "coverage": data["coverage"],
        "V1_control": replay_v1(v1_dataset),
        "V2A_candle_only": simulate_v2a(data, evaluator),
        "limitations": [
            "V2-A does not include actual historical order books or depth checks.",
            "The V2-A candle signal is filled at the NEXT 5m bar's opening price plus modeled slippage.",
            "Fees/slippage assumed from existing paper account, not confirmed exchange quotations.",
            "V1 baseline uses its ORIGINAL historical execution assumptions and 15m schedule, not V2-A's 5m entry model.",
            "A matched calendar period does not imply identical entry opportunity sets or execution models.",
            "An uninterrupted trailing segment after historical gaps introduces selection bias.",
            "No trading, portfolio write, Telegram change, scheduling, or secret usage occurs.",
        ],
    }


def markdown(result):
    v1, v2 = result["V1_control"], result["V2A_candle_only"]
    def value(x):
        return "N/A" if x is None else f"{x:.2f}"
    lines = [
        "# PulseCrypto — V1 vs V2-A matched-period research",
        "",
        "**RESEARCH ONLY. No account updates, order books, broker access or real trades.**",
        "",
        f'**Historical window:** {result["market_period"]["start"]} to '
        f'{result["market_period"]["end_exclusive"]} (exclusive)',
        f'**Usable duration:** {result["market_period"]["actual_days"]:.2f} days '
        f'of {result["market_period"]["requested_days"]} requested',
        "",
        "| Metric | V1 control | V2-A 5m candle-only |",
        "|---|---:|---:|",
        f'| Entries | {v1["paper_entries"]} | {v2["paper_entries"]} |',
        f'| Closed trades | {v1["closed_trades"]} | {v2["closed_trades"]} |',
        f'| Closed win rate | {value(v1["win_rate_pct"])}% | {value(v2["win_rate_pct"])}% |',
        f'| Profit factor | {value(v1["profit_factor"])} | {value(v2["profit_factor"])} |',
        f'| Realized net P/L | USD {v1["realized_net_pnl_usd"]:+.2f} | USD {v2["net_realized_pnl_usd"]:+.2f} |',
        f'| Total marked return | {v1["total_equity_return_pct"]:+.2f}% | {v2["total_return_pct"]:+.2f}% |',
        f'| Peak-to-trough marked drawdown | {v1["max_marked_equity_drawdown_pct"]:.2f}% | {v2["max_drawdown_pct"]:.2f}% |',
        f'| Fees on closed trades | USD {v1["closed_trade_fees_usd"]:.2f} | USD {v2["closed_trade_fees_usd"]:.2f} |',
        "",
        "## V2-A price-only signal decisions",
        "",
    ]
    lines.extend(f'- {reason}: {count}' for reason, count in
                 sorted(v2["rejections"].items(), key=lambda item: -item[1]))
    lines += ["", "## Research limitations", ""]
    lines += ["- " + reason for reason in result["limitations"]]
    if not v1["closed_trades"] or not v2["closed_trades"]:
        lines += ["", "**One or both variants had zero closed trades. No win-rate claim is justified.**"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="V2-A offline historical comparison")
    parser.add_argument("--data", required=True)
    parser.add_argument("--json", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    result = compare(json.loads(Path(args.data).read_text(encoding="utf-8")))
    for name in (args.json, args.markdown):
        Path(name).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                                encoding="utf-8")
    Path(args.markdown).write_text(markdown(result), encoding="utf-8")
    print(f"RESEARCH ONLY: V1 {result['V1_control']['closed_trades']} closed, "
          f"V2-A {result['V2A_candle_only']['closed_trades']} closed; NO LIVE CHANGES")


if __name__ == "__main__":
    main()
