"""V2-A price-only historical controls: read-only timing, gaps, real cost math."""
from datetime import datetime, timezone
import unittest

from v2_shadow import (FIVE, HOUR, FOUR_HOURS, V2Decision,
                       evaluate_v2_price_only, evaluate_v2)
from v2a_backtest import validate, simulate_v2a, compare, stamp
from v2a_history import DAY, WARMUP, download_5m, aggregate, history
from test_v2_shadow import histories as synthetic_histories, healthy_book, EVAL

END = int(datetime(2026, 9, 15, tzinfo=timezone.utc).timestamp() * 1000)


def raw(t, p=100.0):
    return {"time": t, "open": p, "high": p + 0.2, "low": p - 0.2,
            "close": p, "volume": 10.0}


def dataset(days=7):
    end = END
    start = end - days * DAY
    warmup = start - WARMUP
    raw_bars = [raw(t) for t in range(warmup, end, FIVE)]
    return {
        "format_version": 2, "source": "Binance.US public spot klines 5m",
        "requested_start_ms": start, "analysis_start_ms": start,
        "analysis_end_ms": end, "warmup_start_ms": warmup,
        "coverage": {"requested_days": days, "actual_days": days,
                     "retained_pct": 100., "trimmed_start_days": 0.,
                     "gaps": {sym: [] for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}},
        "symbols": {sym: [dict(row) for row in raw_bars]
                    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}
    }


def kline(t, p=100., interval=FIVE):
    return [t, str(p), str(p+.2), str(p-.2), str(p), "10", t+interval-1]


class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): pass
    def json(self): return self.payload


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append(dict(params))
        return FakeResponse(
            [x for x in self.rows if params["startTime"] <= x[0] <= params["endTime"]]
            [:params["limit"]])


class FiveMinuteHistoricalTests(unittest.TestCase):
    def test_pagination_and_confirmed_history(self):
        rows = [kline(i * FIVE) for i in range(1021)]
        session = FakeSession(rows)
        actual, gaps = download_5m(session, "BTCUSDT", FIVE, 1021 * FIVE,
                                   1025 * FIVE)
        self.assertEqual(len(actual), 1020)
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(gaps, [])
        self.assertEqual(actual[-1]["open"], 100.)

    def test_gap_logged_but_never_filled(self):
        rows = [kline(i * FIVE) for i in (0, 1, 4, 5)]
        result, gaps = download_5m(FakeSession(rows), "BTCUSDT",
                                   0, 6 * FIVE, 8 * FIVE)
        self.assertEqual(len(result), 4)
        self.assertEqual(gaps, [{"start_ms": 2 * FIVE, "end_exclusive_ms": 4 * FIVE,
                                 "missing_5m": 2}])

    def test_aggregation_has_no_future_or_invented_candles(self):
        rows = [raw(i*FIVE, float(100+i)) for i in range(12)]
        bars = aggregate(rows, 0, 12 * FIVE, HOUR)
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0]["close"], 111.)
        self.assertEqual(bars[0]["high"], 111.2)
        rows[4]["time"] = 5 * FIVE
        with self.assertRaisesRegex(ValueError, "Missing five-minute"):
            aggregate(rows, 0, 12 * FIVE, HOUR)

    def test_v2_history_shared_window_is_strict(self):
        end = END
        now = end + FOUR_HOURS
        start = end - 7 * DAY - WARMUP
        n = (end - start) // FIVE
        rows = [kline(start+i*FIVE) for i in range(n)]
        session = FakeSession(rows)
        d = history(7, session=session, now_ms=now)
        self.assertEqual(d["analysis_end_ms"], end)
        self.assertEqual(d["analysis_start_ms"], end - 7*DAY)
        self.assertEqual(d["coverage"]["retained_pct"], 100.0)
        self.assertEqual(len(session.calls), (n+999)//1000 * 3)
        self.assertTrue(all(c["interval"] == "5m" for c in session.calls))

    def test_missing_most_recent_candle_fails_closed(self):
        end = END
        start = end - 7*DAY-WARMUP
        rows = [kline(t) for t in range(start, end-FIVE, FIVE)]
        with self.assertRaisesRegex(ValueError, "Most recent"):
            history(7, session=FakeSession(rows), now_ms=end+FOUR_HOURS)


class ReplayTests(unittest.TestCase):
    def test_bad_data_and_missing_candle_rejected(self):
        d = dataset()
        validate(d)
        d["symbols"]["BTCUSDT"][0]["open"] = 0
        with self.assertRaisesRegex(ValueError, "invalid"):
            validate(d)
        d = dataset()
        d["symbols"]["ETHUSDT"].pop(100)
        with self.assertRaisesRegex(ValueError, "incomplete"):
            validate(d)

    def test_zero_trade_and_same_period_baseline(self):
        data = dataset()
        result = compare(data)
        a, b = result["V1_control"], result["V2A_candle_only"]
        self.assertEqual(result["mode"], "MATCHED_PERIOD_V1_V2A_HISTORICAL_RESEARCH")
        self.assertEqual(a["closed_trades"], 0)
        self.assertEqual(b["closed_trades"], 0)
        self.assertEqual(a["paper_entries"], 0)
        self.assertEqual(b["paper_entries"], 0)
        self.assertEqual(b["ending_marked_equity_usd"], 500)
        self.assertEqual(b["order_book_history"], "UNAVAILABLE: not simulated or inferred")
        self.assertIsNone(b["win_rate_pct"])

    def test_candle_only_vs_real_book_gate_is_separate(self):
        setup = synthetic_histories()
        without_book = evaluate_v2_price_only("BTCUSDT", setup, EVAL)
        self.assertEqual(without_book.action, "CANDIDATE_PRICE_ONLY")
        with_normal_gate = evaluate_v2("BTCUSDT", setup, EVAL)
        self.assertEqual(with_normal_gate.action, "WAIT")
        self.assertIn("No contemporaneous order-book", with_normal_gate.reason)
        with_book = evaluate_v2("BTCUSDT", setup, EVAL, healthy_book())
        self.assertEqual(with_book.action, "CANDIDATE")

    def test_next_open_entry_and_conservative_same_bar_stop(self):
        data = dataset()
        start = data["analysis_start_ms"]
        first_after = (start + FIVE - data["warmup_start_ms"]) // FIVE
        entry_bar = data["symbols"]["BTCUSDT"][first_after]
        entry_bar.update({"open": 100.2, "high": 103.0, "low": 98.0,
                          "close": 100.0})
        def once(symbol, frames, at):
            if symbol == "BTCUSDT" and at == start + FIVE:
                return V2Decision("CANDIDATE_PRICE_ONLY", "synthetic test",
                                  symbol, at, "BULLISH_4H_1H",
                                  "15M_EMA20_PULLBACK",
                                  entry_reference=100, stop=99, target=103)
            return V2Decision("WAIT", "No new setup", symbol, at)
        report = simulate_v2a(data, once)
        self.assertEqual(report["paper_entries"], 1)
        self.assertEqual(report["closed_trades"], 1)
        self.assertEqual(report["wins"], 0)
        self.assertEqual(report["losses"], 1)
        self.assertEqual(report["first_entry"], stamp(start+FIVE))
        self.assertEqual(report["first_entry_actual_next_bar_open"], 100.2)
        self.assertEqual(report["trades"][0]["reason"], "STOP")
        self.assertLess(report["net_realized_pnl_usd"], 0)

    def test_last_candle_candidate_remains_pending_not_filled(self):
        data = dataset()
        last_signal = data["analysis_end_ms"]
        def last(symbol, frames, at):
            if symbol == "SOLUSDT" and at == last_signal:
                return V2Decision("CANDIDATE_PRICE_ONLY", "last signal",
                                  symbol, at, "BULLISH_4H_1H",
                                  "15M_EMA20_PULLBACK",
                                  entry_reference=100, stop=99, target=103)
            return V2Decision("WAIT", "No new setup", symbol, at)
        result = simulate_v2a(data, last)
        self.assertEqual(result["paper_entries"], 0)
        self.assertEqual(result["rejections"]["PENDING_AT_END_UNFILLED"], 1)


if __name__ == "__main__":
    unittest.main()
