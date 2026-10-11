"""V2-B offline regression tests: public data, timestamp safety, no orders."""
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from v2_shadow import evaluate_v2, FIVE, FIFTEEN, FOUR_HOURS
from v2b_forward import (
    collect_once, depth_snapshot, fetch_closed_candles,
    sample_recent_public_trades, summarize, load_closed_four_timeframes,
    FORWARD_LAG_MAX_MS,
)
from v2b_archive import append_snapshot, validate_observation, read_day
from test_v2_shadow import EVAL, histories, healthy_book

SAMPLED_AT = EVAL + 60_000


def fake_kline(t, step, price):
    return [t, str(price), str(price + 0.2), str(price - 0.2),
            str(price), "10.0", t + step - 1]


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class MarketSession:
    def __init__(self, malformed=False):
        self.malformed = malformed
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, dict(params)))
        if not url.startswith("https://api.binance.us/api/v3/"):
            raise AssertionError("Attempt to use an unexpected market-data URL")
        if url.endswith("/klines"):
            interval = params["interval"]
            step = FIVE if interval == "5m" else FIFTEEN
            raw = []
            for i, at in enumerate(range(params["startTime"],
                                         params["endTime"] + 1, step)):
                row = fake_kline(at, step, 100 + i * .01)
                if self.malformed and i == 3:
                    row[6] = at + 60_000
                raw.append(row)
            return FakeResponse(raw[:params["limit"]])
        if url.endswith("/depth"):
            return FakeResponse({
                "lastUpdateId": 120,
                "bids": [[str(100 - i*.01), "100"] for i in range(10)],
                "asks": [[str(100.01 + i*.01), "100"] for i in range(10)],
            })
        if url.endswith("/trades"):
            return FakeResponse([
                {"id": 1, "time": EVAL + 30_000, "price": "100.0",
                 "qty": "1", "isBuyerMaker": False},
                {"id": 2, "time": EVAL + 40_000, "price": "101",
                 "qty": "2", "isBuyerMaker": True},
            ])
        raise AssertionError("Unexpected endpoint")


class ForwardSnapshotTests(unittest.TestCase):
    def test_public_ohlcv_candle_lengths_and_higher_timeframe(self):
        rows = load_closed_four_timeframes(MarketSession(), "BTCUSDT", EVAL)
        self.assertEqual(len(rows["4h"]), 55)
        self.assertGreaterEqual(len(rows["1h"]), 55)
        self.assertEqual(len(rows["5m"]), 45)
        self.assertEqual(rows["5m"][-1]["time"], EVAL - FIVE)
        self.assertEqual(rows["4h"][-1]["time"], EVAL - FOUR_HOURS)

    def test_bad_or_incomplete_15m_exchange_history_is_not_synthesized(self):
        with self.assertRaisesRegex(ValueError, "abnormal"):
            load_closed_four_timeframes(MarketSession(malformed=True), "BTCUSDT", EVAL)
        class MissingOneBar(MarketSession):
            def get(self, url, params, timeout):
                response = super().get(url, params, timeout)
                if url.endswith("/klines"):
                    response.payload = response.payload[:-1]
                return response
        with self.assertRaisesRegex(ValueError, "incomplete"):
            fetch_closed_candles(MissingOneBar(), "BTCUSDT", "15m",
                                 EVAL - 4*FIFTEEN, EVAL, FIFTEEN)

    def test_depth_has_receipt_time_not_fictitious_exchange_event_time(self):
        book, raw = depth_snapshot(MarketSession(), "BTCUSDT",
                                   lambda: SAMPLED_AT)
        self.assertEqual(book["timestamp_kind"],
                         "client_REST_response_receipt_not_exchange_event")
        self.assertEqual(book["received_at_ms"], SAMPLED_AT)
        self.assertGreater(book["near_bid_notional_usd"], 0)
        self.assertGreater(book["near_ask_notional_usd"], 0)
        self.assertTrue(book["paper_liquidity_pass"])
        self.assertEqual(book["paper_buy_impact_bps"], 0)
        self.assertEqual(len(book["top_bids"]), 10)
        self.assertEqual(raw["timestamp_ms"], SAMPLED_AT)

    def test_recent_trades_are_explicitly_partial_sample(self):
        data = sample_recent_public_trades(MarketSession(), "BTCUSDT",
                                           lambda: SAMPLED_AT)
        self.assertEqual(data["sampled_trades"], 2)
        self.assertEqual(data["last_60s_buyer_aggressor_count"], 1)
        self.assertEqual(data["last_60s_seller_aggressor_count"], 1)
        self.assertEqual(data["last_60s_window_coverage"],
                         "PARTIAL_OR_UNVERIFIED_recent_200_only")

    def test_depth_is_checked_at_observed_time_not_backdated_candle_close(self):
        h = histories()
        b = healthy_book()
        b["timestamp_ms"] = EVAL + 60_000
        traditional = evaluate_v2("BTCUSDT", h, EVAL, b)
        self.assertEqual(traditional.action, "WAIT")
        self.assertIn("stale or future", traditional.reason)
        sampled = evaluate_v2("BTCUSDT", h, EVAL, b,
                              observed_at_ms=EVAL + 60_000)
        self.assertEqual(sampled.action, "CANDIDATE")
        delayed = evaluate_v2("BTCUSDT", h, EVAL, b,
                              observed_at_ms=EVAL + FORWARD_LAG_MAX_MS + 1)
        self.assertEqual(delayed.action, "WAIT")
        self.assertIn("too late", delayed.reason)

    def test_on_time_full_public_market_collection(self):
        record = collect_once(MarketSession(), lambda: SAMPLED_AT)
        self.assertEqual(record["schema"], "pulsecrypto-v2b-forward-observation-v1")
        self.assertEqual(record["mode"], "RESEARCH_SHADOW_NO_ORDERS")
        self.assertEqual(record["signal_closed_at_ms"], EVAL)
        self.assertEqual(set(record["symbols"]), {"BTCUSDT", "ETHUSDT", "SOLUSDT"})
        self.assertIsInstance(summarize(record), str)
        for data in record["symbols"].values():
            self.assertEqual(data["candles_status"], "verified_contiguous_closed")
            self.assertEqual(data["observation_status"], "ON_TIME_SHADOW_RESEARCH")
            self.assertEqual(data["observation_lag_ms"], 60_000)
            self.assertIsNotNone(data["full_v2"])
            self.assertEqual(data["order_book"]["received_at_ms"], SAMPLED_AT)
            self.assertEqual(data["recent_trades"]["sampled_trades"], 2)

    def test_late_schedule_records_book_but_never_calls_it_entry_time(self):
        later = EVAL + FORWARD_LAG_MAX_MS + 1
        record = collect_once(MarketSession(), lambda: later)
        for data in record["symbols"].values():
            self.assertEqual(
                data["observation_status"], "DELAYED_NOT_AN_EXECUTION_TIME_SIGNAL")
            self.assertIsNone(data["full_v2"])
            self.assertIsNotNone(data["order_book"])

    def test_candle_unavailable_still_keeps_depth_observation(self):
        record = collect_once(MarketSession(malformed=True), lambda: SAMPLED_AT)
        for data in record["symbols"].values():
            self.assertEqual(data["candles_status"], "UNAVAILABLE")
            self.assertEqual(data["observation_status"], "CANDLES_UNAVAILABLE")
            self.assertIsNone(data["price_only"])
            self.assertIsNotNone(data["order_book"])
            self.assertIsNone(data["full_v2"])


class ArchiveTests(unittest.TestCase):
    def record(self, sampled_at=SAMPLED_AT):
        return collect_once(MarketSession(), lambda: sampled_at)

    def test_daily_archive_is_deduplicated_and_stats_keep_timing(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = root / "sample.json"
            data = self.record()
            snapshot.write_text(json.dumps(data), encoding="utf-8")
            out = root / "branch"
            first = append_snapshot(snapshot, out)
            twice = append_snapshot(snapshot, out)
            self.assertEqual(first["samples"], 1)
            self.assertEqual(twice["samples"], 1)
            self.assertEqual(twice["by_symbol"]["BTCUSDT"]["on_time"], 1)
            self.assertIn("V2-B", (out / "README.md").read_text())
            archive = list((out / "data").glob("*.jsonl"))
            self.assertEqual(len(archive), 1)
            self.assertEqual(len(read_day(archive[0])), 1)
            self.assertEqual(len(list(out.glob("manifest.json"))), 1)

    def test_delayed_snapshot_is_kept_without_misleading_candidates(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            p = root / "sample.json"
            p.write_text(json.dumps(self.record(EVAL + 200_000)))
            report = append_snapshot(p, root / "branch")
            self.assertEqual(report["by_symbol"]["ETHUSDT"]["delayed"], 1)
            self.assertEqual(report["by_symbol"]["ETHUSDT"].get("on_time", 0), 0)

    def test_archive_refuses_mismatched_signal_or_fake_late_candidate(self):
        data = self.record()
        data["signal_closed_at_ms"] += FIVE
        with self.assertRaisesRegex(ValueError, "timestamp"):
            validate_observation(data)
        data = self.record(EVAL + 200_000)
        data["symbols"]["BTCUSDT"]["full_v2"] = {"action": "CANDIDATE"}
        with self.assertRaisesRegex(ValueError, "Delayed"):
            validate_observation(data)


if __name__ == "__main__":
    unittest.main()
