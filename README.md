# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8376
First observation: 2026-10-13T00:01:24.195000+00:00
Latest observation: 2026-11-11T04:01:32.293000+00:00
5-minute slots captured: 8376 of 8401 expected (99.7% coverage); missing: 25
Trigger sources: schedule=50, workflow_dispatch=8326

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8376 | 8372 | 4 | 8376 | 0 | 0 | 0 | 0.0475 |
| ETHUSDT | 8376 | 8372 | 4 | 8376 | 0 | 0 | 0 | 0.3379 |
| SOLUSDT | 8376 | 8372 | 4 | 8376 | 0 | 0 | 0 | 1.3929 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
