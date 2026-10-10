# PulseCrypto V2-A — 5-minute historical research, not a trading bot

V2-A implements the proposed multi-timeframe setup: 4H and 1H bullish market
bias, 15M support pullback, and a 5M volume-confirmed structure break.

**V2-A tests PRICE ACTION ONLY.** The complete V2 prototype requires order-book
snapshots; historic depth, bid/ask spread, iceberg activity, market buy/sell
aggression and price impact were not recorded with historical OHLCV. We do not
invent this information or pretend that the historic book filters passed.

## Run in GitHub

1. Actions → PulseCrypto V2-A 5m Historical Comparison.
2. Run workflow → branch main → select 7 days for the first run.
3. Once green, open Summary for side-by-side V1 vs V2-A metrics.
4. Under Artifacts, download the comparison and original 5m dataset.

The workflow is manual-only and cannot modify paper-state, the V1 live
paper bot, Telegram, Cloudflare, Turso, or any broker. No trading credentials
are used.

## Historical methodology

- BTCUSDT, ETHUSDT, SOLUSDT: public Binance.US 5m spot klines.
- Verify the exact 5m opening prices, ranges and volumes. Build 15M, 1H,
  and 4H from contiguous verified 5m bars only.
- Maintain 72 complete 4H candles (288h) of warmup, also sufficient for
  V1's original EMA-200 hourly indicator.
- All four timeframes use fully CLOSED candles, never incomplete bars.
- Trade setup identified at the end of a 5m bar; potential paper entry
  priced at the actual NEXT 5m candle OPEN plus modeled adverse slippage.
  Check stop, target and after-cost expected reward again at that fill.
- Both portfolios begin at $500 and apply the current risk budget (0.5%
  initial-equity risk), trading fee (0.26% each side), slippage (0.10%
  adversely each side), stop-priority conservative bar exits.
- V1 retains its original 15m signal and simulated fill behavior.
  Consequently this is a matched-PERIOD comparison, not an identical
  execution model.
- **Binance.US occasionally reports malformed 5m bar close timestamps** (for
  example, 60 seconds instead of the required 299.999 seconds). Those 5m rows
  cannot be trusted as complete. The downloader requests the exact five real
  public 1m exchange candles for each affected 5m slot, checks that all five
  are consecutive, aligned, fully closed, and contain valid OHLCV, then
  aggregates open / high / low / close / sum(volume). These are actual exchange
  prices, not interpolated prices or artificial candles. Each reconstruction
  is logged in the downloaded data and GitHub report.
- When the 1m recovery is incomplete or invalid, the affected 5m interval
  is classified as missing. Missing candles are **never forward filled**.
  Use the latest shared gap-free interval after full warmup, with a minimum
  75% of the requested days retained. Shortened periods introduce selection
  bias and are disclosed. If the threshold cannot be met, the run fails.

## Interpretation and future work

V2-A can only establish what happened under its own research assumptions;
higher trading frequency and favorable backtests do not prove profitability.
Check net P/L, profit factor, trade sample size, fees, and drawdown. Later,
collect timestamped public depth and trades to compare V2-A to liquidity-aware
V2-B and V2-C forward, without modifying the live V1 trading rules.
