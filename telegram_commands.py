"""Secure, read-only Telegram command polling for PulseCrypto PAPER mode.

Driven by a separate scheduled workflow; only the configured private chat
is answered. Commands never modify paper trades, risk or configuration.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import requests

from telegram_command_reports import make_reply

MAX_COMMAND_AGE_SECONDS = 35 * 60


def read_offset(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or set(data) != {"version", "offset"}
            or data["version"] != 1 or type(data["offset"]) is not int
            or data["offset"] < 0):
        raise ValueError("Invalid Telegram command cursor")
    return data["offset"]


def write_offset(path, offset):
    if type(offset) is not int or offset < 0:
        raise ValueError("Invalid Telegram cursor offset")
    Path(path).write_text(
        json.dumps({"version": 1, "offset": offset}, indent=2) + "\n",
        encoding="utf-8")


def telegram(token, method, payload):
    if not token:
        raise RuntimeError("Telegram token missing")
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        if data.get("ok") is not True:
            raise RuntimeError("Telegram rejected command request")
        return data["result"]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        # HTTP exceptions may contain the bot token in the URL.
        raise RuntimeError("Telegram command API unavailable") from None


def get_updates(token, offset):
    result = telegram(token, "getUpdates", {
        "offset": offset, "limit": 100, "timeout": 0,
        "allowed_updates": ["message"]})
    if not isinstance(result, list):
        raise ValueError("Invalid Telegram update batch")
    return result


def reply(token, chat_id, message):
    if not isinstance(message, str) or not 0 < len(message) <= 4000:
        raise ValueError("Invalid Telegram reply text")
    telegram(token, "sendMessage", {
        "chat_id": chat_id, "text": message,
        "disable_web_page_preview": True})


def extract_command(text):
    if not isinstance(text, str):
        return None
    words = text.strip().lower().split()
    if not words or not words[0].startswith("/") or "@" in words[0]:
        return None
    return words[0]


def process_updates(updates, offset, chat_id, github_token, bot_token, now,
                    *, dry_run=False, send=reply, renderer=make_reply):
    """Process authorized recent messages; caller commits updated cursor."""
    if not isinstance(updates, list) or now.tzinfo is None:
        raise ValueError("Invalid updates or clock")
    try:
        authorized = int(chat_id)
    except (TypeError, ValueError):
        raise ValueError("Expected private chat ID") from None
    if authorized <= 0:
        raise ValueError("A private Telegram chat ID is required")
    processed = 0
    next_offset = offset
    for update in sorted(updates, key=lambda x: x.get("update_id", -1)):
        if not isinstance(update, dict) or type(update.get("update_id")) is not int:
            raise ValueError("Malformed Telegram update")
        update_id = update["update_id"]
        if update_id < next_offset:
            continue
        next_offset = update_id + 1
        msg = update.get("message")
        if not isinstance(msg, dict) or not isinstance(msg.get("chat"), dict):
            continue
        chat = msg["chat"]
        if (chat.get("type") != "private" or type(chat.get("id")) is not int
                or chat["id"] != authorized):
            continue
        timestamp = msg.get("date")
        if type(timestamp) is not int:
            continue
        age = now.timestamp() - timestamp
        if age < -60 or age > MAX_COMMAND_AGE_SECONDS:
            continue
        command = extract_command(msg.get("text"))
        if command is None:
            continue
        processed += 1
        if dry_run:
            continue
        try:
            response = renderer(command, github_token, now)
        except (RuntimeError, ValueError, KeyError, TypeError, OSError, OverflowError):
            response = "⚠️ PulseCrypto couldn't load that report. Try again later."
        send(bot_token, authorized, response)
    return next_offset, processed


def run(path, *, dry_run=False):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    github_token = os.environ.get("GITHUB_TOKEN")
    if not token or not chat_id or not github_token:
        raise RuntimeError("Required GitHub or Telegram credentials missing")
    offset = read_offset(path)
    updates = get_updates(token, offset)
    next_offset, count = process_updates(
        updates, offset, chat_id, github_token, token,
        datetime.now(timezone.utc), dry_run=dry_run)
    print(f"Telegram check: {len(updates)} update(s); {count} eligible command(s)")
    if dry_run:
        print("DRY RUN: no Telegram replies and no saved cursor changes")
        return
    if next_offset > offset:
        write_offset(path, next_offset)
    print("Command processing finished — paper trades were not modified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.state, dry_run=args.dry_run)
