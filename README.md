# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 7320
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-11-06T11:06:27.687000+00:00
5-minute slots captured: 7320 of 7520 expected (97.34% coverage); missing: 200
Trigger sources: legacy_unlabeled=4, schedule=40, workflow_dispatch=7276

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 7320 | 7317 | 3 | 7320 | 0 | 0 | 0 | 0.0529 |
| ETHUSDT | 7320 | 7317 | 3 | 7320 | 0 | 0 | 0 | 0.3454 |
| SOLUSDT | 7320 | 7317 | 3 | 7320 | 0 | 0 | 0 | 1.3861 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
