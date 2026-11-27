# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8481
First observation: 2026-10-29T00:01:35.162000+00:00
Latest observation: 2026-11-27T14:01:33.390000+00:00
5-minute slots captured: 8481 of 8521 expected (99.53% coverage); missing: 40
Trigger sources: schedule=35, workflow_dispatch=8446

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8481 | 8474 | 7 | 8481 | 0 | 0 | 0 | 0.0949 |
| ETHUSDT | 8481 | 8474 | 7 | 8481 | 0 | 0 | 0 | 0.4904 |
| SOLUSDT | 8481 | 8474 | 7 | 8481 | 0 | 0 | 0 | 1.7523 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
