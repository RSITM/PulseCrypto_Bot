"""Read-only historical TJR-public-concept benchmark against V1 and V2-A.

Requires previously verified gap-free real Binance.US 5-minute OHLCV.
Only past CLOSED candles inform decision; hypothetical orders rest from NEXT
five-minute candle onward and expire after 12 candles. No orders or secrets.
Longs are SPOT paper simulations; shorts are THEORETICAL only (no broker,
margin, borrowing, funding, liquidation, maker/taker guarantees). This is
NOT a reconstruction of proprietary TJR settings or a profitable strategy.
"""
import argparse
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from intelligence import SYMBOLS
from v2_shadow import FIVE, HOUR, FOUR_HOURS
from v2a_backtest import build_frames, validate, compare as compare_existing, stamp
from tjr_ict_shadow import (VARIANTS, VARIANT_BY_NAME, TJRScanner, ORDER_EXPIRY_BARS,
                            FEE_PER_SIDE, ADVERSE_SLIPPAGE_PER_SIDE)
from v2a_history import DAY

START_EQUITY = 500.0
RISK_PER_TRADE = 0.005
DAILY_LOSS_STOP = .02
MAX_POSITIONS = 2
MIN_NOTIONAL = 1.0


def _exit_fill(reference, side, fee=FEE_PER_SIDE, slip=ADVERSE_SLIPPAGE_PER_SIDE):
    return reference * (1 - slip if side == "LONG" else 1 + slip)


def _entry_fill(reference, side, slip=ADVERSE_SLIPPAGE_PER_SIDE):
    return reference * (1 + slip if side == "LONG" else 1 - slip)


def mark_equity(balance, positions, marks):
    result = balance
    for symbol, pos in positions.items():
        price = marks[symbol]
        reference = _exit_fill(price, pos["side"])
        direction = 1 if pos["side"] == "LONG" else -1
        # Position already paid entry fee on entry via balance adjustment.
        result += direction * (reference - pos["fill"]) * pos["qty"]
        result -= reference * pos["qty"] * FEE_PER_SIDE
    return result


def make_entry(signal, exposure_available, equity, market_open):
    """Model resting limit orders; discard unfillable/crossed/gap-stop levels."""
    entry, stop, target, side = signal.entry, signal.stop, signal.target, signal.side
    if any(type(x) not in (int, float) or x <= 0 for x in (entry, stop, target, market_open)):
        return None
    if side == "LONG":
        if not stop < entry < target or market_open <= stop:
            return None
    elif side == "THEORETICAL_SHORT":
        if not target < entry < stop or market_open >= stop:
            return None
    else:
        return None
    assumed_fill = _entry_fill(entry, side)
    risk = (assumed_fill - stop if side == "LONG" else stop - assumed_fill)
    per_unit_risk = risk + FEE_PER_SIDE * (assumed_fill + stop)
    if per_unit_risk <= 0 or assumed_fill <= 0 or equity <= 0:
        return None
    # Capital/exposure cap equivalent to at most 1x notional, including
    # hypothetical shorts (NOT a realistic funded margin account).
    qty = min((START_EQUITY * RISK_PER_TRADE) / per_unit_risk,
              max(exposure_available, 0) / (assumed_fill * (1 + FEE_PER_SIDE)))
    if qty <= 0 or qty * assumed_fill < MIN_NOTIONAL:
        return None
    fee = qty * assumed_fill * FEE_PER_SIDE
    return {
        "side": side, "symbol": signal.symbol, "qty": qty,
        "fill": assumed_fill, "entry_fee": fee,
        "signal_at_ms": signal.as_of_ms, "entry_limit": entry,
        "stop": stop, "target": target, "zone_kind": signal.zone_kind,
        "pool": signal.swept_pool, "context": signal.context,
        "target_source": signal.target_source,
        "entry_at_ms": None, "entry_open": market_open,
    }


def exit_price(bar, pos, allow_target=True):
    """Conservative stop-first 5m high/low outcome with explicitly uncertain ordering."""
    side = pos["side"]
    if side == "LONG":
        if bar["low"] <= pos["stop"]:
            return min(pos["stop"], bar["low"]), "STOP"
        if allow_target and bar["high"] >= pos["target"]:
            return pos["target"], "TARGET"
    else:
        if bar["high"] >= pos["stop"]:
            return max(pos["stop"], bar["high"]), "STOP"
        if allow_target and bar["low"] <= pos["target"]:
            return pos["target"], "TARGET"
    return None, None


def replay(data, variant, *, start_ms=None, end_ms=None):
    if variant not in VARIANTS:
        raise ValueError("Unknown frozen TJR variant")
    full_start, full_end, warmup = validate(data)
    start = full_start if start_ms is None else start_ms
    end = full_end if end_ms is None else end_ms
    if (type(start) is not int or type(end) is not int
            or start < full_start or end > full_end
            or start >= end or start % FOUR_HOURS or end % FOUR_HOURS):
        raise ValueError("Invalid aligned research subwindow")
    frames = build_frames(data, warmup, full_end)
    indices = {sym: {
        tf: [b["time"] for b in frames[sym][tf]]
        for tf in ("1h", "4h")
    } for sym in SYMBOLS}
    scanner = TJRScanner(variant)
    pending = {}
    positions = {}
    reasons = Counter()
    by_symbol = {s: Counter() for s in SYMBOLS}
    completed = []
    equity = START_EQUITY
    peak = START_EQUITY
    maximum_dd = 0
    day_start = START_EQUITY
    daily_net = 0
    last_day = None
    simulated_entries = 0

    for bar_time in range(start, end, FIVE):
        i = (bar_time - warmup) // FIVE
        current = {sym: data["symbols"][sym][i] for sym in SYMBOLS}
        as_of = bar_time + FIVE
        day = datetime.fromtimestamp(bar_time / 1000, timezone.utc).date()
        if day != last_day:
            last_day = day
            day_start = mark_equity(equity, positions,
                                    {sym: current[sym]["open"] for sym in positions})
            daily_net = 0
        touched_today = set()

        # First update only positions that existed BEFORE the current bar.
        # A later mark/target on an entry bar cannot be inferred from OHLC.
        for sym, pos in list(positions.items()):
            raw_exit, cause = exit_price(current[sym], pos)
            if cause is None:
                continue
            exit_fill = _exit_fill(raw_exit, pos["side"])
            sign = 1 if pos["side"] == "LONG" else -1
            entry_fee = pos["entry_fee"]
            exit_fee = pos["qty"] * exit_fill * FEE_PER_SIDE
            net = sign * pos["qty"] * (exit_fill - pos["fill"]) - entry_fee - exit_fee
            equity += sign * pos["qty"] * (exit_fill - pos["fill"]) - exit_fee
            daily_net += net
            completed.append({
                "market": sym, "side": pos["side"],
                "entered_at_utc": stamp(pos["entry_at_ms"]),
                "exited_at_utc": stamp(as_of),
                "signal_at_utc": stamp(pos["signal_at_ms"]),
                "zone_kind": pos["zone_kind"], "swept_pool": pos["pool"],
                "target_source": pos["target_source"],
                "entry_limit": pos["entry_limit"],
                "modeled_entry": round(pos["fill"], 8),
                "modeled_exit": round(exit_fill, 8),
                "stop": pos["stop"], "target": pos["target"],
                "exit_reason": cause,
                "entry_fee_usd": round(entry_fee, 5),
                "exit_fee_usd": round(exit_fee, 5),
                "net_pnl_usd": round(net, 5),
                "stop_overshoot_per_unit": round(
                    max(pos["stop"] - current[sym]["low"], 0)
                    if pos["side"] == "LONG" and cause == "STOP" else
                    max(current[sym]["high"] - pos["stop"], 0)
                    if cause == "STOP" else 0, 8),
            })
            del positions[sym]
            touched_today.add(sym)
            reasons["PAPER_CLOSE_" + cause] += 1

        # Resting LIMIT orders may fill starting strictly after the signal
        # candle. They expire; missing opportunity does not become market buy.
        for sym, order in list(pending.items()):
            if sym in positions or sym in touched_today:
                del pending[sym]
                reasons["PENDING_POSITION_CONFLICT"] += 1
                continue
            signal = order["signal"]
            age = (bar_time - signal.as_of_ms) // FIVE
            if age >= ORDER_EXPIRY_BARS:
                del pending[sym]
                reasons["PENDING_EXPIRED"] += 1
                continue
            row = current[sym]
            condition = row["low"] <= signal.entry if signal.side == "LONG" else (
                row["high"] >= signal.entry)
            # Gap through stop makes a nominal limit fill unjustified.
            crossed_stop = (row["open"] <= signal.stop if signal.side == "LONG"
                            else row["open"] >= signal.stop)
            if not condition or crossed_stop:
                if crossed_stop:
                    del pending[sym]
                    reasons["PENDING_GAP_BEYOND_STOP"] += 1
                continue
            if len(positions) >= MAX_POSITIONS or daily_net <= -DAILY_LOSS_STOP * day_start:
                del pending[sym]
                reasons["PENDING_RISK_LIMIT"] += 1
                continue
            spent = sum(pos["qty"] * pos["fill"] for pos in positions.values())
            new = make_entry(signal, max(0, equity - spent), equity, row["open"])
            if new is None:
                del pending[sym]
                reasons["PENDING_ENTRY_INVALID"] += 1
                continue
            new["entry_at_ms"] = bar_time
            equity -= new["entry_fee"]
            positions[sym] = new
            simulated_entries += 1
            del pending[sym]
            touched_today.add(sym)
            reasons["PAPER_ENTRY"] += 1
            by_symbol[sym]["PAPER_ENTRY"] += 1

            # Conservative: entry-bar stop could have been hit AFTER fill;
            # never award a target on the same bar without ordering data.
            raw_exit, cause = exit_price(row, new, allow_target=False)
            if cause == "STOP":
                price = _exit_fill(raw_exit, new["side"])
                direction = 1 if new["side"] == "LONG" else -1
                exit_fee = new["qty"] * price * FEE_PER_SIDE
                net = (direction * new["qty"] * (price - new["fill"])
                       - new["entry_fee"] - exit_fee)
                equity += direction * new["qty"] * (price - new["fill"]) - exit_fee
                daily_net += net
                completed.append({
                    "market": sym, "side": new["side"],
                    "entered_at_utc": stamp(bar_time),
                    "exited_at_utc": stamp(as_of),
                    "signal_at_utc": stamp(signal.as_of_ms),
                    "zone_kind": new["zone_kind"], "swept_pool": new["pool"],
                    "target_source": new["target_source"],
                    "entry_limit": new["entry_limit"],
                    "modeled_entry": round(new["fill"], 8),
                    "modeled_exit": round(price, 8),
                    "stop": new["stop"], "target": new["target"],
                    "exit_reason": "ENTRY_BAR_STOP_CONSERVATIVE",
                    "entry_fee_usd": round(new["entry_fee"], 5),
                    "exit_fee_usd": round(exit_fee, 5),
                    "net_pnl_usd": round(net, 5),
                    "stop_overshoot_per_unit": round(
                        max(new["stop"] - row["low"], 0)
                        if new["side"] == "LONG"
                        else max(row["high"] - new["stop"], 0), 8),
                })
                del positions[sym]
                reasons["PAPER_ENTRY_BAR_STOP"] += 1

        # Scan at closed 5m boundary. No future or partly closed HTF data.
        for sym in SYMBOLS:
            raw5 = data["symbols"][sym][max(0, i - 599):i + 1]
            higher = {}
            for tf, step in (("1h", HOUR), ("4h", FOUR_HOURS)):
                limit = bisect_right(indices[sym][tf], as_of - step)
                higher[tf] = frames[sym][tf][max(0, limit - 60):limit]
            decision = scanner.on_closed_candle(sym, raw5, higher["1h"],
                                                higher["4h"], as_of)
            reasons[decision.action] += 1
            by_symbol[sym][decision.action] += 1
            if decision.action == "RESEARCH_LIMIT_ORDER":
                if sym in positions or sym in pending or sym in touched_today:
                    reasons["SIGNAL_POSITION_CONFLICT"] += 1
                elif (decision.side == "LONG" and decision.stop < decision.entry < decision.target
                      or decision.side == "THEORETICAL_SHORT" and
                      decision.target < decision.entry < decision.stop):
                    pending[sym] = {"signal": decision}
                    reasons["PENDING_PLACED"] += 1
        current_marks = {s: current[s]["close"] for s in positions}
        marked = mark_equity(equity, positions, current_marks)
        peak = max(peak, marked)
        maximum_dd = max(maximum_dd, 100 * (peak - marked) / peak)

    wins = [x["net_pnl_usd"] for x in completed if x["net_pnl_usd"] > 0]
    losses = [x["net_pnl_usd"] for x in completed if x["net_pnl_usd"] < 0]
    ending_marked = mark_equity(equity, positions, {
        s: data["symbols"][s][(end - FIVE - warmup) // FIVE]["close"]
        for s in positions
    })
    return {
        "variant": variant.name,
        "mode": "TJR_PUBLIC_METHOD_HISTORICAL_PAPER_ONLY",
        "period": {"start": stamp(start), "end_exclusive": stamp(end)},
        "entries": simulated_entries, "closed_trades": len(completed),
        "open_positions": len(positions), "unfilled_pending_at_end": len(pending),
        "wins": len(wins), "losses": len(losses),
        "win_rate_pct": round(100 * len(wins) / len(completed), 3) if completed else None,
        "profit_factor": round(sum(wins) / -sum(losses), 4) if losses else None,
        "net_realized_pnl_usd": round(sum(x["net_pnl_usd"] for x in completed), 4),
        "closed_trade_fees_usd": round(
            sum(x["entry_fee_usd"] + x["exit_fee_usd"] for x in completed), 4),
        "marked_equity_usd": round(ending_marked, 4),
        "total_return_pct": round(100 * (ending_marked / START_EQUITY - 1), 4),
        "max_drawdown_pct": round(maximum_dd, 4),
        "decisions": dict(reasons),
        "by_symbol": {s: dict(d) for s, d in by_symbol.items()},
        "trades": completed,
        "notes": [
            "Simulation only: all limit orders are synthetic; no actual exchange orders.",
            "THEORETICAL_SHORT excludes borrowing/financing/funding, futures "
            "mark/maintenance margin, liquidations and market access; no real shorts.",
            "Entry limit triggered only from bars AFTER candle-close signal; "
            "assumes a resting fill at the nominal limit + adverse slippage.",
            "If stop and target overlap in a bar, assume stop first. "
            "Entry bar can trigger a conservative stop, never same-bar target.",
            "Stops filled at worse 5m extremes plus modeled adverse slippage; "
            "not executable price guarantees.",
            "Fees are 0.26% per side; modeled adverse slippage is 0.10% per side.",
            "Sparse signals, hindsight-selected continuous historical window and "
            "discretionary strategies are not evidence of forward profitability.",
        ],
    }


def diagnose(data):
    start, end, _ = validate(data)
    count = (end - start) // FOUR_HOURS
    split = start + (count * 3 // 5) * FOUR_HOURS
    if split - start < DAY or end - split < DAY:
        raise ValueError("Insufficient independent comparison windows")
    variants = {variant.name: replay(data, variant) for variant in VARIANTS}
    for name in ("PUBLIC_NY_FVG", "CRYPTO_24H_FVG"):
        variant = VARIANT_BY_NAME[name]
        variants[name]["earlier_research"] = replay(data, variant,
                                                     start_ms=start, end_ms=split)
        variants[name]["later_chronological_holdout"] = replay(data, variant,
                                                               start_ms=split, end_ms=end)
    benchmark = compare_existing(data)
    return {
        "mode": "TJR_PUBLIC_CONCEPTS_MATCHED_CRYPTO_BACKTEST",
        "source": data["source"],
        "period": {"start": stamp(start), "end_exclusive": stamp(end),
                   "days": (end - start) / DAY},
        "split": {"earlier_end_exclusive": stamp(split),
                  "later_start": stamp(split),
                  "previous_bars_used_as_closed_warmup_only": True,
                  "accounts_restart_with_500_usd_at_split": True},
        "coverage": data["coverage"],
        "variants": variants,
        "existing_controls": {
            "V1": {k: v for k, v in benchmark["V1_control"].items()
                   if k in ("paper_entries", "closed_trades", "win_rate_pct",
                            "net_realized_pnl_usd", "total_return_pct",
                            "max_drawdown_pct", "closed_trade_fees_usd")},
            "V2A": {k: v for k, v in benchmark["V2A_candle_only"].items()
                    if k in ("paper_entries", "closed_trades", "win_rate_pct",
                             "net_realized_pnl_usd", "total_return_pct",
                             "max_drawdown_pct", "closed_trade_fees_usd")},
        },
        "cautions": [
            "Reproduces only TJR/ICT public educational CONCEPTS, not private "
            "TJR strategies, indicators, order flow, or exact discretionary trades.",
            "NY mode uses 9:30–16:00 America/New_York 5m candle-close clock; "
            "spot crypto uses a different 24/7 volatility regime.",
            "Manual 5m OHLCV cannot resolve path ordering, real fills, "
            "short financing costs or historical order-book depth.",
            "Six exploratory variants are not prevalidated and MUST NOT be "
            "ranked on one sample then claimed to have out-of-sample edge.",
            "V1 and V2A control execution models differ from TJR modeled "
            "resting limit orders, so matching calendar dates is not "
            "equivalent to fully standardized fills.",
            "Long-only spot and theoretical-short P&L separated in individual "
            "trade records, both do not represent a verified live short strategy.",
            "No orders, Cloudflare/worker, Telegram, Turso, paper state or schedules changed."
        ]
    }


def report(results):
    def n(v):
        return "N/A" if v is None else f"{v:.2f}"
    lines = [
        "# PulseCrypto — TJR-public-concept research vs crypto adaptation",
        "",
        "**RESEARCH ONLY — NOT THE REAL TJR ALGORITHM; NO REAL OR PAPER ORDERS.**",
        "",
        f'**Market window:** {results["period"]["start"]} → '
        f'{results["period"]["end_exclusive"]} '
        f'({results["period"]["days"]:.2f} days from verified 5m bars)',
        "",
        "## Frozen variant comparison on same BTC/ETH/SOL markets",
        "",
        "| Variant | Entries | Closed | Win rate | Net P/L ($) | Return | Max DD | Fees ($) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, data in results["variants"].items():
        lines.append(f'| {key} | {data["entries"]} | {data["closed_trades"]} '
                     f'| {n(data["win_rate_pct"])}% | {data["net_realized_pnl_usd"]:+.2f} '
                     f'| {data["total_return_pct"]:+.2f}% | {data["max_drawdown_pct"]:.2f}% '
                     f'| {data["closed_trade_fees_usd"]:.2f} |')
    lines += [
        "", "## Existing V1 and V2A period-matched controls", "",
        "| Control | Entries | Closed | Win rate | Net P/L ($) | Return | Drawdown |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, d in results["existing_controls"].items():
        lines.append(f'| {key} | {d["paper_entries"]} | {d["closed_trades"]} '
                     f'| {n(d["win_rate_pct"])}% | {d["net_realized_pnl_usd"]:+.2f} '
                     f'| {d["total_return_pct"]:+.2f}% | {d["max_drawdown_pct"]:.2f}% |')
    lines += [
        "", "## Predeclared earlier/later chronological splits",
        "",
        "| Variant | Window | Entries | Closed | Net P/L ($) | Return |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name in ("PUBLIC_NY_FVG", "CRYPTO_24H_FVG"):
        for key in ("earlier_research", "later_chronological_holdout"):
            d = results["variants"][name][key]
            lines.append(f'| {name} | {key} | {d["entries"]} '
                         f'| {d["closed_trades"]} '
                         f'| {d["net_realized_pnl_usd"]:+.2f} '
                         f'| {d["total_return_pct"]:+.2f}% |')
    lines += ["", "## Candidate reasons by variant", ""]
    for name, d in results["variants"].items():
        counts = sorted(d["decisions"].items(), key=lambda x: -x[1])[:10]
        lines.append("**" + name + "**: " + ", ".join(
            f"{label}={count}" for label, count in counts))
        lines.append("")
    lines += [
        "", "## Caveats and reproducibility", "",
    ]
    lines += ["- " + caution for caution in results["cautions"]]
    lines += [
        "", "Full simulated trade records, side, target source, cost, stop and "
        "zone are retained in the accompanying JSON. This report is not "
        "an endorsement or signal product.",
    ]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description="TJR public concept crypto research only")
    p.add_argument("--data", required=True)
    p.add_argument("--json", required=True)
    p.add_argument("--markdown", required=True)
    args = p.parse_args()
    d = json.loads(Path(args.data).read_text(encoding="utf-8"))
    results = diagnose(d)
    for output in (args.json, args.markdown):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(results, indent=2, allow_nan=False) + "\n",
                               encoding="utf-8")
    Path(args.markdown).write_text(report(results), encoding="utf-8")
    print("TJR public-method + crypto adaptation comparison finished (RESEARCH ONLY)")


if __name__ == "__main__":
    main()
