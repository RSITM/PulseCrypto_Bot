# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 1871
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-18T11:26:27.791000+00:00
5-minute slots captured: 1871 of 2052 expected (91.18% coverage); missing: 181
Trigger sources: legacy_unlabeled=4, schedule=15, workflow_dispatch=1852

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1871 | 1871 | 0 | 1871 | 0 | 0 | 0 | 0.0572 |
| ETHUSDT | 1871 | 1871 | 0 | 1871 | 0 | 0 | 0 | 0.283 |
| SOLUSDT | 1871 | 1871 | 0 | 1871 | 0 | 0 | 0 | 1.2017 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
