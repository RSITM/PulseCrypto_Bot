"""Offline, read-only historical replay of PulseCrypto's production signal and paper ledger.

No broker, Telegram, network access, state changes, or strategy modifications.
"""
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
import argparse
import json
import math
from pathlib import Path

from intelligence import SYMBOLS
from paper_trading import PaperAccount
from signal_engine import evaluate

M15 = 900_000
H1 = 3_600_000
DAY = 86_400_000


def utc(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def verify_bars(rows, interval, symbol):
    step = M15 if interval == "15m" else H1
    if not isinstance(rows, list) or len(rows) < 250:
        raise ValueError(f"{symbol}: insufficient {interval} historical candles")
    previous = None
    for bar in rows:
        if not isinstance(bar, dict) or set(bar) != {"time", "close", "high", "low", "volume"}:
            raise ValueError(f"{symbol}: bad candle format")
        t = bar["time"]
        if type(t) is not int or t < 0 or t % step:
            raise ValueError(f"{symbol}: invalid candle time")
        values = [bar[k] for k in ("close", "high", "low", "volume")]
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError(f"{symbol}: non-finite candle")
        if bar["low"] <= 0 or not bar["low"] <= bar["close"] <= bar["high"] or bar["volume"] < 0:
            raise ValueError(f"{symbol}: invalid candle range")
        if previous is not None and t - previous != step:
            raise ValueError(f"{symbol}: missing or out-of-order {interval} bar")
        previous = t


def valid_levels(signal, slip):
    """Defend the research replay from the known live ledger stop/target condition bug."""
    values = [signal.entry, signal.stop, signal.target]
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
        return False
    return 0 < signal.stop < signal.entry and signal.entry * (1 + slip) < signal.target


def replay(data, evaluator=evaluate):
    if not isinstance(data, dict) or data.get("format_version") != 1:
        raise ValueError("Unsupported snapshot format")
    if data.get("source") != "Binance.US public spot klines":
        raise ValueError("Unexpected historical data source")
    start, end = data.get("analysis_start_ms"), data.get("analysis_end_ms")
    if (type(start) is not int or type(end) is not int or start < 1
            or start % M15 or end % M15 or end <= start or end - start > 90 * DAY):
        raise ValueError("Invalid backtest date range")
    markets = data.get("symbols")
    if not isinstance(markets, dict) or set(markets) != set(SYMBOLS):
        raise ValueError("Expected BTC, ETH and SOL market histories")

    bars15, bars1h, times15, times1h = {}, {}, {}, {}
    for sym in SYMBOLS:
        market = markets[sym]
        if not isinstance(market, dict) or set(market) != {"15m", "1h"}:
            raise ValueError(f"{sym}: both historical intervals required")
        bars15[sym], bars1h[sym] = market["15m"], market["1h"]
        verify_bars(bars15[sym], "15m", sym)
        verify_bars(bars1h[sym], "1h", sym)
        times15[sym] = [b["time"] for b in bars15[sym]]
        times1h[sym] = [b["time"] for b in bars1h[sym]]
        if times15[sym][0] > start - 250 * M15 or times15[sym][-1] < end - M15:
            raise ValueError(f"{sym}: 15m coverage/warmup incomplete")
        if times1h[sym][0] > start - 252 * H1 or times1h[sym][-1] < end - H1:
            raise ValueError(f"{sym}: 1h coverage/warmup incomplete")

    account = PaperAccount()
    decisions = Counter()
    by_symbol = {sym: Counter() for sym in SYMBOLS}
    first_entry, entries = None, 0
    peak, drawdown, equity = account.starting_equity, 0, account.starting_equity
    equity_daily = []

    for current in range(start, end, M15):
        latest, windows = {}, {}
        for sym in SYMBOLS:
            cutoff = bisect_right(times15[sym], current)
            visible = bars15[sym][max(0, cutoff - 250):cutoff]
            if len(visible) < 205 or visible[-1]["time"] != current:
                raise ValueError(f"{sym}: missing 15m bar at {utc(current)}")
            latest[sym], windows[sym] = visible[-1], visible
        day = datetime.fromtimestamp(current / 1000, timezone.utc).date().isoformat()
        account.roll_day(day, {sym: latest[sym]["close"] for sym in account.positions}
                         if account.positions else None)

        exited = set()
        for sym in SYMBOLS:
            if sym in account.positions:
                bar = latest[sym]
                if account.on_candle(sym, bar["low"], bar["high"]) == "PAPER_SELL":
                    exited.add(sym)

        for sym in SYMBOLS:
            if sym in account.positions:
                reason = "OPEN_POSITION"
            elif sym in exited:
                reason = "EXITED_THIS_CYCLE"
            else:
                # 1h closing time must be <= current 15m closing time.
                k = bisect_right(times1h[sym], current + M15 - H1)
                history1h = bars1h[sym][max(0, k - 250):k]
                signal = evaluator(windows[sym], history1h if len(history1h) >= 205 else None)
                reason = signal.action + ": " + signal.reason
                if signal.action == "BUY":
                    if not valid_levels(signal, account.slippage_rate):
                        reason = "ENTRY_BLOCKED: invalid entry/stop/target"
                    else:
                        outcome = account.open_long(sym, signal.entry, signal.stop, signal.target)
                        if outcome == "PAPER_BUY":
                            entries += 1
                            if first_entry is None:
                                first_entry = utc(current)
                            reason = "PAPER_BUY"
                        else:
                            reason = "ENTRY_BLOCKED: " + outcome
            decisions[reason] += 1
            by_symbol[sym][reason] += 1

        equity = account.equity({sym: latest[sym]["close"] for sym in account.positions})
        peak = max(peak, equity)
        drawdown = max(drawdown, 100 * (peak - equity) / peak)
        if (current - start) % DAY == 0 or current == end - M15:
            equity_daily.append({"utc": utc(current), "equity": round(equity, 4)})

    trades = account.trades
    wins = [t["net_pnl"] for t in trades if t["net_pnl"] > 0]
    losses = [t["net_pnl"] for t in trades if t["net_pnl"] < 0]
    result = {
        "mode": "RESEARCH_ONLY_NO_LIVE_CHANGES",
        "source": data["source"],
        "period": {"start": utc(start), "end_exclusive": utc(end),
                   "days": (end - start) / DAY},
        "markets": list(SYMBOLS),
        "assumed_fee_per_side_pct": account.fee_rate * 100,
        "assumed_slippage_per_side_pct": account.slippage_rate * 100,
        "paper_entries": entries,
        "closed_trades": len(trades),
        "positions_still_open": len(account.positions),
        "wins": len(wins), "losses": len(losses),
        "win_rate_pct": (100 * len(wins) / len(trades) if trades else None),
        "profit_factor": (sum(wins) / -sum(losses) if losses else None),
        "realized_net_pnl_usd": round(sum(t["net_pnl"] for t in trades), 4),
        "closed_trade_fees_usd": round(sum(t["entry_fee"] + t["exit_fee"] for t in trades), 4),
        "ending_equity_usd": round(equity, 4),
        "ending_cash_usd": round(account.cash, 4),
        "total_equity_return_pct": round((equity / account.starting_equity - 1) * 100, 4),
        "max_marked_equity_drawdown_pct": round(drawdown, 4),
        "first_entry": first_entry,
        "decisions": dict(decisions),
        "by_symbol": {sym: dict(counter) for sym, counter in by_symbol.items()},
        "equity_samples": equity_daily,
        "caveats": [
            "Trades use historical CLOSED candle prices with simulated adverse slippage.",
            "A buy is simulated at the signal bar close; real next-bar entry may be worse.",
            "On any bar hitting both stop and target, the stop is selected first.",
            "Fees/slippage are placeholders, not verified exchange quotes.",
            "Historical simulated results do not prove future profitability.",
            "The production PaperAccount has a known incorrect and/or invalid-level condition; this separate replay protects against it.",
            "No production account or strategy parameter was modified."
        ]
    }
    return result


def report_markdown(r):
    percent = "N/A" if r["win_rate_pct"] is None else f'{r["win_rate_pct"]:.1f}%'
    factor = "N/A" if r["profit_factor"] is None else f'{r["profit_factor"]:.2f}'
    lines = [
        "# PulseCrypto — Offline Historical Strategy Audit",
        "",
        "> Historical research only. The running 15-minute paper bot is NOT modified.",
        "",
        f'**Period:** {r["period"]["start"]} to {r["period"]["end_exclusive"]} (exclusive; {r["period"]["days"]:.0f} days)',
        f'**Market:** {r["source"]} — BTC, ETH and SOL, 15m closes + confirmed 1h trend',
        f'**Costs per side:** fee {r["assumed_fee_per_side_pct"]:.2f}%, adverse slippage {r["assumed_slippage_per_side_pct"]:.2f}%',
        "",
        "| Metric | Backtest |", "|---|---:|",
        f'| Entries | {r["paper_entries"]} |',
        f'| Closed trades | {r["closed_trades"]} |',
        f'| Open positions at end | {r["positions_still_open"]} |',
        f'| Wins / losses | {r["wins"]} / {r["losses"]} |',
        f'| Closed-trade win rate | {percent} |',
        f'| Profit factor | {factor} |',
        f'| Realized net P/L | USD {r["realized_net_pnl_usd"]:+.2f} |',
        f'| Fees on closed trades | USD {r["closed_trade_fees_usd"]:.2f} |',
        f'| Final marked equity | USD {r["ending_equity_usd"]:.2f} |',
        f'| Marked account return | {r["total_equity_return_pct"]:+.2f}% |',
        f'| Max marked equity drawdown | {r["max_marked_equity_drawdown_pct"]:.2f}% |',
        "", "## Entry decision counts", ""
    ]
    lines += ["- " + reason + ": **" + str(n) + "**" for reason, n in
              sorted(r["decisions"].items(), key=lambda kv: -kv[1])]
    lines += ["", "## Important limitations", ""]
    lines += ["- " + item for item in r["caveats"]]
    if not r["closed_trades"]:
        lines += ["", "**No closed trades: profitability cannot be evaluated.**"]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description="Purely offline historical candle replay")
    p.add_argument("--data", required=True)
    p.add_argument("--markdown", required=True)
    p.add_argument("--json", required=True)
    args = p.parse_args()
    result = replay(json.loads(Path(args.data).read_text(encoding="utf-8")))
    for output in (args.markdown, args.json):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.markdown).write_text(report_markdown(result), encoding="utf-8")
    Path(args.json).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("RESEARCH ONLY: {} entries, {} closed, net USD {:+.2f}".format(
        result["paper_entries"], result["closed_trades"], result["realized_net_pnl_usd"]))


if __name__ == "__main__":
    main()
