# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8468
First observation: 2026-10-17T00:01:35.050000+00:00
Latest observation: 2026-11-15T12:16:34.488000+00:00
5-minute slots captured: 8468 of 8500 expected (99.62% coverage); missing: 32
Trigger sources: schedule=47, workflow_dispatch=8421

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8468 | 8461 | 7 | 8468 | 0 | 0 | 0 | 0.0499 |
| ETHUSDT | 8468 | 8461 | 7 | 8468 | 0 | 0 | 0 | 0.3626 |
| SOLUSDT | 8468 | 8461 | 7 | 8468 | 0 | 0 | 0 | 1.4588 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
