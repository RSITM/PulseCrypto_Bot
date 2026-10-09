"""Opt-in, append-only Turso backup of PulseCrypto's simulated runner ledger.

GitHub's paper-state branch remains the authoritative source until a separate,
verified migration. Does not submit real trades or modify the account.
"""
import argparse
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

from paper_runner import load_runner_state

TABLE = "pulsecrypto_paper_snapshots"


def pipeline_url(database_url):
    if not isinstance(database_url, str) or not database_url:
        raise ValueError("TURSO_DATABASE_URL is missing")
    parsed = urlparse(database_url.strip())
    if (parsed.scheme not in ("libsql", "https") or not parsed.hostname
            or not parsed.hostname.endswith(".turso.io") or parsed.username
            or parsed.password or parsed.port or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment):
        raise ValueError("TURSO_DATABASE_URL must be a Turso libsql:// database URL")
    return "https://" + parsed.hostname + "/v2/pipeline"


def execute(database_url, auth_token, sql, args=(), *, want_rows=False):
    """Execute one parameterized SQL statement over Hrana HTTP v2."""
    if not auth_token or not isinstance(auth_token, str):
        raise ValueError("TURSO_AUTH_TOKEN is missing")
    stmt = {
        "sql": sql,
        "args": [{"type": "text", "value": value} for value in args],
        "want_rows": want_rows,
    }
    if any(not isinstance(item, str) for item in args):
        raise ValueError("Only text query parameters are supported")
    try:
        response = requests.post(
            pipeline_url(database_url),
            headers={"Authorization": "Bearer " + auth_token,
                     "Content-Type": "application/json"},
            json={"baton": None, "requests": [
                {"type": "execute", "stmt": stmt}, {"type": "close"}]},
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()["results"][0]
        if result["type"] != "ok":
            raise RuntimeError("Turso SQL statement failed")
        output = result["response"]
        if output.get("type") != "execute":
            raise RuntimeError("Unexpected Turso response type")
        return output["result"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        # Do not echo request details, SQL, or credentials in CI logs.
        raise RuntimeError("Turso request or response failed") from None


def backup_state(state_file, database_url, auth_token):
    """Append a verified immutable snapshot; idempotent by SHA-256 content."""
    path = Path(state_file)
    # Fail closed on damaged state before sending anything to Turso.
    state = load_runner_state(path)
    raw = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    execute(database_url, auth_token, f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            sha256 TEXT PRIMARY KEY,
            snapshot_json TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(database_url, auth_token, f"""
        INSERT OR IGNORE INTO {TABLE} (sha256, snapshot_json, source)
        VALUES (?, ?, ?)
    """, (digest, raw, "github-paper-state"))
    result = execute(database_url, auth_token,
                     f"SELECT snapshot_json FROM {TABLE} WHERE sha256 = ?",
                     (digest,), want_rows=True)
    rows = result.get("rows", [])
    if len(rows) != 1 or len(rows[0]) != 1 or rows[0][0].get("type") != "text" or rows[0][0].get("value") != raw:
        raise RuntimeError("Turso backup verification failed")
    print("Turso backup verified (paper mode only)")
    print(f"Snapshot SHA-256: {digest}")
    print(f"Simulated cash: ${state.account.cash:.2f}")
    print(f"Open simulated positions: {len(state.account.positions)}")
    print(f"Closed simulated trades: {len(state.account.trades)}")
    return digest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="paper_state/runner.json")
    args = parser.parse_args()
    backup_state(args.state,
                 os.environ.get("TURSO_DATABASE_URL"),
                 os.environ.get("TURSO_AUTH_TOKEN"))
