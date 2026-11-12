# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8517
First observation: 2026-10-14T00:01:34.660000+00:00
Latest observation: 2026-11-12T16:21:27.019000+00:00
5-minute slots captured: 8517 of 8549 expected (99.63% coverage); missing: 32
Trigger sources: schedule=48, workflow_dispatch=8469

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8517 | 8510 | 7 | 8517 | 0 | 0 | 0 | 0.0468 |
| ETHUSDT | 8517 | 8510 | 7 | 8517 | 0 | 0 | 0 | 0.3363 |
| SOLUSDT | 8517 | 8510 | 7 | 8517 | 0 | 0 | 0 | 1.4003 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
