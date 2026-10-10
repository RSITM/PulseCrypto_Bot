"""Offline regression tests for backtest timing, safety, fee assumptions, and history."""
from datetime import datetime, timezone
import unittest

from historical_backtest import replay, valid_levels, M15, H1
from historical_candles import bars_for_range, download
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


if __name__ == "__main__":
    unittest.main()
