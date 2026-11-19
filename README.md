# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8476
First observation: 2026-10-21T00:01:36.680000+00:00
Latest observation: 2026-11-19T13:21:26.887000+00:00
5-minute slots captured: 8476 of 8513 expected (99.57% coverage); missing: 37
Trigger sources: schedule=38, workflow_dispatch=8438

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8476 | 8468 | 8 | 8476 | 0 | 0 | 0 | 0.054 |
| ETHUSDT | 8476 | 8468 | 8 | 8476 | 0 | 0 | 0 | 0.3881 |
| SOLUSDT | 8476 | 8468 | 8 | 8476 | 0 | 0 | 0 | 1.5431 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
