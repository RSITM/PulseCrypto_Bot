# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8480
First observation: 2026-10-13T00:01:24.195000+00:00
Latest observation: 2026-11-11T12:41:26.174000+00:00
5-minute slots captured: 8480 of 8505 expected (99.71% coverage); missing: 25
Trigger sources: schedule=50, workflow_dispatch=8430

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8480 | 8476 | 4 | 8480 | 0 | 0 | 0 | 0.0471 |
| ETHUSDT | 8480 | 8476 | 4 | 8480 | 0 | 0 | 0 | 0.3366 |
| SOLUSDT | 8480 | 8476 | 4 | 8480 | 0 | 0 | 0 | 1.3937 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
