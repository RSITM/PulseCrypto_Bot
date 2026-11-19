# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8322
First observation: 2026-10-21T00:01:36.680000+00:00
Latest observation: 2026-11-19T00:31:23.422000+00:00
5-minute slots captured: 8322 of 8359 expected (99.56% coverage); missing: 37
Trigger sources: schedule=38, workflow_dispatch=8284

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8322 | 8314 | 8 | 8322 | 0 | 0 | 0 | 0.0539 |
| ETHUSDT | 8322 | 8314 | 8 | 8322 | 0 | 0 | 0 | 0.3884 |
| SOLUSDT | 8322 | 8314 | 8 | 8322 | 0 | 0 | 0 | 1.5392 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
