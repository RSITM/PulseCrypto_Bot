# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 5328
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-30T12:01:36.025000+00:00
5-minute slots captured: 5328 of 5515 expected (96.61% coverage); missing: 187
Trigger sources: legacy_unlabeled=4, schedule=35, workflow_dispatch=5289

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5328 | 5327 | 1 | 5328 | 0 | 0 | 0 | 0.0505 |
| ETHUSDT | 5328 | 5327 | 1 | 5328 | 0 | 0 | 0 | 0.3422 |
| SOLUSDT | 5328 | 5327 | 1 | 5328 | 0 | 0 | 0 | 1.2962 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
