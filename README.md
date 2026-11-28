# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8457
First observation: 2026-10-30T00:01:33.717000+00:00
Latest observation: 2026-11-28T11:56:28.005000+00:00
5-minute slots captured: 8457 of 8496 expected (99.54% coverage); missing: 39
Trigger sources: schedule=36, workflow_dispatch=8421

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8457 | 8450 | 7 | 8457 | 0 | 0 | 0 | 0.0979 |
| ETHUSDT | 8457 | 8450 | 7 | 8457 | 0 | 0 | 0 | 0.4915 |
| SOLUSDT | 8457 | 8450 | 7 | 8457 | 0 | 0 | 0 | 1.7777 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
