# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 4750
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-28T11:46:45.372000+00:00
5-minute slots captured: 4750 of 4936 expected (96.23% coverage); missing: 186
Trigger sources: legacy_unlabeled=4, schedule=33, workflow_dispatch=4713

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 4750 | 4749 | 1 | 4750 | 0 | 0 | 0 | 0.0441 |
| ETHUSDT | 4750 | 4749 | 1 | 4750 | 0 | 0 | 0 | 0.3057 |
| SOLUSDT | 4750 | 4749 | 1 | 4750 | 0 | 0 | 0 | 1.2762 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
