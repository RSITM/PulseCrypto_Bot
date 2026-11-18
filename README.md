# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8394
First observation: 2026-10-20T00:01:41.264000+00:00
Latest observation: 2026-11-18T06:36:34+00:00
5-minute slots captured: 8394 of 8432 expected (99.55% coverage); missing: 38
Trigger sources: schedule=41, workflow_dispatch=8353

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8394 | 8386 | 8 | 8394 | 0 | 0 | 0 | 0.0539 |
| ETHUSDT | 8394 | 8386 | 8 | 8394 | 0 | 0 | 0 | 0.3849 |
| SOLUSDT | 8394 | 8386 | 8 | 8394 | 0 | 0 | 0 | 1.5278 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
