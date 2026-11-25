# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8355
First observation: 2026-10-27T00:01:27.836000+00:00
Latest observation: 2026-11-25T03:06:38.815000+00:00
5-minute slots captured: 8355 of 8390 expected (99.58% coverage); missing: 35
Trigger sources: schedule=37, workflow_dispatch=8318

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8355 | 8348 | 7 | 8355 | 0 | 0 | 0 | 0.0874 |
| ETHUSDT | 8355 | 8348 | 7 | 8355 | 0 | 0 | 0 | 0.46 |
| SOLUSDT | 8355 | 8348 | 7 | 8355 | 0 | 0 | 0 | 1.6965 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
