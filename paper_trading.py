"""PulseCrypto V0.4: deterministic, long-only paper-trading ledger.

No broker API access, order placement, market fetching, or Telegram side effects.
Balances are in simulated USD. State is in memory until persistence is added.
"""
from dataclasses import dataclass, field
from datetime import date
from math import isfinite

ALLOWED = frozenset({"BTCUSDT", "ETHUSDT", "SOLUSDT"})

@dataclass
class Position:
    symbol: str
    quantity: float
    entry: float
    stop: float
    target: float
    entry_fee: float

@dataclass
class PaperAccount:
    cash: float = 500.0
    starting_equity: float = 500.0
    fee_rate: float = 0.0026  # conservative placeholder; not a Kraken fee quote
    slippage_rate: float = 0.001  # 0.10% adverse simulated slippage
    risk_fraction: float = 0.005  # 0.5% of starting equity per entry
    daily_loss_fraction: float = 0.02  # daily closed-loss cap based on day-start equity
    max_positions: int = 2
    positions: dict = field(default_factory=dict)
    trades: list = field(default_factory=list)
    session_day: str | None = None
    day_start_equity: float = 500.0
    daily_realized_pnl: float = 0.0

    def __post_init__(self):
        for val in (self.cash, self.starting_equity, self.day_start_equity):
            self._positive(val, "equity")
        for val in (self.fee_rate, self.slippage_rate, self.risk_fraction, self.daily_loss_fraction):
            if not isfinite(val) or val < 0:
                raise ValueError("Rates must be nonnegative and finite")
        if self.fee_rate >= 1 or self.slippage_rate >= 1 or self.risk_fraction <= 0 or self.max_positions < 1:
            raise ValueError("Invalid account settings")

    @staticmethod
    def _positive(value, label):
        if not isinstance(value, (float, int)) or not isfinite(value) or value <= 0:
            raise ValueError(f"{label} must be positive and finite")

    def roll_day(self, day: str, marks: dict | None = None):
        """Call at the start of a UTC session; caller supplies current marks if positions exist."""
        date.fromisoformat(day)
        if self.session_day is not None and day < self.session_day:
            raise ValueError("Cannot move session date backwards")
        if day != self.session_day:
            if self.positions and marks is None:
                raise ValueError("Current marks required to roll open positions")
            self.day_start_equity = self.equity(marks or {})
            self.daily_realized_pnl = 0.0
            self.session_day = day

    def equity(self, marks: dict):
        total = self.cash
        for symbol, pos in self.positions.items():
            if symbol not in marks:
                raise ValueError(f"Missing current mark for {symbol}")
            self._positive(marks[symbol], "mark")
            total += pos.quantity * marks[symbol] * (1 - self.fee_rate)
        return total

    def open_long(self, symbol: str, market_price: float, stop: float, target: float):
        """Return a reason string; only modifies account on a filled simulated BUY."""
        if symbol not in ALLOWED:
            raise ValueError("Unsupported symbol")
        for value, name in ((market_price, "price"), (stop, "stop"), (target, "target")):
            self._positive(value, name)
        fill = market_price * (1 + self.slippage_rate)
        if not stop < fill < target:
            return "SKIP_INVALID_LEVELS"
        if symbol in self.positions or len(self.positions) >= self.max_positions:
            return "SKIP_POSITION_LIMIT"
        if self.session_day is None:
            return "SKIP_NO_SESSION"
        if self.daily_realized_pnl <= -self.day_start_equity * self.daily_loss_fraction:
            return "SKIP_DAILY_LOSS_LIMIT"
        per_unit_risk = fill - stop + (fill + stop) * self.fee_rate
        risk_budget = self.starting_equity * self.risk_fraction
        qty_by_risk = risk_budget / per_unit_risk
        qty_by_cash = self.cash / (fill * (1 + self.fee_rate))
        quantity = min(qty_by_risk, qty_by_cash)
        if quantity <= 0 or not isfinite(quantity):
            return "SKIP_NO_CASH"
        notional = quantity * fill
        entry_fee = notional * self.fee_rate
        self.cash -= notional + entry_fee
        if abs(self.cash) < 1e-9:
            self.cash = 0.0
        self.positions[symbol] = Position(symbol, quantity, fill, stop, target, entry_fee)
        return "PAPER_BUY"

    def close_long(self, symbol: str, market_price: float, reason: str = "EXIT"):
        self._positive(market_price, "price")
        if symbol not in self.positions:
            return "SKIP_NO_POSITION"
        pos = self.positions.pop(symbol)
        fill = market_price * (1 - self.slippage_rate)
        proceeds = pos.quantity * fill
        exit_fee = proceeds * self.fee_rate
        pnl = proceeds - exit_fee - pos.quantity * pos.entry - pos.entry_fee
        self.cash += proceeds - exit_fee
        self.daily_realized_pnl += pnl
        self.trades.append({"symbol": symbol, "entry": pos.entry, "exit": fill,
                            "quantity": pos.quantity, "net_pnl": pnl, "reason": reason,
                            "entry_fee": pos.entry_fee, "exit_fee": exit_fee})
        return "PAPER_SELL"

    def on_candle(self, symbol: str, low: float, high: float):
        """Simulate stop/target execution. Stop wins when both touched in one candle.

        A gap below the stop is filled at the lower observed low as a conservative
        approximation. This is NOT a tick-accurate execution simulator.
        """
        self._positive(low, "low")
        self._positive(high, "high")
        if low > high:
            raise ValueError("Low cannot exceed high")
        pos = self.positions.get(symbol)
        if pos is None:
            return "NO_POSITION"
        if low <= pos.stop:
            return self.close_long(symbol, min(low, pos.stop), "STOP")
        if high >= pos.target:
            return self.close_long(symbol, pos.target, "TARGET")
        return "HOLD"
