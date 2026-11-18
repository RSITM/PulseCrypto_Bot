# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8509
First observation: 2026-10-20T00:01:41.264000+00:00
Latest observation: 2026-11-18T16:11:35.933000+00:00
5-minute slots captured: 8509 of 8547 expected (99.56% coverage); missing: 38
Trigger sources: schedule=41, workflow_dispatch=8468

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8509 | 8501 | 8 | 8509 | 0 | 0 | 0 | 0.0538 |
| ETHUSDT | 8509 | 8501 | 8 | 8509 | 0 | 0 | 0 | 0.3853 |
| SOLUSDT | 8509 | 8501 | 8 | 8509 | 0 | 0 | 0 | 1.5297 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
