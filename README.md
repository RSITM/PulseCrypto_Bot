# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8326
First observation: 2026-10-27T00:01:27.836000+00:00
Latest observation: 2026-11-25T00:41:20.279000+00:00
5-minute slots captured: 8326 of 8361 expected (99.58% coverage); missing: 35
Trigger sources: schedule=36, workflow_dispatch=8290

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8326 | 8319 | 7 | 8326 | 0 | 0 | 0 | 0.0869 |
| ETHUSDT | 8326 | 8319 | 7 | 8326 | 0 | 0 | 0 | 0.4589 |
| SOLUSDT | 8326 | 8319 | 7 | 8326 | 0 | 0 | 0 | 1.6951 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
