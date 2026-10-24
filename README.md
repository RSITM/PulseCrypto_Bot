# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 3723
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-24T22:06:37.940000+00:00
5-minute slots captured: 3723 of 3908 expected (95.27% coverage); missing: 185
Trigger sources: legacy_unlabeled=4, schedule=25, workflow_dispatch=3694

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 3723 | 3723 | 0 | 3723 | 0 | 0 | 0 | 0.05 |
| ETHUSDT | 3723 | 3723 | 0 | 3723 | 0 | 0 | 0 | 0.2985 |
| SOLUSDT | 3723 | 3723 | 0 | 3723 | 0 | 0 | 0 | 1.2612 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
