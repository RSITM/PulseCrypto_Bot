# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 8354
First observation: 2026-10-25T00:01:24.874000+00:00
Latest observation: 2026-11-23T03:06:27.298000+00:00
5-minute slots captured: 8354 of 8390 expected (99.57% coverage); missing: 36
Trigger sources: schedule=39, workflow_dispatch=8315

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 8354 | 8346 | 8 | 8354 | 0 | 0 | 0 | 0.0685 |
| ETHUSDT | 8354 | 8346 | 8 | 8354 | 0 | 0 | 0 | 0.4314 |
| SOLUSDT | 8354 | 8346 | 8 | 8354 | 0 | 0 | 0 | 1.6246 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
