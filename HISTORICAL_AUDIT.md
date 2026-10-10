# PulseCrypto — Offline Historical Audit V1

This is an **independent, manual-only, read-only** study. It does not trade, change
the existing paper strategy, overwrite `paper-state`, access brokerage
credentials, write to Turso, or touch Cloudflare/Telegram secrets.

## Run on GitHub (mobile friendly)

1. Open **Actions → PulseCrypto Historical Strategy Audit**.
2. Select **Run workflow** on branch `main`.
3. Choose `30` days (recommended first run).
4. Open the completed run's **Summary** for the report.
5. Under **Artifacts**, download the `pulsecrypto-historical-research-30-days`
   archive containing the Markdown report, JSON metrics, and the exact historical
   candle snapshot used in the replay.

The workflow is **not scheduled**: an audit happens only when manually requested.

## What is replayed

- BTCUSDT, ETHUSDT and SOLUSDT from publicly available Binance.US **15m** spot klines. For this research audit, each 1h bar is formed from four consecutive validated 15m exchange bars (open time, high, low, final close, summed volume). We do not invent values or fill missing 15m bars. This avoids a historical data-feed discrepancy that caused the first audit run to fail.
- Every 15-minute candle in the selected historical window, with **at least 250
  older 15m bars and 255 older hourly bars** for indicator warmup.
- The **existing `signal_engine.evaluate()`** checks, in their current order:
  ATR as percent of price at least 0.15%; bullish EMA20/50/200 15m alignment;
  bullish 1h alignment; RSI14 between 45 and 65; relative volume at least 1.2.
- Only *completed* hourly and 15m candles may influence signals (lookahead guard).
- Conservative paper fills via the existing `PaperAccount`: 0.26% trading fee
  **on each side**, 0.10% adverse simulated slippage **on each side**.
- Each signal is filtered through a corrected **backtest-only** entry-level
  validation guard. The production code has a known `and`/`or` bug in
  `paper_trading.py` which should be fixed separately with regression tests.
- Signals are entered at their signal bar's close, with next-and-later-bar
  stops and targets; if both stop and target appear on one candle, the **stop
  wins**. This is a candle approximation and may be overly optimistic for
  executable entry timing or real market gaps.

## What the result means

The report includes how often each rule blocked entry, number of entries and
closed trades, profit/loss **after simulated fees and slippage**, drawdown
marked to candle closing prices, ending simulated equity, and a sampled equity
curve. Historical results do not guarantee actual profitability. The assumed
fee/slippage inputs are conservative placeholders rather than verified
exchange fee quotes.

An audit with zero closed trades **cannot establish a win rate**. We must
not loosen thresholds based on a single historical period; compare untouched
out-of-sample periods before selecting any modifications.

## When Binance.US has gaps in historical 15m candles

The first 30-day audit found a nine-hour gap in Binance.US BTCUSDT 15m
history. We do **not** fill missing prices, assume that no stops would
trigger in missing periods, or stitch simulations across a gap.

The audit downloader now retrieves each actual candle and records explicit gap
intervals and missing-candle counts in the saved JSON data. It selects only
the most recent **common uninterrupted** interval across BTC, ETH and SOL,
with another 255 complete hourly bars of indicator warmup.

If that reduces the requested 7/14/30/60/90-day period, the report displays
requested days, actually analyzed days, percentage retained, how much of the
requested start was trimmed, and the missing historical candles. **This is a
partial-window backtest**, not a complete test of the original requested
period. Selecting the latest gap-free segment can introduce selection bias,
so do not compare its performance directly with a complete-period audit.

If fewer than **75%** of the requested days remain, or the most recent
15-minute candle is unavailable, the workflow fails clearly instead of
inventing results. A shorter period or a more complete historical data source
is needed for a robust long-term study.

Binance.US API availability and historical candle quality are external
dependencies. Source files and reports are kept as ephemeral GitHub Actions
artifacts (7-day retention), not committed to the repository.
