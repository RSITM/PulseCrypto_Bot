# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8403
First observation: 2026-10-20T00:01:41.264000+00:00
Latest observation: 2026-11-18T07:21:28.975000+00:00
5-minute slots captured: 8403 of 8441 expected (99.55% coverage); missing: 38
Trigger sources: schedule=41, workflow_dispatch=8362

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8403 | 8395 | 8 | 8403 | 0 | 0 | 0 | 0.0538 |
| ETHUSDT | 8403 | 8395 | 8 | 8403 | 0 | 0 | 0 | 0.3847 |
| SOLUSDT | 8403 | 8395 | 8 | 8403 | 0 | 0 | 0 | 1.5282 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
