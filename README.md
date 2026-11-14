# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8401
First observation: 2026-10-16T00:01:23.337000+00:00
Latest observation: 2026-11-14T06:36:23.335000+00:00
5-minute slots captured: 8401 of 8432 expected (99.63% coverage); missing: 31
Trigger sources: schedule=49, workflow_dispatch=8352

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8401 | 8394 | 7 | 8401 | 0 | 0 | 0 | 0.0453 |
| ETHUSDT | 8401 | 8394 | 7 | 8401 | 0 | 0 | 0 | 0.345 |
| SOLUSDT | 8401 | 8394 | 7 | 8401 | 0 | 0 | 0 | 1.4255 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
