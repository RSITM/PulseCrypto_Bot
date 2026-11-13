# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8493
First observation: 2026-10-15T00:01:33.927000+00:00
Latest observation: 2026-11-13T14:16:30.818000+00:00
5-minute slots captured: 8493 of 8524 expected (99.64% coverage); missing: 31
Trigger sources: schedule=48, workflow_dispatch=8445

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8493 | 8486 | 7 | 8493 | 0 | 0 | 0 | 0.0456 |
| ETHUSDT | 8493 | 8486 | 7 | 8493 | 0 | 0 | 0 | 0.3388 |
| SOLUSDT | 8493 | 8486 | 7 | 8493 | 0 | 0 | 0 | 1.4142 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
