# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8536
First observation: 2026-10-13T00:01:24.195000+00:00
Latest observation: 2026-11-11T17:21:35.340000+00:00
5-minute slots captured: 8536 of 8561 expected (99.71% coverage); missing: 25
Trigger sources: schedule=51, workflow_dispatch=8485

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8536 | 8532 | 4 | 8536 | 0 | 0 | 0 | 0.0471 |
| ETHUSDT | 8536 | 8532 | 4 | 8536 | 0 | 0 | 0 | 0.3366 |
| SOLUSDT | 8536 | 8532 | 4 | 8536 | 0 | 0 | 0 | 1.3951 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
