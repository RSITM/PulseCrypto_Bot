# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8393
First observation: 2026-10-15T00:01:33.927000+00:00
Latest observation: 2026-11-13T05:56:27.424000+00:00
5-minute slots captured: 8393 of 8424 expected (99.63% coverage); missing: 31
Trigger sources: schedule=47, workflow_dispatch=8346

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8393 | 8386 | 7 | 8393 | 0 | 0 | 0 | 0.0456 |
| ETHUSDT | 8393 | 8386 | 7 | 8393 | 0 | 0 | 0 | 0.3381 |
| SOLUSDT | 8393 | 8386 | 7 | 8393 | 0 | 0 | 0 | 1.4125 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
