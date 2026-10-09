"""Read-only performance report for simulated PulseCrypto trading."""
import argparse
from datetime import datetime, timedelta, timezone
from html import escape
import json
import math
from pathlib import Path

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Invalid numeric value in paper ledger")
    return float(value)


def read_snapshot(path):
    state = json.loads(Path(path).read_text(encoding="utf-8"))
    if state.get("runner_version") != 1 or state["ledger"]["version"] != 1:
        raise ValueError("Unsupported paper runner state")
    account = state["ledger"]["account"]
    if number(account["starting_equity"]) <= 0 or number(account["cash"]) < 0:
        raise ValueError("Invalid paper account balance")
    if not isinstance(account["trades"], list) or not isinstance(account["positions"], dict):
        raise ValueError("Invalid paper account")
    if any(sym not in SYMBOLS for sym in account["positions"]):
        raise ValueError("Invalid position symbol")
    for trade in account["trades"]:
        if not isinstance(trade, dict) or trade.get("symbol") not in SYMBOLS:
            raise ValueError("Invalid closed trade")
        for field in ("entry", "exit", "quantity", "net_pnl", "entry_fee", "exit_fee"):
            number(trade[field])
        if not isinstance(trade.get("reason"), str):
            raise ValueError("Invalid trade reason")
    cursors = state["cursors"]
    if not isinstance(cursors, dict) or any(
        sym not in SYMBOLS or type(timestamp) is not int or timestamp < 0
        for sym, timestamp in cursors.items()
    ):
        raise ValueError("Invalid last candle")
    return account, cursors


def metrics(account):
    trades = account["trades"]
    start = number(account["starting_equity"])
    pnls = [number(t["net_pnl"]) for t in trades]
    wins = sum(p > 0 for p in pnls)
    losses = sum(p < 0 for p in pnls)
    peak = start
    current = start
    max_drawdown = 0.0
    curve = [start]
    for pnl in pnls:
        current += pnl
        peak = max(peak, current)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - current) / peak * 100)
        curve.append(current)
    markets = {sym: {"trades": 0, "wins": 0, "net": 0.0} for sym in SYMBOLS}
    for trade in trades:
        market = markets[trade["symbol"]]
        market["trades"] += 1
        market["wins"] += int(trade["net_pnl"] > 0)
        market["net"] += trade["net_pnl"]
    return {
        "start": start, "cash": number(account["cash"]),
        "open": len(account["positions"]), "trades": len(trades),
        "wins": wins, "losses": losses, "breakeven": len(trades) - wins - losses,
        "win_rate": 100 * wins / len(trades) if trades else None,
        "net": sum(pnls), "drawdown": max_drawdown,
        "curve": curve, "markets": markets,
    }


def last_candle(cursors):
    if not cursors:
        return "No candle processed yet"
    dt = datetime.fromtimestamp(max(cursors.values()) / 1000, tz=timezone.utc)
    return (dt + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M UTC")


def equity_label(m):
    if m["open"]:
        return "Unavailable — live prices for open positions are not stored"
    return f"${m['cash']:,.2f} (no open positions)"


def markdown_report(account, cursors):
    m = metrics(account)
    rate = f"{m['win_rate']:.1f}%" if m["win_rate"] is not None else "N/A — no closed trades"
    lines = [
        "# PulseCrypto | Paper Trading Performance",
        "",
        "> SIMULATED trading only. The report cannot place real orders.",
        "",
        f"**Last processed 15-minute candle close:** {last_candle(cursors)}",
        "",
        "| Metric | Value |", "|---|---:|",
        f"| Starting simulated capital | ${m['start']:,.2f} |",
        f"| Available simulated cash | ${m['cash']:,.2f} |",
        f"| Account equity | {equity_label(m)} |",
        f"| Open positions | {m['open']} |",
        f"| Closed trades | {m['trades']} |",
        f"| Wins / losses / breakeven | {m['wins']} / {m['losses']} / {m['breakeven']} |",
        f"| Win rate on closed trades | {rate} |",
        f"| Realized net P/L (simulated fees included) | ${m['net']:+,.2f} |",
        f"| Realized P/L / starting capital | {m['net'] / m['start'] * 100:+.2f}% |",
        f"| Drawdown on closed-trade balance curve | {m['drawdown']:.2f}% |",
        "", "## BTC, ETH and SOL results", "",
        "| Market | Closed trades | Wins | Realized net P/L |", "|---|---:|---:|---:|",
    ]
    for sym, row in m["markets"].items():
        lines.append(f"| {sym[:-4]} | {row['trades']} | {row['wins']} | ${row['net']:+,.2f} |")
    lines += ["", "## Recent completed trades", ""]
    if not account["trades"]:
        lines.append("No trades have closed yet; there is not enough data to estimate a win rate.")
    else:
        lines += ["| # | Symbol | Entry | Exit | Net P/L | Reason |",
                  "|---:|---|---:|---:|---:|---|"]
        count = len(account["trades"])
        for index in range(count - 1, max(-1, count - 11), -1):
            t = account["trades"][index]
            reason = t["reason"].replace("|", "/").replace("\n", " ")
            lines.append(f"| {index + 1} | {t['symbol'][:-4]} | {t['entry']:,.4f} | "
                         f"{t['exit']:,.4f} | ${t['net_pnl']:+,.2f} | {reason} |")
    lines += [
        "", "### Important limitations", "",
        "- When positions are open, total account equity cannot be determined without current market prices.",
        "- Drawdown is based only on the sequence of realized closed-trade profits and losses, not intratrade losses.",
        "- The existing ledger does not record the exact close time of each trade.",
        "- All orders, fees, and slippage are simulated. Paper results do not guarantee live results.",
        "",
    ]
    return "\n".join(lines)


def curve_svg(curve):
    if len(curve) < 2:
        return "<p class='muted'>The realized balance chart will appear after a trade closes.</p>"
    low, high = min(curve), max(curve)
    if math.isclose(low, high):
        low, high = low - 1, high + 1
    points = " ".join(
        f"{24 + idx * 720 / (len(curve)-1):.1f},"
        f"{205 - (value-low) * 175 / (high-low):.1f}"
        for idx, value in enumerate(curve)
    )
    return (f"<svg viewBox='0 0 768 224' role='img' aria-label='Realized balance by closed trade'>"
            f"<polyline points='{points}' fill='none' stroke='#65e0a3' stroke-width='3'/>"
            "</svg>")


def html_report(account, cursors):
    m = metrics(account)
    def card(label, value):
        return (f"<div class='card'><div class='label'>{escape(label)}</div>"
                f"<div class='value'>{escape(str(value))}</div></div>")
    cards = "".join([
        card("Simulated cash", f"${m['cash']:,.2f}"),
        card("Open positions", m["open"]),
        card("Closed trades", m["trades"]),
        card("Win rate", f"{m['win_rate']:.1f}%" if m["win_rate"] is not None else "N/A"),
        card("Realized P/L", f"${m['net']:+,.2f}"),
        card("Closed-trade drawdown", f"{m['drawdown']:.2f}%"),
    ])
    markets = "".join(
        f"<tr><td>{sym[:-4]}</td><td>{r['trades']}</td><td>{r['wins']}</td>"
        f"<td>${r['net']:+,.2f}</td></tr>"
        for sym, r in m["markets"].items()
    )
    trades = ""
    for idx in range(len(account["trades"]) - 1, max(-1, len(account["trades"]) - 11), -1):
        t = account["trades"][idx]
        trades += (f"<tr><td>{idx + 1}</td><td>{t['symbol'][:-4]}</td>"
                   f"<td>{t['entry']:,.4f}</td><td>{t['exit']:,.4f}</td>"
                   f"<td>${t['net_pnl']:+,.2f}</td><td>{escape(t['reason'])}</td></tr>")
    if not trades:
        trades = "<tr><td colspan='6'>No completed trades yet.</td></tr>"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PulseCrypto Paper Performance</title>
<style>
:root{{color-scheme:dark}}body{{background:#0c1422;color:#eaf0fa;font:16px system-ui,sans-serif;margin:auto;max-width:1050px;padding:24px}}
h1{{margin-bottom:3px}}.muted,p{{color:#b2bfd2}}.note{{padding:13px;background:#243149;border-left:4px solid #79aee6;border-radius:6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}}
.card{{background:#172438;border:1px solid #33435e;padding:18px;border-radius:12px}}
.label{{color:#b2bfd2;font-size:13px}}.value{{font-size:25px;font-weight:700;margin-top:7px;overflow-wrap:anywhere}}
section{{margin-top:30px}}.scroll{{overflow:auto}}table{{border-collapse:collapse;min-width:530px;width:100%}}
th,td{{padding:11px;text-align:left;border-bottom:1px solid #33445e}}
svg{{width:100%;height:auto;border-radius:10px;background:#152238}}
</style></head><body>
<h1>PulseCrypto</h1><p>Read-only paper-trading performance report</p>
<div class="note">SIMULATED MONEY ONLY. No real trades or current-market-price estimates.</div>
<p><strong>Last processed candle:</strong> {escape(last_candle(cursors))}<br>
<strong>Starting simulated capital:</strong> ${m['start']:,.2f}<br>
<strong>Total account equity:</strong> {escape(equity_label(m))}</p>
<div class="grid">{cards}</div>
<section><h2>Realized balance curve</h2>{curve_svg(m['curve'])}</section>
<section><h2>Market breakdown</h2><div class="scroll"><table>
<tr><th>Market</th><th>Closed</th><th>Wins</th><th>Net P/L</th></tr>{markets}
</table></div></section>
<section><h2>Last 10 closed trades</h2><div class="scroll"><table>
<tr><th>#</th><th>Market</th><th>Entry</th><th>Exit</th><th>Net P/L</th><th>Exit</th></tr>{trades}
</table></div></section>
<p>Win rate excludes open positions. Realized P/L includes simulated transaction costs.
Drawdown reflects closed trades only, not mark-to-market moves. Individual trade-close timestamps
are not currently recorded in the ledger. This is a static report, not a live trading interface.</p>
</body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--html", required=True)
    args = parser.parse_args()
    account, cursors = read_snapshot(args.state)
    Path(args.markdown).write_text(markdown_report(account, cursors), encoding="utf-8")
    Path(args.html).write_text(html_report(account, cursors), encoding="utf-8")
    print(f"Read-only report: {len(account['trades'])} closed simulated trades")


if __name__ == "__main__":
    main()
