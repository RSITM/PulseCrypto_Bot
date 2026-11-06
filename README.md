# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 7447
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-11-06T21:41:22.523000+00:00
5-minute slots captured: 7447 of 7647 expected (97.38% coverage); missing: 200
Trigger sources: legacy_unlabeled=4, schedule=40, workflow_dispatch=7403

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 7447 | 7444 | 3 | 7447 | 0 | 0 | 0 | 0.0527 |
| ETHUSDT | 7447 | 7444 | 3 | 7447 | 0 | 0 | 0 | 0.345 |
| SOLUSDT | 7447 | 7444 | 3 | 7447 | 0 | 0 | 0 | 1.3868 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
