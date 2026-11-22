# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8435
First observation: 2026-10-24T00:01:35.126000+00:00
Latest observation: 2026-11-22T09:51:27.811000+00:00
5-minute slots captured: 8435 of 8471 expected (99.58% coverage); missing: 36
Trigger sources: schedule=36, workflow_dispatch=8399

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8435 | 8427 | 8 | 8435 | 0 | 0 | 0 | 0.0679 |
| ETHUSDT | 8435 | 8427 | 8 | 8435 | 0 | 0 | 0 | 0.4243 |
| SOLUSDT | 8435 | 8427 | 8 | 8435 | 0 | 0 | 0 | 1.613 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
