"""Offline regression tests for the read-only performance report."""
import json
from pathlib import Path
import tempfile
import unittest

from paper_report import metrics, markdown_report, html_report, read_snapshot, equity_label


def empty_account():
    return {
        "starting_equity": 500.0, "cash": 500.0,
        "positions": {}, "trades": []
    }


def trade(symbol, pnl, reason="TARGET"):
    return {
        "symbol": symbol, "entry": 100.0, "exit": 105.0,
        "quantity": 1.0, "net_pnl": pnl,
        "entry_fee": 0.2, "exit_fee": 0.2, "reason": reason
    }


class PaperReportTests(unittest.TestCase):
    def test_empty_account_does_not_claim_win_rate(self):
        account = empty_account()
        summary = metrics(account)
        self.assertIsNone(summary["win_rate"])
        self.assertEqual(summary["net"], 0)
        self.assertEqual(summary["drawdown"], 0)
        self.assertIn("N/A — no closed trades", markdown_report(account, {}))
        self.assertIn("No completed trades yet", html_report(account, {}))

    def test_realized_profit_and_drawdown(self):
        account = empty_account()
        account["trades"] = [
            trade("BTCUSDT", 12.0), trade("ETHUSDT", -6.0, "STOP")]
        account["cash"] = 506.0
        summary = metrics(account)
        self.assertEqual(summary["win_rate"], 50.0)
        self.assertEqual(summary["net"], 6.0)
        self.assertAlmostEqual(summary["drawdown"], 100 * 6.0 / 512.0)
        self.assertEqual(summary["markets"]["BTCUSDT"]["wins"], 1)

    def test_open_positions_do_not_get_fictitious_equity(self):
        account = empty_account()
        account["cash"] = 400
        account["positions"] = {"BTCUSDT": {"symbol": "BTCUSDT", "quantity": 1.0}}
        self.assertIn("Unavailable", equity_label(metrics(account)))
        self.assertIn("live prices", markdown_report(account, {}))

    def test_html_escapes_untrusted_trade_reason(self):
        account = empty_account()
        account["trades"] = [trade("BTCUSDT", 2, "<script>bad()</script>")]
        html = html_report(account, {})
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_snapshot_validates_version_and_cursor(self):
        account = empty_account()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runner.json"
            payload = {
                "runner_version": 1,
                "ledger": {"version": 1, "account": account},
                "cursors": {"BTCUSDT": 1791546300000}
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded, cursors = read_snapshot(path)
            self.assertEqual(loaded["cash"], 500)
            self.assertEqual(cursors["BTCUSDT"], 1791546300000)
            payload["cursors"]["BTCUSDT"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                read_snapshot(path)


if __name__ == "__main__":
    unittest.main()
