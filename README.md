# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8561
First observation: 2026-10-27T00:01:27.836000+00:00
Latest observation: 2026-11-25T20:41:27.111000+00:00
5-minute slots captured: 8561 of 8601 expected (99.53% coverage); missing: 40
Trigger sources: schedule=37, workflow_dispatch=8524

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8561 | 8554 | 7 | 8561 | 0 | 0 | 0 | 0.091 |
| ETHUSDT | 8561 | 8554 | 7 | 8561 | 0 | 0 | 0 | 0.4693 |
| SOLUSDT | 8561 | 8554 | 7 | 8561 | 0 | 0 | 0 | 1.7044 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
