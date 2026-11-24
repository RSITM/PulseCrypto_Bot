# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8516
First observation: 2026-10-26T00:01:30.961000+00:00
Latest observation: 2026-11-24T16:36:34.944000+00:00
5-minute slots captured: 8516 of 8552 expected (99.58% coverage); missing: 36
Trigger sources: schedule=36, workflow_dispatch=8480

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8516 | 8508 | 8 | 8516 | 0 | 0 | 0 | 0.083 |
| ETHUSDT | 8516 | 8508 | 8 | 8516 | 0 | 0 | 0 | 0.4551 |
| SOLUSDT | 8516 | 8508 | 8 | 8516 | 0 | 0 | 0 | 1.683 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
