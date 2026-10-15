# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 898
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-15T02:21:39.330000+00:00
5-minute slots captured: 898 of 1079 expected (83.23% coverage); missing: 181
Trigger sources: legacy_unlabeled=4, schedule=6, workflow_dispatch=888

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 898 | 898 | 0 | 898 | 0 | 0 | 0 | 0.0633 |
| ETHUSDT | 898 | 898 | 0 | 898 | 0 | 0 | 0 | 0.299 |
| SOLUSDT | 898 | 898 | 0 | 898 | 0 | 0 | 0 | 1.1912 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
