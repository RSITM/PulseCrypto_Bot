"""Offline tests for authorized Telegram command processing."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from telegram_commands import extract_command, process_updates, read_offset, write_offset

NOW = datetime(2026, 10, 9, 15, tzinfo=timezone.utc)


def event(n, command="/status", chat=123456, kind="private", age=2):
    return {"update_id": n, "message": {
        "date": int((NOW - timedelta(minutes=age)).timestamp()),
        "chat": {"type": kind, "id": chat}, "text": command,
    }}


class TelegramProcessingTests(unittest.TestCase):
    def test_restrict_to_authorized_private_chat(self):
        updates = [event(1, chat=99), event(2, kind="group"),
                   event(3, age=40), event(4, "hello"), event(5)]
        sent = []
        offset, count = process_updates(
            updates, 0, 123456, "github", "telegram", NOW,
            send=lambda *args: sent.append(args),
            renderer=lambda cmd, *_: cmd)
        self.assertEqual((offset, count), (6, 1))
        self.assertEqual(sent, [("telegram", 123456, "/status")])

    def test_dry_run_never_replies(self):
        sent = Mock()
        offset, count = process_updates(
            [event(2), event(3, "/help")], 0, 123456,
            "github", "telegram", NOW, send=sent, dry_run=True)
        self.assertEqual((offset, count), (4, 2))
        sent.assert_not_called()

    def test_older_updates_not_replayed(self):
        sent = Mock()
        offset, count = process_updates(
            [event(3), event(4)], 4, 123456, "github", "telegram",
            NOW, send=sent, renderer=lambda *_: "OK")
        self.assertEqual((offset, count), (5, 1))
        self.assertEqual(sent.call_count, 1)

    def test_command_parsing(self):
        self.assertIsNone(extract_command("/status@differentbot"))
        self.assertIsNone(extract_command("hello"))
        self.assertEqual(extract_command("/STATUS"), "/status")

    def test_cursor_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cursor.json"
            write_offset(path, 31)
            self.assertEqual(read_offset(path), 31)
            path.write_text('{"version":1,"offset":true}', encoding="utf-8")
            with self.assertRaises(ValueError):
                read_offset(path)


if __name__ == "__main__":
    unittest.main()
