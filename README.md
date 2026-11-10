# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8481
First observation: 2026-10-12T00:01:18.816000+00:00
Latest observation: 2026-11-10T12:51:27.277000+00:00
5-minute slots captured: 8481 of 8507 expected (99.69% coverage); missing: 26
Trigger sources: schedule=49, workflow_dispatch=8432

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8481 | 8477 | 4 | 8481 | 0 | 0 | 0 | 0.0485 |
| ETHUSDT | 8481 | 8477 | 4 | 8481 | 0 | 0 | 0 | 0.3346 |
| SOLUSDT | 8481 | 8477 | 4 | 8481 | 0 | 0 | 0 | 1.384 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
