# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 1501
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-17T04:36:34.082000+00:00
5-minute slots captured: 1501 of 1682 expected (89.24% coverage); missing: 181
Trigger sources: legacy_unlabeled=4, schedule=10, workflow_dispatch=1487

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1501 | 1501 | 0 | 1501 | 0 | 0 | 0 | 0.0594 |
| ETHUSDT | 1501 | 1501 | 0 | 1501 | 0 | 0 | 0 | 0.2844 |
| SOLUSDT | 1501 | 1501 | 0 | 1501 | 0 | 0 | 0 | 1.2109 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
