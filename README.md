# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 492
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-13T16:26:24.003000+00:00
5-minute slots captured: 492 of 672 expected (73.21% coverage); missing: 180
Trigger sources: legacy_unlabeled=4, schedule=3, workflow_dispatch=485

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 492 | 492 | 0 | 492 | 0 | 0 | 0 | 0.0606 |
| ETHUSDT | 492 | 492 | 0 | 492 | 0 | 0 | 0 | 0.2766 |
| SOLUSDT | 492 | 492 | 0 | 492 | 0 | 0 | 0 | 1.1904 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
