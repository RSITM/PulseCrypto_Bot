"""Append public V2-B forward observations to a separate GitHub research branch.

Designed for a worktree on v2b-observations, never the source/main branch.
Keeps a current-branch 30-day rolling NDJSON archive and transparent summary.
No secrets, exchange orders, paper account changes or network calls.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from statistics import mean

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
RETENTION_DAYS = 30
MAX_SNAPSHOT_BYTES = 200_000
MAX_JSONL_RECORDS_PER_DAY = 600
FIVE = 300_000


def date_from_ms(milliseconds):
    if type(milliseconds) is not int or milliseconds <= 0:
        raise ValueError("Bad observation timestamp")
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).date()


def validate_observation(row):
    if not isinstance(row, dict):
        raise ValueError("Snapshot must be a JSON object")
    if row.get("schema") != "pulsecrypto-v2b-forward-observation-v1":
        raise ValueError("Unexpected V2-B observation schema")
    if row.get("mode") != "RESEARCH_SHADOW_NO_ORDERS":
        raise ValueError("Refusing non-research snapshot")
    when = row.get("started_at_ms")
    ended = row.get("finished_at_ms")
    if (type(when) is not int or type(ended) is not int
            or when <= 0 or ended < when or ended - when > 10 * 60_000):
        raise ValueError("Bad V2-B start/end timestamps")
    if type(row.get("signal_closed_at_ms")) is not int:
        raise ValueError("Invalid 5m signal close")
    if when // 300_000 * 300_000 != row["signal_closed_at_ms"]:
        raise ValueError("Signal timestamp disagrees with collected observation")
    if not isinstance(row.get("symbols"), dict) or set(row["symbols"]) != set(SYMBOLS):
        raise ValueError("Missing market in research observation")
    for sym, data in row["symbols"].items():
        if not isinstance(data, dict) or data.get("symbol") != sym:
            raise ValueError("Mismatched symbol in observation")
        if data.get("full_v2") is not None and data.get("observation_status") != "ON_TIME_SHADOW_RESEARCH":
            raise ValueError("Delayed observations must never have execution candidates")
    return when


def read_day(path):
    if not path.exists():
        return []
    snapshots = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            validate_observation(data)
            snapshots.append(data)
    if len(snapshots) > MAX_JSONL_RECORDS_PER_DAY:
        raise ValueError("Daily observation archive exceeds safety cap")
    return snapshots


def summarize(records):
    totals = {sym: Counter() for sym in SYMBOLS}
    spreads = {sym: [] for sym in SYMBOLS}
    for record in records:
        for sym, obs in record["symbols"].items():
            x = totals[sym]
            x["observations"] += 1
            if obs.get("candles_status") == "verified_contiguous_closed":
                x["verified_candles"] += 1
            if obs.get("observation_status") == "ON_TIME_SHADOW_RESEARCH":
                x["on_time"] += 1
                book = obs.get("order_book") or {}
                value = book.get("spread_bps")
                if type(value) in (int, float) and value >= 0:
                    spreads[sym].append(value)
            elif obs.get("observation_status") == "DELAYED_NOT_AN_EXECUTION_TIME_SIGNAL":
                x["delayed"] += 1
            elif obs.get("observation_status") == "DEPTH_UNAVAILABLE":
                x["depth_unavailable"] += 1
            else:
                x["other_unavailable"] += 1
            if (obs.get("price_only") or {}).get("action") == "CANDIDATE_PRICE_ONLY":
                x["price_candidates"] += 1
            if (obs.get("full_v2") or {}).get("action") == "CANDIDATE":
                x["depth_gated_candidates"] += 1
            if (obs.get("order_book") or {}).get("paper_liquidity_pass") is True:
                x["book_depth_pass"] += 1
    return {sym: {
        **dict(totals[sym]),
        "mean_on_time_spread_bps": round(mean(spreads[sym]), 4)
        if spreads[sym] else None,
    } for sym in SYMBOLS}


def observation_coverage(rows):
    """Coverage of distinct closed five-minute UTC slots in the archive.

    Missing market observations are NOT reconstructed from later prices.
    """
    if not rows:
        return {
            "expected_five_minute_slots": 0,
            "observed_five_minute_slots": 0,
            "missing_five_minute_slots": 0,
            "observed_pct": None,
        }
    closes = {row["signal_closed_at_ms"] for row in rows}
    expected = (max(closes) - min(closes)) // FIVE + 1
    observed = len(closes)
    return {
        "expected_five_minute_slots": expected,
        "observed_five_minute_slots": observed,
        "missing_five_minute_slots": expected - observed,
        "observed_pct": round(100 * observed / expected, 2),
    }


def write_report(directory, rows):
    stats = summarize(rows)
    coverage = observation_coverage(rows)
    first = rows[0]["started_at_utc"] if rows else "N/A"
    last = rows[-1]["started_at_utc"] if rows else "N/A"
    lines = [
        "# PulseCrypto V2-B: public book and order-flow forward observations",
        "",
        "**Research-only public exchange market data; zero orders, no portfolio writes.**",
        "",
        f"Snapshots retained on branch: {len(rows)}",
        f"First observation: {first}",
        f"Latest observation: {last}",
        f"5-minute slots captured: {coverage['observed_five_minute_slots']} "
        f"of {coverage['expected_five_minute_slots']} expected "
        f"({coverage['observed_pct']}% coverage); "
        f"missing: {coverage['missing_five_minute_slots']}",
        "",
        "| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for sym, data in stats.items():
        spread = data["mean_on_time_spread_bps"]
        lines.append(
            f"| {sym} | {data.get('observations', 0)} | {data.get('on_time', 0)} "
            f"| {data.get('delayed', 0)} | {data.get('verified_candles', 0)} "
            f"| {data.get('depth_unavailable', 0)} "
            f"| {data.get('price_candidates', 0)} "
            f"| {data.get('depth_gated_candidates', 0)} "
            f"| {spread if spread is not None else 'N/A'} |"
        )
    lines += [
        "", "Order-book metrics are sampled *only when GitHub runs*; "
        "resting depth can be spoofed or canceled and is not a guaranteed fill.",
        "The public last-200-trades REST endpoint is a partial recent sample, "
        "not historical tick coverage or verified continuous order flow.",
        "Neither candidates nor observed spread imply a profitable forward strategy.",
        "Scheduled GitHub Actions jobs may run late or be skipped. "
        "Delayed data is never backdated to a completed 5m candle.",
        "Retention deletes old files from the current branch tip, but Git commit "
        "history may still retain earlier snapshots.",
    ]
    (directory / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "format_version": 1, "retention_days": RETENTION_DAYS,
        "first_observation": first, "last_observation": last,
        "samples": len(rows), "by_symbol": stats,
        "observation_coverage": coverage,
        "note": "No trading; public Binance.US forward observations only"
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n",
        encoding="utf-8"
    )
    return manifest


def append_snapshot(snapshot, directory):
    if snapshot.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise ValueError("Oversized public market-data research observation")
    observation = json.loads(snapshot.read_text(encoding="utf-8"))
    started = validate_observation(observation)
    day = date_from_ms(started)
    directory.mkdir(parents=True, exist_ok=True)
    daily_dir = directory / "data"
    daily_dir.mkdir(parents=True, exist_ok=True)
    filename = daily_dir / f"{day.isoformat()}.jsonl"

    existing = read_day(filename)
    # GitHub schedule and external workflow_dispatch can observe the same
    # CLOSED 5m candle. Keep the earliest capture for each time slot.
    # Different-start-time runs never inflate trade-candidate counts.
    candle_close = observation["signal_closed_at_ms"]
    match = next((i for i, old in enumerate(existing)
                  if old["signal_closed_at_ms"] == candle_close), None)
    changed = False
    if match is None:
        if len(existing) >= MAX_JSONL_RECORDS_PER_DAY:
            raise ValueError("Too many same-day runs; refusing unbounded archive")
        existing.append(observation)
        changed = True
    elif started < existing[match]["started_at_ms"]:
        existing[match] = observation
        changed = True
    if changed:
        existing.sort(key=lambda row: row["started_at_ms"])
        filename.write_text(
            "".join(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n"
                    for row in existing), encoding="utf-8"
        )

    threshold = day - timedelta(days=RETENTION_DAYS - 1)
    rows = []
    for path in sorted(daily_dir.glob("????-??-??.jsonl")):
        try:
            file_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
        except ValueError as err:
            raise ValueError("Malformed date partition in public research archive") from err
        if file_date < threshold:
            path.unlink()
            continue
        if file_date > day:
            raise ValueError("Future partition in research archive")
        rows.extend(read_day(path))
    rows.sort(key=lambda row: row["started_at_ms"])
    return write_report(directory, rows)


def main():
    parser = argparse.ArgumentParser(description="Isolated V2-B research-branch archive")
    parser.add_argument("append", choices=("append",))
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    manifest = append_snapshot(Path(args.snapshot), Path(args.directory))
    print(f"V2-B observation branch: {manifest['samples']} retained snapshots; "
          "no trading orders or account writes")


if __name__ == "__main__":
    main()
