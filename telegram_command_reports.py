"""Read-only PulseCrypto Telegram summaries from the saved paper ledger."""
import base64
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import json

from health_monitor import evaluate_live, github_get
from paper_report import last_candle, metrics
from paper_state import deserialize

MARKETS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def paper_file(token, filename):
    if filename not in ("runner.json", "signal_diagnostics.json"):
        raise ValueError("Unexpected saved file")
    result = github_get(f"/contents/{filename}?ref=paper-state", token)
    if not isinstance(result, dict) or result.get("encoding") != "base64":
        raise ValueError("Unexpected file encoding")
    try:
        return json.loads(base64.b64decode(result["content"]).decode("utf-8"))
    except (KeyError, TypeError, ValueError, UnicodeDecodeError):
        raise ValueError("Invalid saved paper file") from None


def snapshot(token):
    data = paper_file(token, "runner.json")
    if not isinstance(data, dict) or data.get("runner_version") != 1:
        raise ValueError("Unsupported paper runner version")
    account = asdict(deserialize(json.dumps(data["ledger"])))
    cursors = data.get("cursors")
    if not isinstance(cursors, dict) or any(
        name not in MARKETS or type(value) is not int or value < 0
        for name, value in cursors.items()
    ):
        raise ValueError("Invalid candle checkpoints")
    return account, cursors


def help_reply():
    return (
        "🤖 PulseCrypto — PAPER TRADING ONLY\n\n"
        "/status — scanner, backup and market-data health\n"
        "/performance — closed trades, win rate, realized P/L\n"
        "/signals — signal rejection reasons by coin\n"
        "/balance — simulated cash and open positions\n"
        "/trades — five latest closed paper trades\n"
        "/help — available read-only commands\n\n"
        "Responses arrive on the next scheduled check.\n"
        "No order placement or trading-settings commands."
    )


def performance_reply(account, cursors):
    m = metrics(account)
    rate = f"{m['win_rate']:.1f}%" if m["win_rate"] is not None else "N/A (no closed trades)"
    return (
        "📊 PulseCrypto PAPER PERFORMANCE\n"
        f"Trades: {m['trades']} | Wins: {m['wins']} | Losses: {m['losses']}\n"
        f"Win rate: {rate}\n"
        f"Realized net P/L: ${m['net']:+,.2f}\n"
        f"Closed-trade drawdown: {m['drawdown']:.2f}%\n"
        f"Available simulated cash: ${m['cash']:,.2f}\n"
        f"Open positions: {m['open']}\n"
        f"Last candle close: {last_candle(cursors)}\n"
        "Drawdown excludes unrealized losses; trading is simulated."
    )


def balance_reply(account, cursors):
    m = metrics(account)
    lines = [
        "💰 PulseCrypto SIMULATED ACCOUNT",
        f"Starting capital: ${m['start']:,.2f}",
        f"Available cash: ${m['cash']:,.2f}",
        f"Open positions: {m['open']}",
        f"Last candle close: {last_candle(cursors)}",
    ]
    if not m["open"]:
        lines.append(f"Total equity: ${m['cash']:,.2f} (no open positions)")
    else:
        lines.append("Total equity: unavailable without current prices")
        for symbol, pos in account["positions"].items():
            lines.append(f"• {symbol[:-4]}: entry ${pos['entry']:,.4f}")
    return "\n".join(lines)


def trades_reply(account):
    trades = account["trades"]
    if not trades:
        return "🧾 PulseCrypto PAPER TRADES\nNo completed trades yet."
    lines = ["🧾 PulseCrypto LAST 5 PAPER TRADES"]
    for t in reversed(trades[-5:]):
        lines.append(f"• {t['symbol'][:-4]}: ${t['net_pnl']:+,.2f} ({t['reason'][:30]})")
    lines.append("Trade-close timestamps are not stored in the ledger.")
    return "\n".join(lines)


def signals_reply(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Unsupported signal diagnostics")
    counts = data.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("Missing diagnostics")
    combined = Counter()
    lines = ["📡 PulseCrypto PAPER SIGNALS"]
    for symbol in MARKETS:
        group = counts.get(symbol)
        if not isinstance(group, dict):
            raise ValueError("Missing market diagnostics")
        for reason, count in group.items():
            if not isinstance(reason, str) or type(count) is not int or count < 0:
                raise ValueError("Invalid recorded diagnostics")
            combined[reason] += count
        lines.append(f"{symbol[:-4]}: {sum(group.values())} decisions")
    if combined:
        lines.append("Top decisions:")
        for reason, count in combined.most_common(5):
            lines.append(f"• {reason.replace(chr(10), ' ')[:110]}: {count}")
    else:
        lines.append("No observations yet.")
    lines.append("Decisions recorded since diagnostics were enabled.")
    return "\n".join(lines)


def status_reply(issues, cursors):
    labels = sorted(issues)
    trading = any(code.startswith("TRADING") for code in issues)
    backup = any(code.startswith("BACKUP") for code in issues)
    candles = any(code.startswith(("CANDLES", "LEDGER")) for code in issues)
    return (
        "🩺 PulseCrypto PAPER STATUS\n"
        f"Paper scanner: {'Needs attention' if trading else 'OK'}\n"
        f"Turso backup: {'Needs attention' if backup else 'OK'}\n"
        f"Candle feed: {'Needs attention' if candles else 'OK'}\n"
        f"Last processed candle: {last_candle(cursors)}\n"
        f"Reported issues: {', '.join(labels) if labels else 'None detected'}\n"
        "Based on saved candle timestamps and GitHub workflow results."
    )


def make_reply(command, github_token, now):
    if command in ("/start", "/help"):
        return help_reply()
    if command == "/status":
        issues = evaluate_live(github_token, now)
        try:
            _, cursors = snapshot(github_token)
        except (RuntimeError, ValueError, KeyError, TypeError, OverflowError):
            cursors = {}
            issues.add("LEDGER_UNAVAILABLE")
        return status_reply(issues, cursors)
    if command == "/signals":
        try:
            return signals_reply(paper_file(github_token, "signal_diagnostics.json"))
        except (RuntimeError, ValueError, KeyError, TypeError):
            return "📡 PulseCrypto signal diagnostics are not available yet."
    if command in ("/performance", "/balance", "/trades"):
        account, cursors = snapshot(github_token)
        if command == "/balance":
            return balance_reply(account, cursors)
        if command == "/trades":
            return trades_reply(account)
        return performance_reply(account, cursors)
    return "Unknown command. Send /help to see available commands."
