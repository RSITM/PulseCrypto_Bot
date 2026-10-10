"""Offline regression tests for backtest timing, safety, fee assumptions, and history."""
from datetime import datetime, timezone
import unittest

from historical_backtest import replay, valid_levels, M15, H1
from historical_candles import bars_for_range, available_bars_for_range, download, derive_hourly_from_fifteen
from signal_engine import Signal

START = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp() * 1000)
END = START + H1


def candle(t, price, low=None, high=None):
    return {
        "time": t, "close": price,
        "low": price - 1 if low is None else low,
        "high": price + 1 if high is None else high,
        "volume": 100.0
    }


def dataset(stop_and_target=False):
    symbols = {}
    for symbol, price in (("BTCUSDT", 100.0), ("ETHUSDT", 200.0), ("SOLUSDT", 300.0)):
        q15 = [candle(START - 255 * M15 + i * M15, price) for i in range(259)]
        if stop_and_target and symbol == "BTCUSDT":
            # Next bar touches both stop and target; conservative stop wins.
            q15[256] = candle(START + M15, price, low=98.0, high=103.0)
        q1h = [candle(START - 255 * H1 + i * H1, price) for i in range(256)]
        symbols[symbol] = {"15m": q15, "1h": q1h}
    return {
        "format_version": 1, "source": "Binance.US public spot klines",
        "analysis_start_ms": START, "analysis_end_ms": END,
        "symbols": symbols
    }


def always_wait(*_args):
    return Signal("WAIT", "No trade")


def initial_btc_buy(candles, _higher):
    if candles[-1]["time"] == START and candles[-1]["close"] == 100.0:
        return Signal("BUY", "Synthetic test entry", 100.0, 99.0, 102.0)
    return always_wait()


class OfflineReplayTests(unittest.TestCase):
    def test_no_entries_reports_NA_not_fake_profits(self):
        result = replay(dataset(), always_wait)
        self.assertEqual(result["paper_entries"], 0)
        self.assertEqual(result["closed_trades"], 0)
        self.assertEqual(result["ending_equity_usd"], 500)
        self.assertIsNone(result["win_rate_pct"])
        self.assertIsNone(result["profit_factor"])
        self.assertEqual(result["decisions"]["WAIT: No trade"], 12)
        self.assertEqual(result["mode"], "RESEARCH_ONLY_NO_LIVE_CHANGES")

    def test_stop_takes_precedence_over_target_and_fees_counted(self):
        result = replay(dataset(stop_and_target=True), initial_btc_buy)
        self.assertEqual(result["paper_entries"], 1)
        self.assertEqual(result["closed_trades"], 1)
        self.assertEqual(result["wins"], 0)
        self.assertEqual(result["losses"], 1)
        self.assertLess(result["realized_net_pnl_usd"], 0)
        self.assertGreater(result["closed_trade_fees_usd"], 0)
        self.assertLess(result["ending_equity_usd"], 500)
        self.assertGreater(result["max_marked_equity_drawdown_pct"], 0)
        self.assertIsNotNone(result["first_entry"])

    def test_invalid_live_levels_are_blocked_by_research_guard(self):
        self.assertFalse(valid_levels(Signal("BUY", "bad stop", 100, 101, 102), 0.001))
        self.assertFalse(valid_levels(Signal("BUY", "bad target", 100, 99, 99.9), 0.001))
        self.assertFalse(valid_levels(Signal("BUY", "target below slipped fill", 100, 99, 100.05), 0.001))
        self.assertTrue(valid_levels(Signal("BUY", "valid", 100, 99, 102), 0.001))

    def test_missing_bar_rejected_instead_of_fabricating_returns(self):
        d = dataset()
        d["symbols"]["SOLUSDT"]["15m"].pop()
        with self.assertRaisesRegex(ValueError, "coverage/warmup incomplete"):
            replay(d, always_wait)

    def test_analysis_requires_all_three_markets(self):
        d = dataset()
        del d["symbols"]["ETHUSDT"]
        with self.assertRaisesRegex(ValueError, "BTC, ETH and SOL"):
            replay(d, always_wait)

    def test_insufficient_1h_history_rejected_no_lookahead(self):
        d = dataset()
        d["symbols"]["BTCUSDT"]["1h"] = d["symbols"]["BTCUSDT"]["1h"][-200:]
        with self.assertRaisesRegex(ValueError, "insufficient"):
            replay(d, always_wait)


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get(self, _url, params, timeout):
        self.calls.append(dict(params))
        available = [x for x in self.rows
                     if params["startTime"] <= x[0] <= params["endTime"]]
        return FakeResponse(available[:params["limit"]])


def raw_row(time_ms, price=100.0, interval=M15):
    return [time_ms, str(price), str(price + 1), str(price - 1),
            str(price), "10", time_ms + interval - 1]


class CandleDownloaderTests(unittest.TestCase):
    def test_page_over_1000_closed_candles_without_gaps(self):
        rows = [raw_row(i * M15) for i in range(1002)]
        session = FakeSession(rows)
        found = bars_for_range(session, "BTCUSDT", "15m", 0, len(rows) * M15,
                               (len(rows) + 5) * M15)
        self.assertEqual(len(found), 1002)
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(found[-1]["time"], 1001 * M15)

    def test_gaps_raise_instead_of_skipping_candles(self):
        session = FakeSession([raw_row(0), raw_row(2 * M15)])
        with self.assertRaisesRegex(ValueError, "missing"):
            bars_for_range(session, "BTCUSDT", "15m", 0, 3 * M15, 10 * M15)

    def test_will_not_download_an_unclosed_candle(self):
        session = FakeSession([raw_row(0)])
        with self.assertRaisesRegex(ValueError, "previously closed"):
            bars_for_range(session, "BTCUSDT", "15m", 0, M15, M15)

    def test_only_predefined_audit_windows(self):
        with self.assertRaisesRegex(ValueError, "7, 14, 30, 60 or 90"):
            download(days=31, session=FakeSession([]), now_ms=START)


    def test_hourly_aggregation_uses_only_four_real_closed_quarters(self):
        quarters = [
            {"time": i * M15, "close": 100 + i, "high": 102 + i,
             "low": 99 + i, "volume": 2.0 + i}
            for i in range(8)
        ]
        hours = derive_hourly_from_fifteen(quarters, 0, 2 * H1)
        self.assertEqual(len(hours), 2)
        self.assertEqual(hours[0],
                         {"time": 0, "close": 103, "high": 105,
                          "low": 99, "volume": 14.0})
        self.assertEqual(hours[1]["time"], H1)
        self.assertEqual(hours[1]["close"], 107)
        self.assertEqual(hours[1]["high"], 109)
        self.assertEqual(hours[1]["low"], 103)
        self.assertEqual(hours[1]["volume"], 30.0)

    def test_hourly_aggregation_rejects_missing_quarter(self):
        quarters = [candle(i * M15, 100) for i in range(4)]
        quarters[2]["time"] = 3 * M15
        with self.assertRaisesRegex(ValueError, "Missing 15m source"):
            derive_hourly_from_fifteen(quarters, 0, H1)
        with self.assertRaisesRegex(ValueError, "Incomplete 15m source"):
            derive_hourly_from_fifteen(quarters[:3], 0, H1)

    def test_download_uses_only_15m_feed_and_replays_30day_history(self):
        days = 7
        now_ms = START + 10 * H1
        end = (now_ms // H1 - 1) * H1
        beginning = end - days * 24 * H1 - 255 * H1
        n = (end - beginning) // M15
        session = FakeSession([raw_row(beginning + i * M15) for i in range(n)])
        recorded = download(days=days, session=session, now_ms=now_ms)
        self.assertEqual(recorded["analysis_end_ms"], end)
        self.assertIn("Aggregated", recorded["hourly_source"])
        self.assertTrue(all(call["interval"] == "15m" for call in session.calls))
        self.assertGreater(len(session.calls), 1)
        for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
            bars = recorded["symbols"][symbol]
            self.assertEqual(len(bars["15m"]), n)
            self.assertEqual(len(bars["1h"]), n // 4)
            self.assertEqual(bars["1h"][-1]["time"], end - H1)
            self.assertEqual(bars["1h"][-1]["close"], 100.0)


    def test_sparse_exchange_candles_have_explicit_gap_records(self):
        rows = [raw_row(i * M15) for i in (0, 1, 4, 5)]
        session = FakeSession(rows)
        actual, gaps = available_bars_for_range(session, "BTCUSDT", "15m",
                                                0, 6 * M15, 15 * M15)
        self.assertEqual([bar["time"] for bar in actual],
                         [0, M15, 4 * M15, 5 * M15])
        self.assertEqual(gaps, [{"start_ms": 2 * M15,
                                 "end_exclusive_ms": 4 * M15,
                                 "missing_candles": 2}])
        self.assertEqual(len(session.calls), 1)

    def test_small_warmup_gap_shifts_actual_window_with_full_disclosure(self):
        days = 7
        now_ms = START + 10 * H1
        end = (now_ms // H1 - 1) * H1
        requested_start = end - days * 24 * H1
        warmup = requested_start - 255 * H1
        n = (end - warmup) // M15
        # Exclude a real 15m BTC candle 36h after the warmup begins.
        missing = warmup + 36 * H1
        rows = [raw_row(warmup + i * M15) for i in range(n)
                if warmup + i * M15 != missing]
        test_session = FakeSession(rows)
        data = download(days=days, session=test_session, now_ms=now_ms)
        cov = data["coverage"]
        self.assertLess(cov["actual_days"], days)
        self.assertGreaterEqual(cov["retained_pct"], 75)
        self.assertEqual(cov["requested_days"], days)
        self.assertEqual(data["requested_start_ms"], requested_start)
        self.assertEqual(cov["trimmed_start_days"], 37 / 24)
        self.assertEqual(data["analysis_start_ms"], requested_start + 37 * H1)
        self.assertEqual(cov["gaps_in_requested_fetch"]["BTCUSDT"][0]["missing_candles"], 1)
        for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
            self.assertEqual(data["symbols"][symbol]["15m"][0]["time"],
                             data["analysis_start_ms"] - 255 * H1)
        report = replay(data, always_wait)
        self.assertEqual(report["coverage"]["trimmed_start_days"], 37 / 24)
        self.assertEqual(report["paper_entries"], 0)

    def test_large_gap_fails_instead_of_reporting_biased_short_test(self):
        days = 7
        now_ms = START + 10 * H1
        end = (now_ms // H1 - 1) * H1
        warmup = end - days * 24 * H1 - 255 * H1
        n = (end - warmup) // M15
        # Cut the history 85h into warmup: less than 75% window survives.
        missing = warmup + 85 * H1
        rows = [raw_row(warmup + i * M15) for i in range(n)
                if warmup + i * M15 != missing]
        with self.assertRaisesRegex(ValueError, "Not enough continuous"):
            download(days=days, session=FakeSession(rows), now_ms=now_ms)

    def test_missing_most_recent_candle_refuses_a_stale_replay(self):
        days = 7
        now_ms = START + 10 * H1
        end = (now_ms // H1 - 1) * H1
        warmup = end - days * 24 * H1 - 255 * H1
        n = (end - warmup) // M15
        rows = [raw_row(warmup + i * M15) for i in range(n - 1)]
        with self.assertRaisesRegex(ValueError, "Recent exchange candles unavailable"):
            download(days=days, session=FakeSession(rows), now_ms=now_ms)


if __name__ == "__main__":
    unittest.main()
