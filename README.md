# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8314
First observation: 2026-10-28T00:01:34.685000+00:00
Latest observation: 2026-11-26T00:06:35.424000+00:00
5-minute slots captured: 8314 of 8354 expected (99.52% coverage); missing: 40
Trigger sources: schedule=34, workflow_dispatch=8280

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8314 | 8307 | 7 | 8314 | 0 | 0 | 0 | 0.0934 |
| ETHUSDT | 8314 | 8307 | 7 | 8314 | 0 | 0 | 0 | 0.4757 |
| SOLUSDT | 8314 | 8307 | 7 | 8314 | 0 | 0 | 0 | 1.7244 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
