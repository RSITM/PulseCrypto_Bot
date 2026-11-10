# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8534
First observation: 2026-10-12T00:01:18.816000+00:00
Latest observation: 2026-11-10T17:16:34.056000+00:00
5-minute slots captured: 8534 of 8560 expected (99.7% coverage); missing: 26
Trigger sources: schedule=49, workflow_dispatch=8485

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8534 | 8530 | 4 | 8534 | 0 | 0 | 0 | 0.0484 |
| ETHUSDT | 8534 | 8530 | 4 | 8534 | 0 | 0 | 0 | 0.3359 |
| SOLUSDT | 8534 | 8530 | 4 | 8534 | 0 | 0 | 0 | 1.3839 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
