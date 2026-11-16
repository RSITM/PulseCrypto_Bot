# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8418
First observation: 2026-10-18T00:01:33.433000+00:00
Latest observation: 2026-11-16T08:16:24.872000+00:00
5-minute slots captured: 8418 of 8452 expected (99.6% coverage); missing: 34
Trigger sources: schedule=43, workflow_dispatch=8375

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8418 | 8411 | 7 | 8418 | 0 | 0 | 0 | 0.0525 |
| ETHUSDT | 8418 | 8411 | 7 | 8418 | 0 | 0 | 0 | 0.3775 |
| SOLUSDT | 8418 | 8411 | 7 | 8418 | 0 | 0 | 0 | 1.4885 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
