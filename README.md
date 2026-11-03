# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 6436
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-11-03T08:26:45.673000+00:00
5-minute slots captured: 6436 of 6624 expected (97.16% coverage); missing: 188
Trigger sources: legacy_unlabeled=4, schedule=37, workflow_dispatch=6395

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 6436 | 6434 | 2 | 6436 | 0 | 0 | 0 | 0.0563 |
| ETHUSDT | 6436 | 6434 | 2 | 6436 | 0 | 0 | 0 | 0.3489 |
| SOLUSDT | 6436 | 6434 | 2 | 6436 | 0 | 0 | 0 | 1.3733 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
