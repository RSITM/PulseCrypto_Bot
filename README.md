# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8494
First observation: 2026-10-19T00:01:32.735000+00:00
Latest observation: 2026-11-17T15:06:31.524000+00:00
5-minute slots captured: 8494 of 8534 expected (99.53% coverage); missing: 40
Trigger sources: schedule=42, workflow_dispatch=8452

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8494 | 8486 | 8 | 8494 | 0 | 0 | 0 | 0.0532 |
| ETHUSDT | 8494 | 8486 | 8 | 8494 | 0 | 0 | 0 | 0.3789 |
| SOLUSDT | 8494 | 8486 | 8 | 8494 | 0 | 0 | 0 | 1.5107 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
