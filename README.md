# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8600
First observation: 2026-10-23T00:01:36.373000+00:00
Latest observation: 2026-11-21T23:36:27.631000+00:00
5-minute slots captured: 8600 of 8636 expected (99.58% coverage); missing: 36
Trigger sources: schedule=36, workflow_dispatch=8564

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8600 | 8592 | 8 | 8600 | 0 | 0 | 0 | 0.0664 |
| ETHUSDT | 8600 | 8592 | 8 | 8600 | 0 | 0 | 0 | 0.42 |
| SOLUSDT | 8600 | 8592 | 8 | 8600 | 0 | 0 | 0 | 1.5958 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
