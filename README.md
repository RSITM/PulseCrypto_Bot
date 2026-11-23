# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8502
First observation: 2026-10-25T00:01:24.874000+00:00
Latest observation: 2026-11-23T15:26:24.423000+00:00
5-minute slots captured: 8502 of 8538 expected (99.58% coverage); missing: 36
Trigger sources: schedule=39, workflow_dispatch=8463

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8502 | 8494 | 8 | 8502 | 0 | 0 | 0 | 0.0746 |
| ETHUSDT | 8502 | 8494 | 8 | 8502 | 0 | 0 | 0 | 0.4394 |
| SOLUSDT | 8502 | 8494 | 8 | 8502 | 0 | 0 | 0 | 1.642 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
