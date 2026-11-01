# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 5889
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-11-01T10:46:35.367000+00:00
5-minute slots captured: 5889 of 6076 expected (96.92% coverage); missing: 187
Trigger sources: legacy_unlabeled=4, schedule=36, workflow_dispatch=5849

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5889 | 5888 | 1 | 5889 | 0 | 0 | 0 | 0.0569 |
| ETHUSDT | 5889 | 5888 | 1 | 5889 | 0 | 0 | 0 | 0.3517 |
| SOLUSDT | 5889 | 5888 | 1 | 5889 | 0 | 0 | 0 | 1.345 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
