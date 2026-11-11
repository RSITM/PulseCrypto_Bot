# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8604
First observation: 2026-10-13T00:01:24.195000+00:00
Latest observation: 2026-11-11T23:36:28.168000+00:00
5-minute slots captured: 8604 of 8636 expected (99.63% coverage); missing: 32
Trigger sources: schedule=51, workflow_dispatch=8553

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8604 | 8599 | 5 | 8604 | 0 | 0 | 0 | 0.047 |
| ETHUSDT | 8604 | 8599 | 5 | 8604 | 0 | 0 | 0 | 0.336 |
| SOLUSDT | 8604 | 8599 | 5 | 8604 | 0 | 0 | 0 | 1.3952 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
