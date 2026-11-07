# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 7702
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-11-07T19:01:32.199000+00:00
5-minute slots captured: 7702 of 7903 expected (97.46% coverage); missing: 201
Trigger sources: legacy_unlabeled=4, schedule=44, workflow_dispatch=7654

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 7702 | 7699 | 3 | 7702 | 0 | 0 | 0 | 0.0513 |
| ETHUSDT | 7702 | 7699 | 3 | 7702 | 0 | 0 | 0 | 0.3402 |
| SOLUSDT | 7702 | 7699 | 3 | 7702 | 0 | 0 | 0 | 1.3873 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
