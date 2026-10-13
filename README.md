# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 300
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-13T00:26:33.193000+00:00
5-minute slots captured: 300 of 480 expected (62.5% coverage); missing: 180
Trigger sources: legacy_unlabeled=4, workflow_dispatch=296

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 300 | 300 | 0 | 300 | 0 | 0 | 0 | 0.0691 |
| ETHUSDT | 300 | 300 | 0 | 300 | 0 | 0 | 0 | 0.265 |
| SOLUSDT | 300 | 300 | 0 | 300 | 0 | 0 | 0 | 1.1247 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
