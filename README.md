# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 259
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-12T21:01:34.731000+00:00
5-minute slots captured: 259 of 439 expected (59.0% coverage); missing: 180
Trigger sources: legacy_unlabeled=4, workflow_dispatch=255

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 259 | 259 | 0 | 259 | 0 | 0 | 0 | 0.0713 |
| ETHUSDT | 259 | 259 | 0 | 259 | 0 | 0 | 0 | 0.2643 |
| SOLUSDT | 259 | 259 | 0 | 259 | 0 | 0 | 0 | 1.0892 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
