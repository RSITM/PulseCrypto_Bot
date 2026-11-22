# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8577
First observation: 2026-10-24T00:01:35.126000+00:00
Latest observation: 2026-11-22T21:41:34.200000+00:00
5-minute slots captured: 8577 of 8613 expected (99.58% coverage); missing: 36
Trigger sources: schedule=37, workflow_dispatch=8540

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8577 | 8569 | 8 | 8577 | 0 | 0 | 0 | 0.0672 |
| ETHUSDT | 8577 | 8569 | 8 | 8577 | 0 | 0 | 0 | 0.4265 |
| SOLUSDT | 8577 | 8569 | 8 | 8577 | 0 | 0 | 0 | 1.6156 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
