# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 1104
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-15T19:31:32.855000+00:00
5-minute slots captured: 1104 of 1285 expected (85.91% coverage); missing: 181
Trigger sources: legacy_unlabeled=4, schedule=6, workflow_dispatch=1094

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1104 | 1104 | 0 | 1104 | 0 | 0 | 0 | 0.0635 |
| ETHUSDT | 1104 | 1104 | 0 | 1104 | 0 | 0 | 0 | 0.294 |
| SOLUSDT | 1104 | 1104 | 0 | 1104 | 0 | 0 | 0 | 1.2325 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
