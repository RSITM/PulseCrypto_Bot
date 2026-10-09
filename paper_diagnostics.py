"""Bounded, read-only insights into decisions made by the paper signal engine.

Stored separately from runner.json so the simulated account schema and strategy
settings never change. Records one observation per symbol and new closed candle.
"""
from collections import Counter
import argparse
import json
import os
from pathlib import Path
import tempfile

from intelligence import SYMBOLS

VERSION = 1
MAX_RECENT = 180
OUTCOMES = frozenset({
    "WAIT", "PAPER_BUY", "ENTRY_BLOCKED", "OPEN_POSITION",
    "EXITED_THIS_CYCLE", "MISSED_CANDLES",
})


def empty_history():
    return {"version": VERSION, "counts": {sym: {} for sym in SYMBOLS},
            "recent": []}


def validate_observation(item):
    if not isinstance(item, dict) or set(item) != {"symbol", "candle_ms", "outcome", "reason"}:
        raise ValueError("Invalid diagnostic observation")
    if item["symbol"] not in SYMBOLS:
        raise ValueError("Unknown diagnostic symbol")
    if type(item["candle_ms"]) is not int or item["candle_ms"] < 0:
        raise ValueError("Invalid candle time")
    if item["outcome"] not in OUTCOMES:
        raise ValueError("Unknown diagnostic outcome")
    if not isinstance(item["reason"], str) or not 0 < len(item["reason"]) <= 180:
        raise ValueError("Invalid diagnostic reason")


def load_history(path):
    path = Path(path)
    if not path.exists():
        return empty_history()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"version", "counts", "recent"} or data["version"] != VERSION:
        raise ValueError("Unsupported diagnostics history")
    if not isinstance(data["counts"], dict) or set(data["counts"]) != set(SYMBOLS):
        raise ValueError("Invalid diagnostic counters")
    for group in data["counts"].values():
        if (not isinstance(group, dict) or any(
            not isinstance(key, str) or not isinstance(value, int) or isinstance(value, bool)
            or value < 0 for key, value in group.items()
        )):
            raise ValueError("Invalid diagnostic count")
    if not isinstance(data["recent"], list) or len(data["recent"]) > MAX_RECENT:
        raise ValueError("Invalid recent diagnostics")
    for item in data["recent"]:
        validate_observation(item)
    return data


def merge_history(history, observations):
    """Accumulate observations; recent IDs make repeat cycles idempotent."""
    data = json.loads(json.dumps(history))
    seen = {(x["symbol"], x["candle_ms"]) for x in data["recent"]}
    for item in observations:
        validate_observation(item)
        key = (item["symbol"], item["candle_ms"])
        if key in seen:
            continue
        seen.add(key)
        bucket = item["outcome"] + ": " + item["reason"]
        counts = data["counts"][item["symbol"]]
        counts[bucket] = counts.get(bucket, 0) + 1
        data["recent"].append(dict(item))
    data["recent"] = data["recent"][-MAX_RECENT:]
    return data


def append_observations(path, observations):
    path = Path(path)
    updated = merge_history(load_history(path), observations)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".signal-diagnostics-", suffix=".tmp", delete=False
        ) as stream:
            temporary = stream.name
            json.dump(updated, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return updated


def markdown_summary(history):
    lines = [
        "## PulseCrypto Signal Diagnostics",
        "",
        "Observations begin after instrumentation was enabled; earlier trading cycles are not included.",
        "One observation is counted for each new closed 15-minute candle and symbol.",
        "",
        "| Market | New candles | Evaluated signals | WAIT | Paper entries | Blocked buys | Skipped evaluations |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    total = 0
    all_reasons = Counter()
    for sym in SYMBOLS:
        reasons = history["counts"][sym]
        n = sum(reasons.values())
        total += n
        wait = sum(v for k, v in reasons.items() if k.startswith("WAIT: "))
        buy = sum(v for k, v in reasons.items() if k.startswith("PAPER_BUY: "))
        blocked = sum(v for k, v in reasons.items() if k.startswith("ENTRY_BLOCKED: "))
        evaluated = wait + buy + blocked
        skipped = n - evaluated
        lines.append(f"| {sym[:-4]} | {n} | {evaluated} | {wait} | {buy} | {blocked} | {skipped} |")
        for reason, count in reasons.items():
            all_reasons[(sym, reason)] += count
    lines += ["", "### Most common reasons", ""]
    if not total:
        lines.append("No observations yet. The next completed paper-trading cycle will begin collecting data.")
    else:
        lines += ["| Market | Decision and reason | Count |", "|---|---|---:|"]
        for (sym, reason), count in all_reasons.most_common(12):
            safe_reason = reason.replace("|", "/").replace("\n", " ")
            lines.append(f"| {sym[:-4]} | {safe_reason} | {count} |")
    lines += [
        "", "Diagnostics explain paper-trading entry decisions, not future returns.",
        "No settings are automatically changed using these statistics.", "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("report",))
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    print(markdown_summary(load_history(args.file)))
