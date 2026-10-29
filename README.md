# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 5142
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-29T20:31:33.698000+00:00
5-minute slots captured: 5142 of 5329 expected (96.49% coverage); missing: 187
Trigger sources: legacy_unlabeled=4, schedule=34, workflow_dispatch=5104

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5142 | 5141 | 1 | 5142 | 0 | 0 | 0 | 0.0416 |
| ETHUSDT | 5142 | 5141 | 1 | 5142 | 0 | 0 | 0 | 0.3083 |
| SOLUSDT | 5142 | 5141 | 1 | 5142 | 0 | 0 | 0 | 1.277 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
