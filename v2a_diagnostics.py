"""Read-only hypothesis comparisons and trade forensics for PulseCrypto V2-A.

NO production or simulated-order changes. No external API access. All variants
are prespecified, price-only, use confirmed candles, the same paper costs,
and are intended for diagnosis rather than selecting a live trading strategy.
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path

from intelligence import SYMBOLS, atr, ema
from v2_shadow import (FIVE, FIFTEEN, HOUR, FOUR_HOURS, INTERVALS,
                       FEE_PER_SIDE, ADVERSE_SLIPPAGE_PER_SIDE,
                       MIN_REWARD_RISK, MIN_NET_REWARD_PCT,
                       V2Decision, _bullish_bias, _closed_candles,
                       evaluate_v2_price_only)
from v2a_backtest import simulate_v2a, validate, stamp


@dataclass(frozen=True)
class ResearchVariant:
    name: str
    description: str
    bias_mode: str = "4h_and_1h"
    setup_mode: str = "ema20_pullback"
    five_break_bars: int = 3


VARIANTS = (
    ResearchVariant("BASELINE_V2A",
                    "Original 4H+1H bias, 15M EMA20 pullback, 5M 3-bar breakout"),
    ResearchVariant("ONE_HOUR_ONLY",
                    "Remove ONLY 4H alignment; retain 1H, 15M and 5M rules",
                    bias_mode="1h_only"),
    ResearchVariant("BREAKOUT_RETEST",
                    "Replace ONLY 15M EMA20 pullback with 15M breakout and retest",
                    setup_mode="breakout_retest"),
    ResearchVariant("FIVE_MIN_2BAR",
                    "Change ONLY 5M breakout lookback from three bars to two",
                    five_break_bars=2),
)
VARIANT_BY_NAME = {v.name: v for v in VARIANTS}


def breakout_retest(fifteen):
    """Prior confirmed 15m breakout above resistance, followed by a retest.

    Resistance formed before the eight candles preceding the latest closed
    bar. This intentionally does NOT invent future structure or fills.
    """
    if len(fifteen) < 30:
        return False
    level = max(x["high"] for x in fifteen[-30:-10])
    recent = fifteen[-9:-1]
    if (fifteen[-1]["close"] <= level
            or fifteen[-1]["close"] <= fifteen[-2]["close"]):
        return False
    for i, candle in enumerate(recent[:-1]):
        if candle["close"] <= level * 1.001:
            continue
        if any(level * .992 <= b["low"] <= level * 1.006
               and b["close"] >= level
               for b in recent[i + 1:]):
            return True
    return False


def evaluate_variant(symbol, histories, as_of_ms, variant):
    if variant.name == "BASELINE_V2A":
        # Call unmodified baseline rather than approximating it.
        return evaluate_v2_price_only(symbol, histories, as_of_ms)
    if variant.name not in VARIANT_BY_NAME or variant != VARIANT_BY_NAME[variant.name]:
        raise ValueError("Unknown or modified predefined variant")
    if symbol not in SYMBOLS:
        raise ValueError("Unsupported market")
    if type(as_of_ms) is not int or as_of_ms <= 0 or as_of_ms % FIVE:
        raise ValueError("Historical evaluation must align to a closed 5m time")
    if not isinstance(histories, dict) or set(histories) != set(INTERVALS):
        raise ValueError("All four histories required")
    for tf in INTERVALS:
        _closed_candles(histories[tf], tf, as_of_ms)
    def wait(reason, bias="UNCONFIRMED", setup="NONE"):
        return V2Decision("WAIT", reason, symbol, as_of_ms, bias, setup)

    one_hour_bullish = _bullish_bias(histories["1h"])
    four_hour_bullish = _bullish_bias(histories["4h"])
    if not one_hour_bullish or (variant.bias_mode != "1h_only" and not four_hour_bullish):
        return wait("Higher-timeframe alignment absent", "NOT_BULLISH")
    bias = "BULLISH_1H_ONLY_RESEARCH" if variant.bias_mode == "1h_only" else "BULLISH_4H_1H"

    fifteen = histories["15m"]
    if variant.setup_mode == "ema20_pullback":
        average = ema([b["close"] for b in fifteen], 20)
        valid = (any(average * .990 <= b["low"] <= average * 1.0035
                     for b in fifteen[-8:-1])
                 and fifteen[-1]["close"] > average
                 and fifteen[-1]["close"] > fifteen[-2]["close"])
        setup = "15M_EMA20_PULLBACK"
    else:
        valid = breakout_retest(fifteen)
        setup = "15M_BREAKOUT_RETEST"
    if not valid:
        return wait("15M setup not confirmed", bias)

    five = histories["5m"]
    count = variant.five_break_bars
    if five[-1]["close"] <= max(b["high"] for b in five[-(count + 1):-1]):
        return wait("5M structure break not confirmed", bias, setup)
    volume20 = sum(b["volume"] for b in five[-21:-1]) / 20
    if volume20 <= 0 or five[-1]["volume"] < volume20 * 1.15:
        return wait("5M relative volume confirmation absent", bias, setup)
    if five[-1]["close"] <= five[-2]["close"]:
        return wait("5M close lacks upward momentum", bias, setup)

    entry = five[-1]["close"] * (1 + ADVERSE_SLIPPAGE_PER_SIDE)
    stop = min(b["low"] for b in five[-6:]) - .10 * atr(five)
    # Same structural target, fee/slippage hurdle and stop logic as baseline.
    target = max(b["high"] for b in fifteen[-21:-1])
    if stop <= 0 or stop >= entry or target <= entry:
        return wait("No valid structural stop / overhead resistance room", bias, setup)
    ratio = (target - entry) / (entry - stop)
    net_reward = (
        target * (1 - ADVERSE_SLIPPAGE_PER_SIDE) * (1 - FEE_PER_SIDE)
        - entry * (1 + FEE_PER_SIDE)
    ) / entry
    if ratio < MIN_REWARD_RISK or net_reward < MIN_NET_REWARD_PCT:
        return wait("Insufficient reward after modeled execution costs", bias, setup)
    return V2Decision(
        "CANDIDATE_PRICE_ONLY",
        f"Unvalidated price-only candidate: {variant.name}; no historical book",
        symbol, as_of_ms, bias, setup,
        round(entry, 8), round(stop, 8), round(target, 8), round(ratio, 3)
    )


def evaluator_for(variant):
    def evaluate(symbol, histories, as_of_ms):
        return evaluate_variant(symbol, histories, as_of_ms, variant)
    return evaluate


def summary_metrics(result):
    return {
        "paper_entries": result["paper_entries"],
        "closed_trades": result["closed_trades"],
        "wins": result["wins"], "losses": result["losses"],
        "win_rate_pct": result["win_rate_pct"],
        "profit_factor": result["profit_factor"],
        "total_return_pct": result["total_return_pct"],
        "net_realized_pnl_usd": result["net_realized_pnl_usd"],
        "closed_trade_fees_usd": result["closed_trade_fees_usd"],
        "max_drawdown_pct": result["max_drawdown_pct"],
        "open_positions": result["open_positions"],
        "top_rejections": sorted(result["rejections"].items(),
                                 key=lambda row: -row[1])[:7],
    }


def diagnose(data):
    start, end, _ = validate(data)
    # Chronologically ordered, static split; all model parameters are frozen.
    # Warmup comes ONLY from older previously closed real candles.
    four_h_bars = (end - start) // FOUR_HOURS
    split = start + (four_h_bars * 3 // 5) * FOUR_HOURS
    if split <= start + DAY or end - split < DAY:
        raise ValueError("Not enough history for independent training/holdout windows")
    variants = {}
    for variant in VARIANTS:
        evaluator = evaluator_for(variant)
        earlier = simulate_v2a(data, evaluator, start_ms=start, end_ms=split)
        later = simulate_v2a(data, evaluator, start_ms=split, end_ms=end)
        full = simulate_v2a(data, evaluator)
        variants[variant.name] = {
            "description": variant.description,
            "research_earlier": summary_metrics(earlier),
            "untouched_later_holdout": summary_metrics(later),
            "full_period": summary_metrics(full),
            "full_trade_forensics": full["trade_forensics"]
        }
    return {
        "mode": "V2A_FIXED_VARIANT_DIAGNOSTIC_RESEARCH_ONLY",
        "market_source": data["source"],
        "available_period": {"start": stamp(start), "end_exclusive": stamp(end),
                             "days": (end - start) / DAY},
        "early_window": {"start": stamp(start), "end_exclusive": stamp(split),
                         "days": (split - start) / DAY},
        "later_window": {"start": stamp(split), "end_exclusive": stamp(end),
                         "days": (end - split) / DAY},
        "coverage": data["coverage"],
        "variants": variants,
        "limitations": [
            "All variants are predeclared and use identical historical OHLCV data.",
            "Later holdout is chronological and portfolio state resets at split; "
            "repeatedly selecting variants based on holdout results will cause overfitting.",
            "This is exploratory research, not proof of true out-of-sample profitability.",
            "Variations change exactly one stated entry restriction; no optimized parameters.",
            "All paper costs and stop/target execution assumptions remain unchanged.",
            "No contemporaneous historical order-book data or spread/depth confirmation.",
            "Trade high/low order within 5m bars is unknown; modeled stop fills may "
            "differ materially from actual executable prices.",
            "V1 trading, Turso, Cloudflare, Telegram, and paper-state are untouched.",
        ],
    }


def report(result):
    variants = result["variants"]
    def fmt(v):
        return "N/A" if v is None else f"{v:.2f}"
    lines = [
        "# PulseCrypto V2-A research — controlled variations and loss audit",
        "",
        "**Price-action-only offline research; zero trading or account updates.**",
        "",
        f'**Full sample:** {result["available_period"]["start"]} to '
        f'{result["available_period"]["end_exclusive"]} '
        f'({result["available_period"]["days"]:.2f} days)',
        f'**Earlier window:** {result["early_window"]["days"]:.2f} days; '
        f'**later untouched chronological holdout:** {result["later_window"]["days"]:.2f} days',
        "",
        "| Predeclared variant | Full trades | Full net P/L | Full max DD | Earlier trades | Earlier net P/L | Later trades | Later net P/L |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in variants.items():
        full, early, later = (data[key] for key in
                              ("full_period", "research_earlier", "untouched_later_holdout"))
        lines.append(
            f'| {name} | {full["closed_trades"]} | USD {full["net_realized_pnl_usd"]:+.2f} '
            f'| {full["max_drawdown_pct"]:.2f}% | {early["closed_trades"]} '
            f'| USD {early["net_realized_pnl_usd"]:+.2f} | {later["closed_trades"]} '
            f'| USD {later["net_realized_pnl_usd"]:+.2f} |'
        )
    lines += ["", "## Variants (change one condition only)", ""]
    for name, variant in variants.items():
        lines += [f'- **{name}:** {variant["description"]}']
    lines += ["", "## Baseline stop and execution forensics", ""]
    baseline = variants["BASELINE_V2A"]["full_trade_forensics"]
    if not baseline:
        lines += ["No closed baseline V2-A trades; no claim about win rates is justified."]
    else:
        for t in baseline:
            stop_sensitivity = t["stop_price_hypothetical_net_pnl_usd"]
            sensitivity = ("N/A" if stop_sensitivity is None else
                           f'USD {stop_sensitivity:+.2f}')
            lines += [
                f'### {t["symbol"]} — {t["entered_at_utc"]} → {t["closed_at_utc"]}',
                f'- Outcome: **{t["exit_reason"]}**, net USD {t["net_pnl_usd"]:+.2f}; '
                f'fees USD {t["fees_usd"]:.2f}',
                f'- Actual historical next-5m OPEN: {t["next_bar_open"]:.8g}; '
                f'modeled entry after slippage: {t["modeled_entry_fill"]:.8g}',
                f'- Stop: {t["stop"]:.8g}; target: {t["target"]:.8g}; '
                f'conservative modeled exit: {t["modeled_exit_fill"]:.8g}',
                f'- Last exit-bar low: {t["exit_bar_low"]:.8g}; '
                f'stop overshoot per unit: {t["stop_overshoot_per_unit"]:.8g}; '
                f'opened below stop: {t["stop_gap_at_open"]}',
                f'- Hypothetical stop-price execution sensitivity: **{sensitivity}** '
                '(NOT a claim of executable prices)',
                "",
            ]
    lines += ["", "## Full-period baseline blocking reasons", ""]
    for reason, count in variants["BASELINE_V2A"]["full_period"]["top_rejections"]:
        lines.append(f'- {reason}: **{count}**')
    lines += ["", "## Important methodology notes", ""]
    lines += ["- " + item for item in result["limitations"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Read-only PulseCrypto V2-A diagnostics")
    parser.add_argument("--data", required=True)
    parser.add_argument("--json", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    snapshot = json.loads(Path(args.data).read_text(encoding="utf-8"))
    diagnostics = diagnose(snapshot)
    for output in (args.json, args.markdown):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(diagnostics, allow_nan=False, indent=2) + "\n",
                               encoding="utf-8")
    Path(args.markdown).write_text(report(diagnostics), encoding="utf-8")
    print("V2-A DIAGNOSTICS RESEARCH ONLY: "
          f"{len(diagnostics['variants'])} fixed variants, split holdout, no orders")


if __name__ == "__main__":
    main()
