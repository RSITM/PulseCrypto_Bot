# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 5894
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-11-01T11:11:29.752000+00:00
5-minute slots captured: 5894 of 6081 expected (96.92% coverage); missing: 187
Trigger sources: legacy_unlabeled=4, schedule=36, workflow_dispatch=5854

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5894 | 5893 | 1 | 5894 | 0 | 0 | 0 | 0.0569 |
| ETHUSDT | 5894 | 5893 | 1 | 5894 | 0 | 0 | 0 | 0.3516 |
| SOLUSDT | 5894 | 5893 | 1 | 5894 | 0 | 0 | 0 | 1.3456 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
