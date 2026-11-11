# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8441
First observation: 2026-10-13T00:01:24.195000+00:00
Latest observation: 2026-11-11T09:26:37.044000+00:00
5-minute slots captured: 8441 of 8466 expected (99.7% coverage); missing: 25
Trigger sources: schedule=50, workflow_dispatch=8391

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8441 | 8437 | 4 | 8441 | 0 | 0 | 0 | 0.0473 |
| ETHUSDT | 8441 | 8437 | 4 | 8441 | 0 | 0 | 0 | 0.3372 |
| SOLUSDT | 8441 | 8437 | 4 | 8441 | 0 | 0 | 0 | 1.3929 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
