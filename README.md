# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8328
First observation: 2026-10-16T00:01:23.337000+00:00
Latest observation: 2026-11-14T00:31:35.186000+00:00
5-minute slots captured: 8328 of 8359 expected (99.63% coverage); missing: 31
Trigger sources: schedule=49, workflow_dispatch=8279

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8328 | 8321 | 7 | 8328 | 0 | 0 | 0 | 0.0452 |
| ETHUSDT | 8328 | 8321 | 7 | 8328 | 0 | 0 | 0 | 0.3438 |
| SOLUSDT | 8328 | 8321 | 7 | 8328 | 0 | 0 | 0 | 1.4203 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
