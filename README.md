# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8478
First observation: 2026-10-25T00:01:24.874000+00:00
Latest observation: 2026-11-23T13:26:37.073000+00:00
5-minute slots captured: 8478 of 8514 expected (99.58% coverage); missing: 36
Trigger sources: schedule=39, workflow_dispatch=8439

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8478 | 8470 | 8 | 8478 | 0 | 0 | 0 | 0.0684 |
| ETHUSDT | 8478 | 8470 | 8 | 8478 | 0 | 0 | 0 | 0.4331 |
| SOLUSDT | 8478 | 8470 | 8 | 8478 | 0 | 0 | 0 | 1.6293 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
