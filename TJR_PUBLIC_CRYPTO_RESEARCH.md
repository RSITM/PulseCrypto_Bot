# PulseCrypto — TJR-inspired public concepts + BTC/ETH/SOL crypto research

**This is independently coded RESEARCH; NOT TJR Trades' proprietary strategy,
not endorsed or approved by TJR, and not a reproduction of his private
indicators, live decisions, discretionary levels or any paid mentorship.**

No real orders, no simulated orders added to the running account, no
Cloudflare, Telegram, Turso, worker or V1/V2-B collector modifications.

## Public references used to inform concepts

- [TJR's Boot Camp Day 30: Execution (TJR YouTube)](https://www.youtube.com/watch?v=ESsy0uoFAz4)
  discusses liquidity sweeps, breaks of structure, order blocks, FVGs,
  and equilibrium as candidate-entry building blocks.
- [TJR's public indicator descriptions](https://www.tjrtrades.com/lto/opt-in-a)
  identify liquidity, **candle-close** BOS, FVG and confluence mapping,
  and clarify that indicators alone are not buy/sell signals.
- Other 2026 posts circulating online interpret TJR's updated strategy
  differently; they are NOT verified exact proprietary trading rules.
  In particular, a 1-minute BOS/inverse FVG trigger from select 2026
  videos is **NOT reconstructed** by this five-minute-only historical
  experiment. Do not call the result an exact 2026 model replication.

## Frozen, explicitly assumed quantitative rules

All rules in the code are our testable parameter choices where TJR teaches
a chart-discretionary idea without publishing an exact machine algorithm.

**Liquidity pools (already known at entry):**
- Prior complete New York calendar day's high/low when available.
- Proxy Asian range: prior NY-local 20:00–00:00, only when all 5m bars exist.
- Proxy London early range: current NY-local 02:00–05:00, only if complete.
- Previous *completed* 1H and 4H high/low.
- Prior 36 completed 5m bars' high/low as a three-hour structural pool.

**Sweep:** last fully closed 5m candle wicks through a known high or
low and closes back inside. Ambiguous same-candle two-sided raids are skipped.
There is **no assertion that actual stop orders were present** at those levels.

**MSS/BOS confirmation:** subsequently fully closed 5m candle breaks the
pre-sweep four-bar high/low in the reversal direction, with candle range
at least 0.65 times recent 14-bar ATR and body >= 0.35 times ATR.
Sweep must receive a shift within seven 5m bars; a setup without its zone
expires. Candle chronology matters; same-candle future confirmations
are never assumed.

**FVG:** nonoverlap of the first/third candle wicks over three complete
5m candles, width >= 0.035 ATR (not exchange order-flow proof).

**Order block:** the last opposing color 5m candle around the known
sweep-to-MSS leg, using full candle high/low as a hypothetical zone.
No proprietary TJR order-block refinement.

**Equilibrium:** 50% of the already-known sweep extreme to current
displacement extension. Strict confluence variants intersect FVG/OB with
discount (long) or premium (short) side of that 50% midpoint.
A standalone EQ version uses a 50% retracement level.

**Stop:** beyond the swept swing with an additional 0.1 ATR buffer.
**Target:** nearest remaining previously known opposing liquidity that
meets minimum gross R:R=1.33, else an explicitly labeled 2R hypothesis.
After modeled 0.26% fee + 0.10% slippage on each side, target gain must
still exceed 0.2%. These constants are *not an actual fee quote or a
promise about fill prices*.

**NY profile:** entry setup scans from 09:30 to 16:00 New York local time,
adjusted automatically for DST. Crypto 24H mode can scan all UTC hours.

**Bias:** public-session variants report 1H/4H EMA20/EMA50 context but
do not *require* alignment; crypto adaptations require aligned 1H,
with an extra strict comparison requiring both 1H and 4H alignment.
This isolates whether the assumption adds value.

**Historical entries:** rest a *hypothetical limit order* at the FVG/OB
midpoint or EQ; earliest eligible fill is the NEXT 5m candle, with a
maximum of 12 pending candles before expiry. If the next real OHLCV
range touches the nominal limit, an assumed fill incurs 0.10% adverse
slippage. If that candle already opened beyond the protective stop,
the stale order is rejected. If both high and low touch a stop and
target on a later candle, the conservative **stop-first** model wins.
On the fill candle, an intrabar stop can be recognized, but a target
cannot be awarded: 5m OHLCV has no path ordering. Stops are modeled at
adverse full bar extremes, NOT guaranteed executable stop prices.

**Account & exposure research:** hypothetical $500 start, $2.50 risk
budget per entry, 2% daily closed-loss halt, at most two concurrent
positions, and at most 1x gross notional across positions. Fees and
slippage assessed on both sides. Long results are spot-like paper
simulations. "THEORETICAL_SHORT" results are *abstract inverse-price*
payoffs without exchange borrow/funding, margin, liquidation, minimum
sizes or mark-to-market margin calls; DO NOT infer they are tradable.

## Eight non-optimized research profiles

| Variant | Trading hours | Retracement | HTF requirement |
|---|---|---|---|
| PUBLIC_NY_FVG | 9:30–16 NY | FVG | Context only |
| PUBLIC_NY_ORDER_BLOCK | 9:30–16 NY | Last opposing candle | Context only |
| PUBLIC_NY_EQUILIBRIUM | 9:30–16 NY | Midpoint | Context only |
| PUBLIC_NY_FVG_OR_OB_WITH_EQ | 9:30–16 NY | FVG (fallback OB) overlapping EQ discount/premium | Context only |
| CRYPTO_24H_FVG | 24/7 | FVG | 1H |
| CRYPTO_24H_ORDER_BLOCK | 24/7 | OB | 1H |
| CRYPTO_24H_FVG_OR_OB | 24/7 | FVG or fallback OB | 1H |
| CRYPTO_24H_STRICT_4H_1H_FVG | 24/7 | FVG | Both 4H and 1H |

These are candidate hypotheses, not winner selections or optimized settings.
The earlier/later chronological split is displayed for **PUBLIC_NY_FVG**
and **CRYPTO_24H_FVG** only. Both segments reset to $500 rather than
carrying capital state from one into the other. Repeated changes based on
the holdout would invalidate claims of independent evaluation.

## How to run from GitHub

1. Go to GitHub → Actions → **PulseCrypto TJR-Inspired Public-Method Crypto Research**.
2. Tap **Run workflow** → branch **main** → days **7** initially.
3. The workflow runs regression tests, downloads Binance.US public closed
   BTCUSDT/ETHUSDT/SOLUSDT 5m candles with a fully validated >=288h
   historical warmup, and will fail if it cannot find >=75% of the chosen
   continuous requested 7/14/30-day window.
4. Once complete, open its GitHub run summary for side-by-side TJR-inspired
   variant comparison, V1 and V2-A matched-date control metrics, and
   the earlier/later sample split.
5. Its artifact includes source 5m JSON, full trade-level research JSON
   (direction, entry, fee, target, stop, result), and Markdown report,
   retained for seven days. It never changes the V1/V2-B jobs.

## Important limitations

The algorithm does **not** know actual live order placement, liquidity
identities, historical depth/spread, resting-limit queue position,
intrabar high/low ordering, one-minute inverse FVG, or TJR's discretion.
Applying the same exact algorithm to NY-session futures vs 24/7 spot
crypto would require different underlying instruments and data; this
research tests all approaches on BTC/ETH/SOL only.

Before considering new bot signals, reproduce at least several
disjoint market regimes, track trade count and fees, inspect both tails,
collect forward price+depth observations separately, and obtain a
sufficient untouched chronological sample. No profitability claims are
appropriate without evidence; six losing trades would be more concerning
than 100 flat WAIT signals, but neither can prove long-term behavior.
