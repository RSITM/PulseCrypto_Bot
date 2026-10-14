# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 850
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-14T22:21:33.644000+00:00
5-minute slots captured: 850 of 1031 expected (82.44% coverage); missing: 181
Trigger sources: legacy_unlabeled=4, schedule=6, workflow_dispatch=840

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 850 | 850 | 0 | 850 | 0 | 0 | 0 | 0.0651 |
| ETHUSDT | 850 | 850 | 0 | 850 | 0 | 0 | 0 | 0.3003 |
| SOLUSDT | 850 | 850 | 0 | 850 | 0 | 0 | 0 | 1.1953 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
