# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8452
First observation: 2026-10-15T00:01:33.927000+00:00
Latest observation: 2026-11-13T10:51:31.782000+00:00
5-minute slots captured: 8452 of 8483 expected (99.63% coverage); missing: 31
Trigger sources: schedule=47, workflow_dispatch=8405

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8452 | 8445 | 7 | 8452 | 0 | 0 | 0 | 0.0457 |
| ETHUSDT | 8452 | 8445 | 7 | 8452 | 0 | 0 | 0 | 0.3387 |
| SOLUSDT | 8452 | 8445 | 7 | 8452 | 0 | 0 | 0 | 1.413 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
