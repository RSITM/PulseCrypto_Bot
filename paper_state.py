"""Versioned local JSON persistence for the *simulated* PulseCrypto account.

No exchange access or live orders. The runner must preserve this file between
GitHub Actions invocations; a fresh checkout alone is not persistent storage.
"""
import json
import math
import os
from pathlib import Path
import tempfile
from dataclasses import asdict, fields
from paper_trading import ALLOWED, PaperAccount, Position

VERSION = 1

def _number(value, *, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("State contains non-finite or non-numeric value")
    if nonnegative and value < 0:
        raise ValueError("Negative balance/quantity in state")
    return float(value)

def _validate(account):
    _number(account.cash, nonnegative=True)
    _number(account.starting_equity, nonnegative=True)
    if account.starting_equity <= 0 or account.max_positions < 1:
        raise ValueError("Invalid account configuration")
    if len(account.positions) > account.max_positions:
        raise ValueError("Too many positions")
    for symbol, p in account.positions.items():
        if symbol not in ALLOWED or p.symbol != symbol:
            raise ValueError("Invalid saved position symbol")
        for field_name in ("quantity", "entry", "stop", "target"):
            if _number(getattr(p, field_name), nonnegative=True) <= 0:
                raise ValueError("Invalid saved position price or quantity")
        _number(p.entry_fee, nonnegative=True)
        if not p.stop < p.entry < p.target:
            raise ValueError("Invalid saved risk levels")
    if not isinstance(account.trades, list):
        raise ValueError("Invalid trades")
    for trade in account.trades:
        if not isinstance(trade, dict) or trade.get("symbol") not in ALLOWED:
            raise ValueError("Invalid recorded trade")
        for name in ("entry", "exit", "quantity", "net_pnl", "entry_fee", "exit_fee"):
            _number(trade.get(name))
        if not isinstance(trade.get("reason"), str):
            raise ValueError("Invalid trade reason")
    if account.session_day is not None:
        from datetime import date
        if not isinstance(account.session_day, str):
            raise ValueError("Invalid session day")
        date.fromisoformat(account.session_day)

def serialize(account: PaperAccount) -> str:
    _validate(account)
    return json.dumps({"version": VERSION, "account": asdict(account)}, indent=2, sort_keys=True, allow_nan=False) + "\n"

def deserialize(raw: str) -> PaperAccount:
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("version") != VERSION:
        raise ValueError("Unknown paper state version")
    state = data.get("account")
    if not isinstance(state, dict):
        raise ValueError("Invalid paper account state")
    expected = {f.name for f in fields(PaperAccount)}
    if set(state) != expected:
        raise ValueError("State schema mismatch")
    positions = state["positions"]
    if not isinstance(positions, dict):
        raise ValueError("Invalid positions")
    expected_position = {f.name for f in fields(Position)}
    converted = {}
    for symbol, item in positions.items():
        if not isinstance(item, dict) or set(item) != expected_position:
            raise ValueError("Position schema mismatch")
        converted[symbol] = Position(**item)
    state = dict(state)
    state["positions"] = converted
    account = PaperAccount(**state)
    _validate(account)
    return account

def load(path="paper_state/account.json") -> PaperAccount:
    path = Path(path)
    if not path.exists():
        return PaperAccount()
    return deserialize(path.read_text(encoding="utf-8"))

def save(account: PaperAccount, path="paper_state/account.json") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize(account)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".paper-", suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
