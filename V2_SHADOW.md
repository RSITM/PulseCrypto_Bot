# PulseCrypto V2 — multi-timeframe shadow research

**Status: research-only; NOT connected to the live paper bot or Telegram.**

PulseCrypto V1 stays on its own existing 15-minute GitHub schedule, with the
same $500 paper balance, stops, targets, alert flow, and Turso backups. V2
currently evaluates only in-memory **already-closed** candles provided by
offline research callers. V2 does not fetch prices, dispatch trades, edit the
paper account, or issue live or paper orders.

## Architecture (initial prototype, unvalidated)

1. **4H + 1H bias:** price above EMA20, EMA20 above EMA50, and EMA20 rising.
   Daily macro bias is planned for a later step; it is not implemented yet.
2. **15M pullback setup:** recent candle low near 15M EMA20, then a confirming
   15M close back above EMA20 and above the preceding close.
3. **5M entry candidate:** closes above the prior three 5M highs, with
   >=1.15 times the preceding 20 candles' mean volume.
4. **Public order-book gate:** a nonfuture snapshot age <=10s, correct bid/ask
   order, spread <=12 basis points, near-touch displayed ask depth >=5 times
   intended paper notional, and walk-the-book expected impact <=10 basis points.
   A missing book returns **WAIT**, never fabricated execution quality.
5. **Paper costs and geometry:** 0.26% fee each side and 0.10% adverse slippage
   each side (research placeholders); structural stop below the recent six
   5M lows, near-term prior 15M resistance as target, reward/risk >=2, and
   modeled net target reward >=0.3% of entry after both sides' costs.

**Important:** BTC, ETH and SOL spot are the only markets, with no shorting or
leverage. All thresholds are *candidate research hypotheses* and **must not
be assumed profitable** based on passing unit tests.

## Technical limitations

- Historical backtests using candles cannot reconstruct old order books.
  A valid V2 backtest with book data requires timestamped archived snapshots
  collected prospectively, or a clearly labeled separate candle-only variant.
- The latest closed 5M, 15M, 1H and 4H candles must all be provided with
  aligned UTC OPEN timestamps and no missing bars. No lookahead is permitted.
- A posted order book is not a guaranteed executable quote. It can be
  canceled or spoofed; trade fills, taker fees and slippage may be worse.
- The price action rules here are simple reproducible hypotheses rather than
  professional-grade structure analysis. Real order flow or liquidity-sweep
  detection is **not yet implemented**.
- Although the current book module simulates market BUY impact, it never
  places orders. Further work is necessary to implement paper entries and
  exits with next-bar execution, evaluate limits vs market orders, validate
  historical coverage, and compare against the same-period V1 control.

## Phase roadmap

- **Phase 1 (this change):** isolated V2 timeframe + book research evaluator,
  strict closed-candle and freshness checks, synthetic deterministic tests.
- **Phase 2:** offline 5M/15M/1H/4H candle downloader and walk-forward
  V2-A backtest, *candle-only control explicitly separated from book gating*.
- **Phase 3:** free, time-stamped public market depth collection for V2-B/C
  forward simulation; spread/slippage, sample size and missing-book reporting.
- **Phase 4:** compare net expectancy, fees, drawdown, signal frequency and
  robustness in untouched historical periods. **Do not change V1 based on
  a single backtest or implement real trading.**

Run smoke and regression tests locally with:

`python -m unittest discover -s tests -v`

Any future V2 version must preserve **RESEARCH_ONLY** behavior until
its results justify considering a separate forward paper simulation.
