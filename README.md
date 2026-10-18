# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 1937
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-18T16:56:22.330000+00:00
5-minute slots captured: 1937 of 2118 expected (91.45% coverage); missing: 181
Trigger sources: legacy_unlabeled=4, schedule=15, workflow_dispatch=1918

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1937 | 1937 | 0 | 1937 | 0 | 0 | 0 | 0.0567 |
| ETHUSDT | 1937 | 1937 | 0 | 1937 | 0 | 0 | 0 | 0.2857 |
| SOLUSDT | 1937 | 1937 | 0 | 1937 | 0 | 0 | 0 | 1.2105 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
