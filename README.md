# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8329
First observation: 2026-10-25T00:01:24.874000+00:00
Latest observation: 2026-11-23T01:01:37.520000+00:00
5-minute slots captured: 8329 of 8365 expected (99.57% coverage); missing: 36
Trigger sources: schedule=38, workflow_dispatch=8291

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8329 | 8321 | 8 | 8329 | 0 | 0 | 0 | 0.0684 |
| ETHUSDT | 8329 | 8321 | 8 | 8329 | 0 | 0 | 0 | 0.4309 |
| SOLUSDT | 8329 | 8321 | 8 | 8329 | 0 | 0 | 0 | 1.624 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
