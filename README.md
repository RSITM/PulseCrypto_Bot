# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8501
First observation: 2026-10-26T00:01:30.961000+00:00
Latest observation: 2026-11-24T15:21:33.014000+00:00
5-minute slots captured: 8501 of 8537 expected (99.58% coverage); missing: 36
Trigger sources: schedule=36, workflow_dispatch=8465

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8501 | 8493 | 8 | 8501 | 0 | 0 | 0 | 0.0824 |
| ETHUSDT | 8501 | 8493 | 8 | 8501 | 0 | 0 | 0 | 0.4536 |
| SOLUSDT | 8501 | 8493 | 8 | 8501 | 0 | 0 | 0 | 1.6815 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
