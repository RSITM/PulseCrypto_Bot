# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8346
First observation: 2026-10-15T00:01:33.927000+00:00
Latest observation: 2026-11-13T02:01:21.401000+00:00
5-minute slots captured: 8346 of 8377 expected (99.63% coverage); missing: 31
Trigger sources: schedule=46, workflow_dispatch=8300

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8346 | 8339 | 7 | 8346 | 0 | 0 | 0 | 0.0455 |
| ETHUSDT | 8346 | 8339 | 7 | 8346 | 0 | 0 | 0 | 0.3365 |
| SOLUSDT | 8346 | 8339 | 7 | 8346 | 0 | 0 | 0 | 1.4115 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
