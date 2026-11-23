# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8361
First observation: 2026-10-25T00:01:24.874000+00:00
Latest observation: 2026-11-23T03:41:26.284000+00:00
5-minute slots captured: 8361 of 8397 expected (99.57% coverage); missing: 36
Trigger sources: schedule=39, workflow_dispatch=8322

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8361 | 8353 | 8 | 8361 | 0 | 0 | 0 | 0.0686 |
| ETHUSDT | 8361 | 8353 | 8 | 8361 | 0 | 0 | 0 | 0.4315 |
| SOLUSDT | 8361 | 8353 | 8 | 8361 | 0 | 0 | 0 | 1.6247 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
