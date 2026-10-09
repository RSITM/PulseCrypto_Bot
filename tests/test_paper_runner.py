import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from intelligence import SYMBOLS
from signal_engine import Signal
from paper_runner import RunnerState, load_runner_state, save_runner_state, step
from paper_trading import PaperAccount

FIFTEEN = 900_000
HOUR = 3_600_000
BASE = 3_600_000_000

def bars(interval, count=250, start=BASE):
    return [{"time": start + n * interval, "close": 100.0,
             "high": 101.0, "low": 99.0, "volume": 20.0}
            for n in range(count)]

def markets(n=250):
    m15 = {s: bars(FIFTEEN, n) for s in SYMBOLS}
    m1h = {s: bars(HOUR, n, start=BASE - 200 * HOUR) for s in SYMBOLS}
    return m15, m1h

class PaperRunnerTests(unittest.TestCase):
    def test_no_duplicate_trade_same_candle(self):
        a, h = markets()
        initial = RunnerState(PaperAccount(), {})
        with patch("paper_runner.evaluate", return_value=Signal("BUY", "test", 100, 95, 115)):
            once, events = step(initial, a, h, "2026-10-08")
            twice, repeat_events = step(once, a, h, "2026-10-08")
        self.assertEqual(len(events), 2)  # two-position account cap
        self.assertEqual(len(repeat_events), 0)
        self.assertEqual(len(twice.account.positions), 2)
        self.assertEqual(initial.account.positions, {})

    def test_exit_only_on_new_candle(self):
        a, h = markets()
        initial = RunnerState(PaperAccount(), {})
        with patch("paper_runner.evaluate", return_value=Signal("BUY", "test", 100, 95, 115)):
            once, events = step(initial, a, h, "2026-10-08")
        self.assertIn("BTCUSDT", once.account.positions)
        for sym in SYMBOLS:
            last = a[sym][-1]
            a[sym].append({"time": last["time"] + FIFTEEN, "close": 94.0,
                           "high": 100.0, "low": 94.0, "volume": 20.0})
        with patch("paper_runner.evaluate", return_value=Signal("WAIT", "test")):
            next_state, events = step(once, a, h, "2026-10-08")
        self.assertEqual(len([e for e in events if e["action"] == "PAPER_SELL"]), 2)
        self.assertEqual(len(next_state.account.trades), 2)
        self.assertEqual(once.account.trades, [])

    def test_late_cycle_does_not_open_new_position(self):
        a, h = markets()
        latest = a["BTCUSDT"][-1]["time"]
        state = RunnerState(PaperAccount(), {sym: latest - 3 * FIFTEEN for sym in SYMBOLS})
        with patch("paper_runner.evaluate", return_value=Signal("BUY", "test", 100, 95, 115)):
            next_state, events = step(state, a, h, "2026-10-08")
        self.assertEqual(events, [])
        self.assertEqual(next_state.account.positions, {})
        self.assertEqual(next_state.cursors["BTCUSDT"], latest)

    def test_missing_history_refused(self):
        a, h = markets()
        state = RunnerState(PaperAccount(), {"BTCUSDT": 1})
        with self.assertRaisesRegex(ValueError, "Missing earlier bars"):
            step(state, a, h, "2026-10-08")

    def test_save_load_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "account.json"
            state = RunnerState(PaperAccount(), {"BTCUSDT": BASE})
            save_runner_state(state, path)
            loaded = load_runner_state(path)
            self.assertEqual(loaded.cursors, state.cursors)
            self.assertEqual(loaded.account.cash, 500.0)
            path.write_text('{"runner_version":99}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_runner_state(path)

    def test_reject_missing_symbol_without_mutating(self):
        a, h = markets()
        a.pop("ETHUSDT")
        original = RunnerState(PaperAccount(), {})
        with self.assertRaises(ValueError):
            step(original, a, h, "2026-10-08")
        self.assertEqual(original.cursors, {})

if __name__ == "__main__":
    unittest.main()
