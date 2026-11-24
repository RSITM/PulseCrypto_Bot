# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8391
First observation: 2026-10-26T00:01:30.961000+00:00
Latest observation: 2026-11-24T06:11:34.415000+00:00
5-minute slots captured: 8391 of 8427 expected (99.57% coverage); missing: 36
Trigger sources: schedule=36, workflow_dispatch=8355

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8391 | 8383 | 8 | 8391 | 0 | 0 | 0 | 0.0776 |
| ETHUSDT | 8391 | 8383 | 8 | 8391 | 0 | 0 | 0 | 0.45 |
| SOLUSDT | 8391 | 8383 | 8 | 8391 | 0 | 0 | 0 | 1.6737 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
