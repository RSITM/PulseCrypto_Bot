# PulseCrypto V2-B — forward public liquidity and book-depth research

**Paper bot V1 stays unchanged. V2-B NEVER places real or simulated orders.**

This is the first phase of the requested V2-B liquidity/market-depth upgrade:
a time-stamped read-only data collector, not an automatically executing
trading strategy. It uses free/public Binance.US spot REST APIs without
exchange API keys.

## Inputs and timestamp integrity

For BTCUSDT, ETHUSDT and SOLUSDT on Binance.US:

- Actual **closed 5M** price candles for potential entry confirmation.
- Actual **closed 15M** candles for pullback/structure detection.
- **1H and 4H** trend bars constructed from complete aligned 15M candles.
  A minimum of 55 complete 4H bars is required for EMA50 plus trend checks.
- **Public /api/v3/depth** snapshot, up to 100 bid/ask levels, with
  top 20 levels retained in the research archive, plus derived spread,
  executable displayed-ask VWAP for a hypothetical $50 order, near-touch
  bid/ask USD liquidity, and displayed-book depth imbalance.
- **Public /api/v3/trades** (last 200 available spot trades), with a
  *sampled* 60-second buyer- versus seller-aggressor notional summary
  based on isBuyerMaker. These 200 samples may NOT fully cover the
  minute, and are never represented as full continuous order flow.

All trade-tape and order-book data are observational, not guaranteed fills.
Book responses do NOT provide an exchange capture time; the script labels
their timestamp accurately as the local **REST response receipt** time.
An apparently large order-book wall might disappear before execution.

The collector compares the actual snapshot time to the last fully CLOSED
5-minute boundary and marks observations more than 150 seconds late
as DELAYED_NOT_AN_EXECUTION_TIME_SIGNAL. Late data is retained as
research, but no liquidity-aware candidate is evaluated using it.
The depth gate checks snapshot freshness at the **receipt time**, not at a
past candle close; it cannot look ahead in historical testing.

If any kline is unclosed, missing, truncated or unaligned, there is no
forward-filled data and no price candidate; the market's price data is
marked UNAVAILABLE, while a valid independent book snapshot may still be
recorded.

## When it runs, cost and persistence

The GitHub workflow **PulseCrypto V2-B Public Liquidity Research** attempts
one observation five minutes apart, nominally at UTC minutes :01, :06,
:11, :16, etc., and also supports manual execution. GitHub native schedule
is a **best-effort fallback**, not a guaranteed five-minute time series.
A change to the cron specification can reactivate a stopped schedule but
cannot prevent GitHub's job queue from dropping scheduled triggers.

### More reliable external five-minute trigger (manual account setup required)

The already-configured `workflow_dispatch` event also accepts a POST from
cron-job.org, which can be configured similarly to the existing V1 dispatcher.
**No cron-job.org job is created by this repository**: the account owner must
configure the new job in their cron-job.org dashboard.

1. In GitHub Settings > Developer settings > Personal access tokens >
   **Fine-grained tokens**, create a short-lived token restricted to
   `RSITM/PulseCrypto_Bot`, with ONLY **Actions: Read and write** plus the
   implicit metadata permission. Do not paste the token into GitHub code,
   tickets, ChatGPT, a URL or workflow logs.
2. In cron-job.org, add a NEW job titled
   `PulseCrypto V2-B public research`. Do NOT edit V1's cron job.
3. Target URL:
   `https://api.github.com/repos/RSITM/PulseCrypto_Bot/actions/workflows/v2b-forward-research.yml/dispatches`
4. Request method: **POST**. Body (JSON):
   `{"ref":"main"}`
5. Request headers: `Accept: application/vnd.github+json`,
   `Content-Type: application/json`, and
   `Authorization: Bearer <YOUR_FINE_GRAINED_PAT>`.
   Set the private bearer token in the cron-job.org header field only.
   Disable saving HTTP response bodies if possible.
6. Choose timezone **UTC**, schedule the exact minutes
   `:01, :06, :11, :16, :21, :26, :31, :36, :41, :46, :51, :56`
   every hour, every day. This gives roughly a minute for the preceding
   closed five-minute candle to settle. Enable failure alerts if desired.
7. Verify the cron-job.org result is a success response and check
   GitHub Actions V2-B runs whose trigger is `workflow_dispatch`.
   The on-time receipt status and archive coverage are the source of truth.

When both GitHub fallback scheduling and the external dispatcher fire,
`v2b_archive.py` retains a **single, earliest-captured observation** per
closed five-minute UTC candle. It never counts two dispatches of the same
candle as two separate market opportunities. The dashboard displays
**expected, observed and missing five-minute slots**, percentage coverage,
and the source of the retained triggers. Missing observations are NOT filled
with imagined historical order-book data.

The external service and GitHub runners can themselves delay; the 150-second
on-time filter still applies. PAT tokens grant workflow-dispatch capability,
so keep one-token/one-repo scope, use an expiration date, and rotate if
exposed. GitHub workflow logs record `GITHUB_EVENT_NAME` and GitHub run ID,
not the bearer token. For POST workflow dispatch, GitHub officially requires
**Actions: write** permission for fine-grained tokens.

Current setup is STILL safe without this external dispatcher; however, its
built-in GitHub scheduler alone has demonstrated sparse execution.


GitHub Actions scheduling is **best effort**. Jobs can run late or be
skipped; their own on-time/delayed counts in the report matter more than
nominal schedule frequency. No paid third-party API or subscription is
required. GitHub account usage limits and provider API limits still apply.

Every execution uploads a 7-day GitHub Actions artifact with its original
JSON snapshot and Markdown observation. For persistent forward comparison,
the collector appends snapshots to a separate **v2b-observations** Git
branch, **never** to main, paper-state, Turso, or Cloudflare. The current
branch tip retains up to 30 days of daily JSONL files under data/ and
includes a human-readable README.md and manifest.json with observation
counts, on-time status, spreads and V2 price-only vs depth-gated candidates.
Old snapshots can remain in prior Git commit history even after file
retention; do not put private information in public market-data archives.

The scheduled job requests contents:write ONLY to commit the public research
archive. It uses no Telegram bot tokens, exchange keys, Turso credentials,
Cloudflare secrets, or execution routes. The price engine emits WAIT or
CANDIDATE as research labels; those are **NOT trade instructions**.

## How to inspect

1. GitHub Actions → **PulseCrypto V2-B Public Liquidity Research**.
2. Open the latest run → **Summary**. The table shows observed price-action
   status, research depth filter, sampling lag and public liquidity metrics.
3. After the first successful scheduled/manual run, select repository
   branch **v2b-observations** and read README.md for cumulative counts.
4. Daily UTC files under data/YYYY-MM-DD.jsonl store original snapshots.

## Data limitations and next research steps

- This version is an **observation collector only**, so it DOES NOT provide
  forward profit factor, win rate or a V2-B simulated account. Such numbers
  would be fabricated before we have time-stamped candidate/future-price pairs.
- Five-minute scheduled snapshots may miss intrabar order-book changes;
  order book spoofing and liquidity withdrawal remain risks.
- Flow from the last 200 public trades is **sampled**, not full CVD, and
  observed at a different time from the book snapshot.
- No shorts, leverage, real trade execution or bot state changes.
- V2 candidates are relatively rare in prior candle-only backtests. Enough
  forward on-time candidates may take weeks/months; no profitability can
  be inferred from sparse observations.

After collecting enough legitimate observations, independently design a
shadow paper-simulator with next-candle pricing and matched control group,
then compare V2-A versus liquidity-aware V2-B on future actual observations,
including missing-data rates, costs, drawdowns, and sample size. Keep V1
paper-only and unchanged until strong independent evidence warrants review.
