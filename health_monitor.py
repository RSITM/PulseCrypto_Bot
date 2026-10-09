"""Independent, read-only PulseCrypto health checks and Telegram transition alerts.

Scheduled from an external cron-job.org workflow_dispatch. Never submits trades.
The dedicated health-state branch stores alert status, not account balances.
"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

import requests

REPO = "RSITM/PulseCrypto_Bot"
API = f"https://api.github.com/repos/{REPO}"
WORKFLOWS = (
    ("TRADING", "paper-forward.yml", 40),
    ("BACKUP", "turso-backup-test.yml", 45),
)
INTERVAL_MS = 900_000
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
MAX_CANDLE_LAG = timedelta(minutes=45)
STATE_VERSION = 1

DESCRIPTIONS = {
    "TRADING_OVERDUE": "Paper trading has not completed successfully within 40 minutes",
    "TRADING_FAILED": "Latest completed paper-trading workflow failed",
    "TRADING_UNAVAILABLE": "Could not check paper-trading workflow status",
    "BACKUP_OVERDUE": "Turso backup has not completed successfully within 45 minutes",
    "BACKUP_FAILED": "Latest completed Turso backup workflow failed",
    "BACKUP_UNAVAILABLE": "Could not check Turso backup workflow status",
    "CANDLES_STALE": "At least one BTC/ETH/SOL 15-minute candle is stale or missing",
    "LEDGER_UNAVAILABLE": "Could not read or validate saved paper-trading candle checkpoints",
}


def parse_time(text):
    if not isinstance(text, str):
        raise ValueError("Missing workflow timestamp")
    result = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Workflow timestamp lacks timezone")
    return result.astimezone(timezone.utc)


def workflow_issues(prefix, runs, now, max_age_minutes):
    """Require a recently successful completed run; flag latest failed run."""
    if not isinstance(runs, list):
        raise ValueError("Invalid workflow run list")
    finished = [r for r in runs if r.get("status") == "completed"]
    problems = set()
    if finished:
        # API returns recent runs, but sorting makes the logic deterministic.
        recent = max(finished, key=lambda r: parse_time(
            r.get("run_started_at") or r.get("created_at")))
        if recent.get("conclusion") not in ("success", "skipped", "neutral"):
            problems.add(prefix + "_FAILED")
    successes = [r for r in finished if r.get("conclusion") == "success"]
    if not successes:
        problems.add(prefix + "_OVERDUE")
    else:
        recent_success = max(parse_time(
            r.get("run_started_at") or r.get("created_at")) for r in successes)
        age = now - recent_success
        if age > timedelta(minutes=max_age_minutes) or age < -timedelta(minutes=5):
            problems.add(prefix + "_OVERDUE")
    return problems


def candle_issues(cursors, now):
    if not isinstance(cursors, dict):
        raise ValueError("Invalid candle cursors")
    for symbol in SYMBOLS:
        timestamp = cursors.get(symbol)
        if type(timestamp) is not int or timestamp < 0:
            return {"CANDLES_STALE"}
        # Candle timestamp identifies its open, not its close.
        closed = datetime.fromtimestamp(
            (timestamp + INTERVAL_MS) / 1000, tz=timezone.utc)
        lag = now - closed
        if lag > MAX_CANDLE_LAG or lag < -timedelta(minutes=16):
            return {"CANDLES_STALE"}
    return set()


def github_get(path, token):
    if not token:
        raise RuntimeError("GitHub Actions token is missing")
    try:
        response = requests.get(
            API + path,
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        # Do not print response bodies or request credentials into public CI logs.
        raise RuntimeError("GitHub health status request failed") from None


def fetch_workflow_runs(token, filename):
    data = github_get(
        f"/actions/workflows/{filename}/runs?branch=main&per_page=20", token)
    runs = data.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("Missing workflow runs")
    return runs


def fetch_cursors(token):
    data = github_get("/contents/runner.json?ref=paper-state", token)
    if data.get("encoding") != "base64" or not isinstance(data.get("content"), str):
        raise ValueError("Unexpected paper ledger response")
    content = base64.b64decode(data["content"], validate=False)
    ledger = json.loads(content)
    if ledger.get("runner_version") != 1 or ledger.get("ledger", {}).get("version") != 1:
        raise ValueError("Unexpected paper ledger version")
    return ledger.get("cursors")


def evaluate_live(token, now):
    issues = set()
    for prefix, filename, max_age in WORKFLOWS:
        try:
            runs = fetch_workflow_runs(token, filename)
            issues.update(workflow_issues(prefix, runs, now, max_age))
        except (RuntimeError, ValueError, KeyError, TypeError):
            issues.add(prefix + "_UNAVAILABLE")
    try:
        issues.update(candle_issues(fetch_cursors(token), now))
    except (RuntimeError, ValueError, KeyError, TypeError, OverflowError, OSError):
        issues.add("LEDGER_UNAVAILABLE")
    return issues


def load_state(path):
    path = Path(path)
    if not path.exists():
        return {"version": STATE_VERSION, "active": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or set(data) != {"version", "active"}
            or data["version"] != STATE_VERSION or not isinstance(data["active"], list)
            or len(set(map(str, data["active"]))) != len(data["active"])
            or any(code not in DESCRIPTIONS for code in data["active"])):
        raise ValueError("Invalid health monitor state")
    return data


def format_transition(new, recovered):
    lines = ["🚨 PulseCrypto Health Alert — PAPER TRADING ONLY"]
    if new:
        lines.append("")
        lines.append("Needs attention:")
        lines.extend("• " + DESCRIPTIONS[k] for k in sorted(new))
    if recovered:
        lines.append("")
        lines.append("Recovered:")
        lines.extend("✅ " + DESCRIPTIONS[k] for k in sorted(recovered))
    lines.append("")
    lines.append("No live orders are enabled. Check GitHub Actions and cron-job.org.")
    return "\n".join(lines)


def send_telegram(message, bot_token, chat_id):
    if not bot_token or not chat_id:
        raise RuntimeError("Telegram credentials missing")
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=15,
        )
        response.raise_for_status()
        if response.json().get("ok") is not True:
            raise RuntimeError("Telegram rejected health alert")
    except (requests.RequestException, ValueError):
        # Telegram API URL includes the token; never echo request exceptions.
        raise RuntimeError("Telegram health notification failed") from None


def run(state_path, *, dry_run=False, now=None, token=None,
        telegram_token=None, chat_id=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    token = token if token is not None else os.environ.get("GITHUB_TOKEN")
    telegram_token = telegram_token if telegram_token is not None else os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id if chat_id is not None else os.environ.get("TELEGRAM_CHAT_ID")
    current = evaluate_live(token, now)
    state = load_state(state_path)
    previous = set(state["active"])
    new = current - previous
    recovered = previous - current
    print("Health check complete (paper mode)")
    print("Current issues: " + (", ".join(sorted(current)) or "none"))
    print("New issues: " + (", ".join(sorted(new)) or "none"))
    print("Recovered: " + (", ".join(sorted(recovered)) or "none"))
    if dry_run:
        print("DRY RUN: no messages sent and no alert state updated")
        return
    if new or recovered:
        send_telegram(format_transition(new, recovered), telegram_token, chat_id)
        # Save only after Telegram confirms acceptance. If persistence fails,
        # retry on the next independent health cycle instead of losing the alert.
        Path(state_path).write_text(
            json.dumps({"version": STATE_VERSION, "active": sorted(current)}, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.state, dry_run=args.dry_run)
