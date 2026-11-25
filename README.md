# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8348
First observation: 2026-10-27T00:01:27.836000+00:00
Latest observation: 2026-11-25T02:31:35.390000+00:00
5-minute slots captured: 8348 of 8383 expected (99.58% coverage); missing: 35
Trigger sources: schedule=37, workflow_dispatch=8311

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8348 | 8341 | 7 | 8348 | 0 | 0 | 0 | 0.0872 |
| ETHUSDT | 8348 | 8341 | 7 | 8348 | 0 | 0 | 0 | 0.4596 |
| SOLUSDT | 8348 | 8341 | 7 | 8348 | 0 | 0 | 0 | 1.696 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
