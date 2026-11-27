# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8369
First observation: 2026-10-29T00:01:35.162000+00:00
Latest observation: 2026-11-27T04:41:27.464000+00:00
5-minute slots captured: 8369 of 8409 expected (99.52% coverage); missing: 40
Trigger sources: schedule=34, workflow_dispatch=8335

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8369 | 8362 | 7 | 8369 | 0 | 0 | 0 | 0.0954 |
| ETHUSDT | 8369 | 8362 | 7 | 8369 | 0 | 0 | 0 | 0.4884 |
| SOLUSDT | 8369 | 8362 | 7 | 8369 | 0 | 0 | 0 | 1.7504 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
