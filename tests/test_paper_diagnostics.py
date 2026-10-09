"""Signal decision instrumentation must not modify trade entries or exits."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from intelligence import SYMBOLS
from paper_runner import RunnerState, step
from paper_trading import PaperAccount
from signal_engine import Signal
from paper_diagnostics import (
    append_observations, load_history, markdown_summary, merge_history, empty_history,
)

FIFTEEN = 900_000
HOUR = 3_600_000
BASE = 3_600_000_000


def bars(interval, count=250, start=BASE):
    return [{"time": start + i * interval, "close": 100.0,
             "high": 101.0, "low": 99.0, "volume": 20.0}
            for i in range(count)]


def markets():
    return ({sym: bars(FIFTEEN) for sym in SYMBOLS},
            {sym: bars(HOUR, start=BASE - 200 * HOUR) for sym in SYMBOLS})


class PaperDiagnosticsTests(unittest.TestCase):
    def test_wait_reason_and_no_duplicate_for_same_candle(self):
        m15, m1h = markets()
        observations = []
        with patch("paper_runner.evaluate", return_value=Signal("WAIT", "15m trend not bullish")):
            state, events = step(RunnerState(PaperAccount(), {}), m15, m1h,
                                 "2026-10-08", diagnostics=observations)
            step(state, m15, m1h, "2026-10-08", diagnostics=observations)
        self.assertEqual(events, [])
        self.assertEqual(len(observations), 3)
        self.assertEqual({row["outcome"] for row in observations}, {"WAIT"})
        self.assertTrue(all(row["reason"] == "15m trend not bullish" for row in observations))
        self.assertEqual(state.account.cash, 500)

    def test_entry_decisions_match_actual_paper_orders(self):
        m15, m1h = markets()
        observations = []
        with patch("paper_runner.evaluate", return_value=Signal("BUY", "valid test signal", 100, 95, 115)):
            state, events = step(RunnerState(PaperAccount(), {}), m15, m1h,
                                 "2026-10-08", diagnostics=observations)
        self.assertEqual(len(events), 2)
        self.assertEqual(sum(x["outcome"] == "PAPER_BUY" for x in observations), 2)
        blocked = [x for x in observations if x["outcome"] == "ENTRY_BLOCKED"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["reason"], "SKIP_POSITION_LIMIT")
        self.assertEqual(len(state.account.positions), 2)

    def test_late_cycle_skips_evaluation_without_trade(self):
        m15, m1h = markets()
        cursor = m15["BTCUSDT"][-1]["time"] - 3 * FIFTEEN
        observations = []
        with patch("paper_runner.evaluate", side_effect=AssertionError("must not evaluate")):
            state, events = step(RunnerState(PaperAccount(),
                                            {sym: cursor for sym in SYMBOLS}),
                                 m15, m1h, "2026-10-08", diagnostics=observations)
        self.assertEqual(events, [])
        self.assertEqual({x["outcome"] for x in observations}, {"MISSED_CANDLES"})
        self.assertEqual(state.account.cash, 500)

    def test_open_positions_and_same_candle_exits(self):
        m15, m1h = markets()
        with patch("paper_runner.evaluate", return_value=Signal("BUY", "test", 100, 95, 115)):
            first, _ = step(RunnerState(PaperAccount(), {}), m15, m1h, "2026-10-08")
        for sym in SYMBOLS:
            previous = m15[sym][-1]
            m15[sym].append({"time": previous["time"] + FIFTEEN,
                             "close": 100.0, "high": 101.0, "low": 99.0,
                             "volume": 20.0})
        observations = []
        with patch("paper_runner.evaluate", return_value=Signal("WAIT", "test")):
            hold, events = step(first, m15, m1h, "2026-10-08", diagnostics=observations)
        self.assertEqual(events, [])
        self.assertEqual(sum(x["outcome"] == "OPEN_POSITION" for x in observations), 2)
        for sym in SYMBOLS:
            m15[sym].append({"time": m15[sym][-1]["time"] + FIFTEEN,
                             "close": 94.0, "high": 100.0, "low": 94.0,
                             "volume": 20.0})
        observations = []
        with patch("paper_runner.evaluate", return_value=Signal("WAIT", "test")):
            final, events = step(hold, m15, m1h, "2026-10-08", diagnostics=observations)
        self.assertEqual(len([x for x in events if x["action"] == "PAPER_SELL"]), 2)
        self.assertEqual(sum(x["outcome"] == "EXITED_THIS_CYCLE" for x in observations), 2)
        self.assertEqual(len(final.account.trades), 2)

    def test_accumulation_is_idempotent_and_reportable(self):
        observation = {
            "symbol": "BTCUSDT", "candle_ms": BASE,
            "outcome": "WAIT", "reason": "Volume confirmation absent"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "diagnostics.json"
            once = append_observations(path, [observation])
            twice = append_observations(path, [observation])
            self.assertEqual(once["counts"]["BTCUSDT"], twice["counts"]["BTCUSDT"])
            self.assertEqual(sum(twice["counts"]["BTCUSDT"].values()), 1)
            self.assertEqual(len(load_history(path)["recent"]), 1)
            summary = markdown_summary(twice)
            self.assertIn("Volume confirmation absent", summary)
            self.assertIn("Evaluated signals", summary)

    def test_invalid_observation_does_not_modify_history(self):
        history = empty_history()
        with self.assertRaises(ValueError):
            merge_history(history, [{"symbol": "ETHUSDT",
                                     "candle_ms": True,
                                     "outcome": "WAIT", "reason": "x"}])
        self.assertEqual(history, empty_history())


if __name__ == "__main__":
    unittest.main()
