# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8589
First observation: 2026-10-19T00:01:32.735000+00:00
Latest observation: 2026-11-17T23:01:26.850000+00:00
5-minute slots captured: 8589 of 8629 expected (99.54% coverage); missing: 40
Trigger sources: schedule=42, workflow_dispatch=8547

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8589 | 8581 | 8 | 8589 | 0 | 0 | 0 | 0.0542 |
| ETHUSDT | 8589 | 8581 | 8 | 8589 | 0 | 0 | 0 | 0.3808 |
| SOLUSDT | 8589 | 8581 | 8 | 8589 | 0 | 0 | 0 | 1.5156 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
