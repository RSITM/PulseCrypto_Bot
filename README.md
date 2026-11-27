# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8379
First observation: 2026-10-29T00:01:35.162000+00:00
Latest observation: 2026-11-27T05:31:29.246000+00:00
5-minute slots captured: 8379 of 8419 expected (99.52% coverage); missing: 40
Trigger sources: schedule=34, workflow_dispatch=8345

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8379 | 8372 | 7 | 8379 | 0 | 0 | 0 | 0.0954 |
| ETHUSDT | 8379 | 8372 | 7 | 8379 | 0 | 0 | 0 | 0.4888 |
| SOLUSDT | 8379 | 8372 | 7 | 8379 | 0 | 0 | 0 | 1.7506 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
