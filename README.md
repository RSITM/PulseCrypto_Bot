# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8500
First observation: 2026-10-19T00:01:32.735000+00:00
Latest observation: 2026-11-17T15:36:30.314000+00:00
5-minute slots captured: 8500 of 8540 expected (99.53% coverage); missing: 40
Trigger sources: schedule=42, workflow_dispatch=8458

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8500 | 8492 | 8 | 8500 | 0 | 0 | 0 | 0.0532 |
| ETHUSDT | 8500 | 8492 | 8 | 8500 | 0 | 0 | 0 | 0.3791 |
| SOLUSDT | 8500 | 8492 | 8 | 8500 | 0 | 0 | 0 | 1.5111 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
