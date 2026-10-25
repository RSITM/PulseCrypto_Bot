# PulseCrypto V2-B: public book and order-flow forward observations

**Research-only public exchange market data; zero orders, no portfolio writes.**

Snapshots retained on branch: 3872
First observation: 2026-10-11T08:30:20.849000+00:00
Latest observation: 2026-10-25T10:31:34.671000+00:00
5-minute slots captured: 3872 of 4057 expected (95.44% coverage); missing: 185
Trigger sources: legacy_unlabeled=4, schedule=26, workflow_dispatch=3842

| Symbol | Samples | On-time | Delayed | Candle history verified | Depth unavailable | Price-only candidates | Depth-gated candidates | Mean on-time spread (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 3872 | 3872 | 0 | 3872 | 0 | 0 | 0 | 0.0492 |
| ETHUSDT | 3872 | 3872 | 0 | 3872 | 0 | 0 | 0 | 0.2988 |
| SOLUSDT | 3872 | 3872 | 0 | 3872 | 0 | 0 | 0 | 1.2601 |

Order-book metrics are sampled *only when GitHub runs*; resting depth can be spoofed or canceled and is not a guaranteed fill.
The public last-200-trades REST endpoint is a partial recent sample, not historical tick coverage or verified continuous order flow.
Neither candidates nor observed spread imply a profitable forward strategy.
Scheduled GitHub Actions jobs may run late or be skipped. Delayed data is never backdated to a completed 5m candle.
Retention deletes old files from the current branch tip, but Git commit history may still retain earlier snapshots.
