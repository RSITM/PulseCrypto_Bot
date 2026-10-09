"""Read-only PulseCrypto Telegram report formatting regression tests."""
import base64
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

from telegram_command_reports import (
    balance_reply, help_reply, performance_reply, signals_reply,
    trades_reply, snapshot, status_reply, make_reply)
from paper_trading import PaperAccount
from paper_state import serialize

NOW = datetime(2026, 10, 9, 15, tzinfo=timezone.utc)


class TelegramReportsTests(unittest.TestCase):
    def test_no_trades_shows_no_fictitious_win_rate(self):
        account = {"starting_equity": 500, "cash": 500,
                   "positions": {}, "trades": []}
        self.assertIn("$500.00", balance_reply(account, {}))
        self.assertIn("N/A", performance_reply(account, {}))
        self.assertIn("No completed trades", trades_reply(account))

    def test_open_positions_show_unknown_equity(self):
        account = {"starting_equity": 500, "cash": 400,
                   "positions": {"BTCUSDT": {"entry": 100}}, "trades": []}
        self.assertIn("unavailable without current prices", balance_reply(account, {}))

    def test_signal_rejection_reasons(self):
        data = {"version": 1, "counts": {
            "BTCUSDT": {"WAIT: 15m trend not bullish": 2},
            "ETHUSDT": {}, "SOLUSDT": {}}}
        output = signals_reply(data)
        self.assertIn("15m trend not bullish", output)
        self.assertIn("2 decisions", output)

    def test_health_status_failure(self):
        message = status_reply({"TRADING_OVERDUE", "CANDLES_STALE"}, {})
        self.assertIn("Needs attention", message)
        self.assertIn("TRADING_OVERDUE", message)

    def test_help_only_advertises_read_only(self):
        self.assertIn("/signals", help_reply())
        self.assertIn("No order placement", help_reply())
        self.assertIn("/help", make_reply("/unknown", "mock", NOW))

    def test_saved_account_schema(self):
        state = {"runner_version": 1,
                 "ledger": json.loads(serialize(PaperAccount())),
                 "cursors": {}}
        encoded = base64.b64encode(json.dumps(state).encode()).decode()
        with patch("telegram_command_reports.github_get",
                   return_value={"encoding": "base64", "content": encoded}):
            account, cursors = snapshot("test")
        self.assertEqual(account["cash"], 500)
        self.assertEqual(cursors, {})


if __name__ == "__main__":
    unittest.main()
