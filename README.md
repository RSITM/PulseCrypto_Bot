# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 7654
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-11-07T15:01:20.859000+00:00
5-minute slots captured: 7654 of 7855 expected (97.44% coverage); missing: 201
Trigger sources: legacy_unlabeled=4, schedule=43, workflow_dispatch=7607

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 7654 | 7651 | 3 | 7654 | 0 | 0 | 0 | 0.0515 |
| ETHUSDT | 7654 | 7651 | 3 | 7654 | 0 | 0 | 0 | 0.341 |
| SOLUSDT | 7654 | 7651 | 3 | 7654 | 0 | 0 | 0 | 1.388 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
