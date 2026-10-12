"""TJR-INSPIRED public concept tests; never proprietary replication or orders."""
from datetime import datetime, timezone
from unittest.mock import patch
import unittest

from v2_shadow import FIVE, HOUR, FOUR_HOURS
from tjr_ict_shadow import (
    TJRScanner, VARIANT_BY_NAME, VARIANTS, Liquidity, ResearchSignal,
    candidate_sweep, fair_value_gap, order_block, execution_room,
    depth_gate_for_research, is_ny_window, true_range_atr,
)
from tjr_historical import (replay, make_entry, exit_price, mark_equity,
                            ORDER_EXPIRY_BARS, START_EQUITY)
from test_v2a_backtest import dataset

ASOF = int(datetime(2026, 9, 15, 16, tzinfo=timezone.utc).timestamp() * 1000)


def raw(t, open_price=100., high=100.5, low=99.5, close=100.):
    return {"time": t, "open": open_price, "high": high,
            "low": low, "close": close, "volume": 30.}


def frames(at=ASOF):
    five = [raw(t) for t in range(at - 60 * FIVE, at, FIVE)]
    def higher(step):
        end = at // step * step
        return [{"time": t, "high": 101., "low": 99., "close": 100., "volume": 300.}
                for t in range(end - 60 * step, end, step)]
    return five, higher(HOUR), higher(FOUR_HOURS)


def level(*_args, **_kwargs):
    return [Liquidity("PRIOR_CONFIRMED_POOL", 101.0, 99.0)]


class PublicLogicTests(unittest.TestCase):
    def test_variants_are_stable_and_research_only(self):
        self.assertEqual(len(VARIANTS), 6)
        self.assertEqual(len(set(x.name for x in VARIANTS)), len(VARIANTS))
        self.assertEqual(VARIANT_BY_NAME["CRYPTO_24H_FVG"].session, "ALL")
        self.assertEqual(VARIANT_BY_NAME["PUBLIC_NY_FVG"].session, "NY")

    def test_new_york_session_timezone_aware(self):
        self.assertTrue(is_ny_window(ASOF))
        self.assertFalse(is_ny_window(ASOF - 9 * HOUR))
        # Winter vs summer 09:30 ET both pass.
        winter = int(datetime(2026, 1, 15, 14, 35, tzinfo=timezone.utc).timestamp() * 1000)
        summer = int(datetime(2026, 7, 15, 13, 35, tzinfo=timezone.utc).timestamp() * 1000)
        self.assertTrue(is_ny_window(winter))
        self.assertTrue(is_ny_window(summer))

    def test_three_bar_fvg_and_last_opposing_order_block(self):
        rows, *_ = frames()
        rows[-3] = raw(rows[-3]["time"], high=101.0)
        rows[-2] = raw(rows[-2]["time"], open_price=101., close=100.)
        rows[-1] = raw(rows[-1]["time"], open_price=102., low=102.,
                       high=104., close=103.)
        atr = true_range_atr(rows)
        self.assertEqual(fair_value_gap(rows, "LONG", atr), (101., 102.))
        self.assertEqual(order_block(rows, "LONG", ASOF - 3*FIVE, ASOF),
                         (99.5, 100.5))

    def test_sweep_requires_close_back_inside_known_level(self):
        candles, h1, h4 = frames()
        with patch("tjr_ict_shadow.known_liquidity", level):
            candles[-1].update(open=100.4, low=98.6, high=100.7, close=100.)
            sweep = candidate_sweep(candles, h1, h4, ASOF)
            self.assertEqual(sweep["side"], "LONG")
            self.assertEqual(sweep["pool"], "PRIOR_CONFIRMED_POOL")
            candles[-1]["close"] = 98.0
            self.assertIsNone(candidate_sweep(candles, h1, h4, ASOF))
            candles[-1].update(open=99.8, low=99.5, high=101.4, close=100.0)
            sweep_short = candidate_sweep(candles, h1, h4, ASOF)
            self.assertEqual(sweep_short["side"], "THEORETICAL_SHORT")

    def test_sequential_sweep_shift_fvg_yields_only_research_limit(self):
        five, h1, h4 = frames()
        five[-1].update(open=100.4, low=98.6, high=100.7, close=100.)
        scanner = TJRScanner(VARIANT_BY_NAME["PUBLIC_NY_FVG"])
        with patch("tjr_ict_shadow.known_liquidity", level):
            start = scanner.on_closed_candle("BTCUSDT", five, h1, h4, ASOF)
            self.assertEqual(start.action, "SWEEP")
            next5 = five + [raw(ASOF, open_price=100.6, high=103.4,
                               low=101.2, close=103.0)]
            decision = scanner.on_closed_candle("BTCUSDT", next5, h1, h4, ASOF + FIVE)
            self.assertEqual(decision.action, "RESEARCH_LIMIT_ORDER")
            self.assertEqual(decision.side, "LONG")
            self.assertEqual(decision.zone_kind, "FVG")
            self.assertLess(decision.stop, decision.entry)
            self.assertGreater(decision.target, decision.entry)
            self.assertEqual(decision.to_dict()["mode"],
                             "TJR_PUBLIC_INSPIRED_PRICE_ONLY_RESEARCH")
            self.assertIsNone(scanner.state["BTCUSDT"])

    def test_order_block_and_equilibrium_variants(self):
        for name, wanted in [
            ("PUBLIC_NY_ORDER_BLOCK", "ORDER_BLOCK"),
            ("PUBLIC_NY_EQUILIBRIUM", "EQUILIBRIUM"),
        ]:
            with self.subTest(name=name):
                five, h1, h4 = frames()
                five[-1].update(open=100.4, low=98.6, high=100.7, close=100.)
                scanner = TJRScanner(VARIANT_BY_NAME[name])
                with patch("tjr_ict_shadow.known_liquidity", level):
                    self.assertEqual(scanner.on_closed_candle(
                        "BTCUSDT", five, h1, h4, ASOF).action, "SWEEP")
                    next5 = five + [raw(ASOF, open_price=100.6, high=103.4,
                                        low=101.2, close=103.0)]
                    decision = scanner.on_closed_candle(
                        "BTCUSDT", next5, h1, h4, ASOF + FIVE)
                self.assertEqual(decision.action, "RESEARCH_LIMIT_ORDER")
                self.assertEqual(decision.zone_kind, wanted)

    def test_missing_or_future_candle_fails_closed(self):
        five, h1, h4 = frames()
        scanner = TJRScanner(VARIANT_BY_NAME["CRYPTO_24H_FVG"])
        five[-5]["time"] += FIVE
        with self.assertRaisesRegex(ValueError, "gap"):
            scanner.on_closed_candle("BTCUSDT", five, h1, h4, ASOF)
        five, h1, h4 = frames()
        h4[-1]["time"] += FOUR_HOURS
        with self.assertRaises(ValueError):
            scanner.on_closed_candle("BTCUSDT", five, h1, h4, ASOF)

    def test_reward_after_cost_and_stop_rules(self):
        self.assertFalse(execution_room(100, 99, 100.5, "LONG", 1.33))
        self.assertTrue(execution_room(100, 98, 105, "LONG", 1.33))
        self.assertTrue(execution_room(100, 102, 95, "THEORETICAL_SHORT", 1.33))
        self.assertFalse(execution_room(100, 101, 100.5, "THEORETICAL_SHORT", 1.33))

    def test_forward_depth_is_never_an_historical_assumption(self):
        signal = ResearchSignal("RESEARCH_LIMIT_ORDER", "test", "BTCUSDT", ASOF,
                                side="LONG", entry=100, stop=98, target=105)
        self.assertFalse(depth_gate_for_research(signal, None, ASOF + 200_000)["accepted"])
        self.assertFalse(depth_gate_for_research(signal, None, ASOF + FIVE)["accepted"])
        short = ResearchSignal("RESEARCH_LIMIT_ORDER", "test", "BTCUSDT", ASOF,
                               side="THEORETICAL_SHORT", entry=100, stop=102, target=95)
        self.assertFalse(depth_gate_for_research(short, None, ASOF+30_000)["accepted"])


class HistoricalHypothesesTests(unittest.TestCase):
    def test_theoretical_long_and_short_sizing_no_margin_leverage(self):
        for side, stop, target in (("LONG", 98., 105.),
                                   ("THEORETICAL_SHORT", 102., 95.)):
            sig = ResearchSignal(
                "RESEARCH_LIMIT_ORDER", "test", "BTCUSDT", ASOF,
                side=side, zone_kind="FVG", swept_pool="TEST",
                entry=100, stop=stop, target=target
            )
            order = make_entry(sig, 500, 500, 100.)
            self.assertIsNotNone(order)
            self.assertLessEqual(order["qty"] * order["fill"], 500)
            self.assertGreater(order["qty"], 0)

    def test_stops_prioritized_when_target_and_stop_touched(self):
        sig = ResearchSignal(
            "RESEARCH_LIMIT_ORDER", "test", "BTCUSDT", ASOF,
            side="LONG", entry=100., stop=99., target=104.)
        order = make_entry(sig, 500, 500, 100.)
        self.assertEqual(exit_price(raw(ASOF, high=105, low=98), order)[1], "STOP")
        self.assertEqual(exit_price(raw(ASOF, high=105, low=99.5),
                                    order, allow_target=False)[1], None)
        short = ResearchSignal(
            "RESEARCH_LIMIT_ORDER", "test", "BTCUSDT", ASOF,
            side="THEORETICAL_SHORT", entry=100., stop=101., target=96.)
        theoretical = make_entry(short, 500, 500, 100.)
        self.assertEqual(exit_price(raw(ASOF, high=102, low=95), theoretical)[1],
                         "STOP")

    def test_market_positions_never_change_user_account(self):
        self.assertEqual(mark_equity(START_EQUITY, {}, {}), START_EQUITY)

    def test_historical_flat_data_zero_entries(self):
        d = dataset(7)
        result = replay(d, VARIANT_BY_NAME["CRYPTO_24H_FVG"])
        self.assertEqual(result["closed_trades"], 0)
        self.assertEqual(result["entries"], 0)
        self.assertEqual(result["marked_equity_usd"], 500.0)

    def test_next_candle_limit_order_and_same_bar_conservative_stop(self):
        d = dataset(7)
        started = d["analysis_start_ms"]
        fill_index = (started + FIVE - d["warmup_start_ms"]) // FIVE
        d["symbols"]["BTCUSDT"][fill_index].update(
            open=100., low=98., high=105., close=100.)
        sig = ResearchSignal(
            "RESEARCH_LIMIT_ORDER", "synthetic test", "BTCUSDT",
            started + FIVE, side="LONG", zone_kind="FVG",
            swept_pool="FIXTURE", entry=100., stop=99., target=104.)
        class OnlyOnce:
            def __init__(self, variant): self.variant = variant
            def on_closed_candle(self, symbol, five, h1, h4, as_of):
                if symbol == "BTCUSDT" and as_of == started + FIVE:
                    return sig
                return ResearchSignal("WAIT", "no signal", symbol, as_of)
        with patch("tjr_historical.TJRScanner", OnlyOnce):
            result = replay(d, VARIANT_BY_NAME["CRYPTO_24H_FVG"])
        self.assertEqual(result["entries"], 1)
        self.assertEqual(result["closed_trades"], 1)
        self.assertEqual(result["trades"][0]["exit_reason"], "ENTRY_BAR_STOP_CONSERVATIVE")
        self.assertLess(result["net_realized_pnl_usd"], 0)
        self.assertEqual(result["trades"][0]["signal_at_utc"],
                         "2026-09-08 00:05 UTC")

    def test_expiring_unfilled_limit_does_not_become_market_trade(self):
        d = dataset(7)
        started = d["analysis_start_ms"]
        sig = ResearchSignal(
            "RESEARCH_LIMIT_ORDER", "test", "BTCUSDT",
            started + FIVE, side="LONG", zone_kind="FVG",
            entry=95., stop=94., target=105.)
        class OnlyOnce:
            def __init__(self, variant): self.variant = variant
            def on_closed_candle(self, symbol, five, h1, h4, as_of):
                return sig if symbol == "BTCUSDT" and as_of == started + FIVE else (
                    ResearchSignal("WAIT", "none", symbol, as_of))
        with patch("tjr_historical.TJRScanner", OnlyOnce):
            result = replay(d, VARIANT_BY_NAME["CRYPTO_24H_FVG"])
        self.assertEqual(result["entries"], 0)
        self.assertEqual(result["closed_trades"], 0)
        self.assertGreater(result["decisions"].get("PENDING_EXPIRED", 0), 0)


if __name__ == "__main__":
    unittest.main()
