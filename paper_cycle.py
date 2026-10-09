"""Manual GitHub Actions paper cycle and notification formatter.

Run step writes the ledger locally; GitHub workflow commits it before notify.
No brokerage integrations or real-money trades.
"""
import argparse
import json
from pathlib import Path
from paper_runner import run

def format_event(event):
    symbol = event["symbol"].replace("USDT", "")
    if event["action"] == "PAPER_BUY":
        return ("🧪 PulseCrypto PAPER BUY — " + symbol
                + "\nEntry: " + f'{event["entry"]:.4f}'
                + "\nStop: " + f'{event["stop"]:.4f}'
                + "\nTarget: " + f'{event["target"]:.4f}'
                + "\nSIMULATION ONLY — no real order")
    if event["action"] == "PAPER_SELL":
        trade = event["trade"]
        return ("🧪 PulseCrypto PAPER SELL — " + symbol
                + "\nExit: " + f'{trade["exit"]:.4f}'
                + "\nNet P/L: $" + f'{trade["net_pnl"]:.2f}'
                + "\nReason: " + str(trade["reason"])
                + "\nSIMULATION ONLY — no real order")
    raise ValueError("Unknown paper event")

def run_cycle(state_file, event_file):
    _, events = run(state_file)
    Path(event_file).write_text(json.dumps(events, allow_nan=False), encoding="utf-8")
    print(f"Prepared {len(events)} paper notification(s)")

def notify(event_file):
    from main import send_alert
    events = json.loads(Path(event_file).read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise ValueError("Invalid notifications")
    for event in events:
        send_alert(format_event(event))
    print(f"Sent {len(events)} paper notification(s)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "notify"))
    parser.add_argument("--state", default="paper_state/runner.json")
    parser.add_argument("--events", default="paper_events.json")
    args = parser.parse_args()
    if args.command == "run":
        run_cycle(args.state, args.events)
    else:
        notify(args.events)
