"""Offline-testable paper strategy runner. No real exchange order capability.

The runner uses a single versioned JSON snapshot holding both account and candle
cursors; callers must preserve that file between invocations.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile

from candle_feed import fetch_closed, INTERVAL_MS
from intelligence import SYMBOLS
from paper_state import serialize, deserialize
from paper_trading import PaperAccount
from signal_engine import evaluate

RUNNER_VERSION = 1

@dataclass
class RunnerState:
    account: PaperAccount
    cursors: dict

def load_runner_state(path):
    path = Path(path)
    if not path.exists():
        return RunnerState(PaperAccount(), {})
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("runner_version") != RUNNER_VERSION:
        raise ValueError("Unknown runner state version")
    cursors = data.get("cursors")
    if not isinstance(cursors, dict) or any(
        key not in SYMBOLS or type(value) is not int or value < 0
        for key, value in cursors.items()
    ):
        raise ValueError("Invalid candle cursors")
    account = deserialize(json.dumps(data["ledger"]))
    return RunnerState(account, cursors)

def save_runner_state(state, path):
    path = Path(path)
    if not isinstance(state.cursors, dict) or any(
        key not in SYMBOLS or type(value) is not int or value < 0
        for key, value in state.cursors.items()
    ):
        raise ValueError("Invalid candle cursors")
    payload = json.dumps({"runner_version": RUNNER_VERSION,
                          "ledger": json.loads(serialize(state.account)),
                          "cursors": state.cursors}, allow_nan=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".runner-", delete=False) as stream:
            temp = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)

def step(state, candles_by_symbol, hourly_by_symbol, day, diagnostics=None):
    """Consume fully validated closed bars; mutate state only after validation.

    First observation may generate an entry but not an exit; exits use later bars.
    Refuses missing history when there are open positions, rather than
    silently skipping possible stops.
    """
    symbols = tuple(SYMBOLS)
    if set(candles_by_symbol) != set(symbols) or set(hourly_by_symbol) != set(symbols):
        raise ValueError("All symbols required")
    for sym in symbols:
        series, hour = candles_by_symbol[sym], hourly_by_symbol[sym]
        if len(series) < 205 or len(hour) < 205:
            raise ValueError("Insufficient history")
        for bars, interval in ((series, "15m"), (hour, "1h")):
            times = [b["time"] for b in bars]
            if any(type(t) is not int for t in times):
                raise ValueError("Missing candle timestamp")
            if any(b - a != INTERVAL_MS[interval] for a, b in zip(times, times[1:])):
                raise ValueError("Gapped or unordered candles")
        if hour[-1]["time"] + INTERVAL_MS["1h"] > series[-1]["time"] + INTERVAL_MS["15m"]:
            raise ValueError("Hourly candle is ahead of 15m close")
        cursor = state.cursors.get(sym)
        if cursor is not None and cursor > series[-1]["time"]:
            raise ValueError("Candle time went backwards")
        if cursor is not None and cursor < series[0]["time"] - INTERVAL_MS["15m"]:
            raise ValueError("Missing earlier bars: refusing to skip potential exits")
    # Copies keep partial failure from writing half-processed account.
    from paper_state import deserialize, serialize
    account = deserialize(serialize(state.account))
    cursors = dict(state.cursors)
    marks = {sym: candles_by_symbol[sym][-1]["close"] for sym in account.positions}
    account.roll_day(day, marks=marks if account.positions else None)
    events = []
    # Iterate stops on all unseen closed bars before evaluating fresh entries.
    for sym in symbols:
        series = candles_by_symbol[sym]
        cursor = cursors.get(sym)
        unseen = [b for b in series if cursor is not None and b["time"] > cursor]
        if sym in account.positions:
            for bar in unseen:
                result = account.on_candle(sym, bar["low"], bar["high"])
                if result == "PAPER_SELL":
                    events.append({"symbol": sym, "action": result,
                                   "trade": dict(account.trades[-1]), "time": bar["time"]})
                    break
    for sym in symbols:
        series = candles_by_symbol[sym]
        latest = series[-1]
        cursor = cursors.get(sym)
        if cursor is None or latest["time"] > cursor:
            exited = any(e["symbol"] == sym for e in events)
            # Diagnostic outcomes mirror the existing entry eligibility checks.
            # They never change whether evaluate() or open_long() gets called.
            if (sym not in account.positions
                and not exited
                and (cursor is None or latest["time"] - cursor == INTERVAL_MS["15m"])):
                hour = hourly_by_symbol[sym]
                eligible = [b for b in hour if b["time"] + INTERVAL_MS["1h"] <= latest["time"] + INTERVAL_MS["15m"]]
                signal = evaluate(series, eligible if len(eligible) >= 205 else None)
                print(f"PAPER SIGNAL {sym}: {signal.action} — {signal.reason} (closed 15m candle {latest['time']})")
                outcome, reason = "WAIT", signal.reason
                if signal.action == "BUY":
                    result = account.open_long(sym, signal.entry, signal.stop, signal.target)
                    if result == "PAPER_BUY":
                        outcome, reason = "PAPER_BUY", signal.reason
                        events.append({"symbol": sym, "action": result,
                                       "entry": account.positions[sym].entry,
                                       "stop": signal.stop, "target": signal.target,
                                       "time": latest["time"]})
                    else:
                        outcome, reason = "ENTRY_BLOCKED", result
            elif sym in account.positions:
                outcome, reason = "OPEN_POSITION", "Position already open"
            elif exited:
                outcome, reason = "EXITED_THIS_CYCLE", "Same-candle reentry disabled"
            else:
                outcome, reason = "MISSED_CANDLES", "More than one new 15m candle; entry skipped"
            if diagnostics is not None:
                diagnostics.append({"symbol": sym, "candle_ms": latest["time"],
                                    "outcome": outcome, "reason": reason})
            cursors[sym] = latest["time"]
    return RunnerState(account, cursors), events

def run(path="paper_state/runner.json", observations_path=None):
    """One manual, read-only market observation; saves locally, prints events."""
    # Fetch all series before changing saved state.
    data = {sym: fetch_closed(sym, "15m") for sym in SYMBOLS}
    hourly = {sym: fetch_closed(sym, "1h") for sym in SYMBOLS}
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).date().isoformat()
    observations = []
    new_state, events = step(load_runner_state(path), data, hourly, now, diagnostics=observations)
    save_runner_state(new_state, path)
    if observations_path is not None:
        try:
            Path(observations_path).write_text(json.dumps(observations, allow_nan=False), encoding="utf-8")
        except OSError:
            print("Warning: unable to write optional signal diagnostics; paper ledger was saved")
    print(json.dumps({"mode": "PAPER_ONLY", "events": events,
                      "cash": round(new_state.account.cash, 4),
                      "open_positions": list(new_state.account.positions),
                      "completed_trades": len(new_state.account.trades)}, indent=2))
    return new_state, events

if __name__ == "__main__":
    run()
