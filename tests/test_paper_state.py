import json
import tempfile
import unittest
from pathlib import Path
from paper_trading import PaperAccount
from paper_state import load, save, serialize, deserialize

class PaperPersistenceTests(unittest.TestCase):
    def test_new_file_creates_fresh_account(self):
        with tempfile.TemporaryDirectory() as d:
            account = load(Path(d) / "state.json")
            self.assertEqual(account.cash, 500.0)
            self.assertEqual(account.positions, {})

    def test_roundtrip_with_open_and_closed_trades(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "nested" / "account.json"
            account = PaperAccount()
            account.roll_day("2026-10-08")
            self.assertEqual(account.open_long("BTCUSDT", 100, 95, 115), "PAPER_BUY")
            self.assertEqual(account.open_long("SOLUSDT", 100, 95, 115), "PAPER_BUY")
            self.assertEqual(account.close_long("BTCUSDT", 110), "PAPER_SELL")
            save(account, path)
            restored = load(path)
            self.assertAlmostEqual(restored.cash, account.cash)
            self.assertEqual(restored.session_day, account.session_day)
            self.assertEqual(len(restored.trades), 1)
            self.assertEqual(set(restored.positions), {"SOLUSDT"})
            self.assertAlmostEqual(restored.positions["SOLUSDT"].quantity,
                                   account.positions["SOLUSDT"].quantity)
            self.assertEqual(restored.close_long("SOLUSDT", 105), "PAPER_SELL")

    def test_reject_unknown_version(self):
        account = json.loads(serialize(PaperAccount()))
        account["version"] = 999
        with self.assertRaises(ValueError):
            deserialize(json.dumps(account))

    def test_reject_tampered_position(self):
        a = PaperAccount()
        a.roll_day("2026-10-08")
        a.open_long("BTCUSDT", 100, 95, 115)
        state = json.loads(serialize(a))
        state["account"]["positions"]["BTCUSDT"]["quantity"] = -1
        with self.assertRaises(ValueError):
            deserialize(json.dumps(state))

    def test_reject_invalid_json(self):
        with self.assertRaises(json.JSONDecodeError):
            deserialize("not json")

if __name__ == "__main__":
    unittest.main()
