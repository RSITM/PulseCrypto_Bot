"""Offline checks for the independent PulseCrypto Telegram health monitor."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from health_monitor import (
    candle_issues, evaluate_live, load_state, parse_time,
    run, workflow_issues,
)

NOW = datetime(2026, 10, 9, 13, 0, tzinfo=timezone.utc)


def workflow_run(minutes_ago, conclusion="success"):
    started = NOW - timedelta(minutes=minutes_ago)
    return {
        "status": "completed",
        "conclusion": conclusion,
        "run_started_at": started.isoformat(),
    }


class HealthMonitorTests(unittest.TestCase):
    def test_recent_success_and_fresh_candles_are_healthy(self):
        self.assertEqual(workflow_issues("TRADING", [workflow_run(15)], NOW, 40), set())
        latest_open = int((NOW - timedelta(minutes=20)).timestamp() * 1000)
        self.assertEqual(candle_issues(
            {sym: latest_open for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}, NOW),
            set())

    def test_missing_success_and_recent_failure(self):
        result = workflow_issues("TRADING", [workflow_run(6, "failure")], NOW, 40)
        self.assertIn("TRADING_OVERDUE", result)
        self.assertIn("TRADING_FAILED", result)

    def test_latest_failure_with_older_good_run(self):
        result = workflow_issues(
            "BACKUP", [workflow_run(5, "failure"), workflow_run(25, "success")],
            NOW, 45)
        self.assertEqual(result, {"BACKUP_FAILED"})

    def test_overdue_success(self):
        self.assertEqual(
            workflow_issues("BACKUP", [workflow_run(60)], NOW, 45),
            {"BACKUP_OVERDUE"})

    def test_candles_stale_or_missing(self):
        old_open = int((NOW - timedelta(minutes=90)).timestamp() * 1000)
        self.assertEqual(candle_issues(
            {sym: old_open for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}, NOW),
            {"CANDLES_STALE"})
        self.assertEqual(candle_issues({}, NOW), {"CANDLES_STALE"})

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            parse_time("2026-10-09T13:00:00")

    def test_api_failure_captured_as_unavailable(self):
        latest_open = int((NOW - timedelta(minutes=20)).timestamp() * 1000)
        with patch("health_monitor.fetch_workflow_runs", side_effect=RuntimeError("offline")), patch(
            "health_monitor.fetch_cursors",
            return_value={sym: latest_open for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT")},
        ):
            result = evaluate_live("test-token", NOW)
        self.assertEqual(result, {"TRADING_UNAVAILABLE", "BACKUP_UNAVAILABLE"})

    def test_telegram_alert_sent_only_on_transition_and_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "health.json"
            with patch("health_monitor.evaluate_live", side_effect=[
                {"TRADING_OVERDUE"}, {"TRADING_OVERDUE"}, set(),
            ]), patch("health_monitor.send_telegram") as send:
                for _ in range(3):
                    run(path, now=NOW, token="mock", telegram_token="mock", chat_id="mock")
            self.assertEqual(send.call_count, 2)
            self.assertIn("Needs attention", send.call_args_list[0].args[0])
            self.assertIn("Recovered", send.call_args_list[1].args[0])
            self.assertEqual(load_state(path)["active"], [])

    def test_failed_telegram_does_not_suppress_next_alert(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "health.json"
            with patch("health_monitor.evaluate_live", return_value={"BACKUP_OVERDUE"}), patch(
                "health_monitor.send_telegram", side_effect=RuntimeError("failed")
            ):
                with self.assertRaises(RuntimeError):
                    run(path, now=NOW, token="mock", telegram_token="mock", chat_id="mock")
            self.assertFalse(path.exists())

    def test_dry_run_does_not_send_or_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "health.json"
            with patch("health_monitor.evaluate_live", return_value={"TRADING_OVERDUE"}), patch(
                "health_monitor.send_telegram"
            ) as send:
                run(path, dry_run=True, now=NOW, token="mock",
                    telegram_token="mock", chat_id="mock")
            send.assert_not_called()
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
