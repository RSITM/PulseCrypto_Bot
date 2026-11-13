# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8566
First observation: 2026-10-15T00:01:33.927000+00:00
Latest observation: 2026-11-13T20:21:25.263000+00:00
5-minute slots captured: 8566 of 8597 expected (99.64% coverage); missing: 31
Trigger sources: schedule=49, workflow_dispatch=8517

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8566 | 8559 | 7 | 8566 | 0 | 0 | 0 | 0.0456 |
| ETHUSDT | 8566 | 8559 | 7 | 8566 | 0 | 0 | 0 | 0.3405 |
| SOLUSDT | 8566 | 8559 | 7 | 8566 | 0 | 0 | 0 | 1.4167 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
