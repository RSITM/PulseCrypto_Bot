# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 4026
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-25T23:21:33.637000+00:00
5-minute slots captured: 4026 of 4211 expected (95.61% coverage); missing: 185
Trigger sources: legacy_unlabeled=4, schedule=28, workflow_dispatch=3994

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 4026 | 4026 | 0 | 4026 | 0 | 0 | 0 | 0.0485 |
| ETHUSDT | 4026 | 4026 | 0 | 4026 | 0 | 0 | 0 | 0.2999 |
| SOLUSDT | 4026 | 4026 | 0 | 4026 | 0 | 0 | 0 | 1.2707 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
