"""Offline diagnostics: fixed candidate variants and chronology regression tests."""
import unittest
from unittest.mock import patch

from v2a_diagnostics import (
    VARIANTS, VARIANT_BY_NAME, breakout_retest, evaluate_variant,
    diagnose, report,
)
from v2a_backtest import simulate_v2a
from v2_shadow import FIVE, FOUR_HOURS, V2Decision, evaluate_v2_price_only
from test_v2_shadow import histories, EVAL
from test_v2a_backtest import dataset, stamp


def synthetic_trade(symbol, _frames, at):
    data = dataset()
    first_at = data["analysis_start_ms"] + FIVE
    if symbol == "BTCUSDT" and at == first_at:
        return V2Decision("CANDIDATE_PRICE_ONLY", "controlled stop test",
                          symbol, at, "BULLISH_4H_1H", "15M_EMA20_PULLBACK",
                          entry_reference=100, stop=99, target=103)
    return V2Decision("WAIT", "no setup", symbol, at)


class VariantRulesTests(unittest.TestCase):
    def test_fixed_variants_are_explicit_and_one_difference_each(self):
        self.assertEqual([v.name for v in VARIANTS], [
            "BASELINE_V2A", "ONE_HOUR_ONLY", "BREAKOUT_RETEST", "FIVE_MIN_2BAR"
        ])
        baseline = VARIANTS[0]
        self.assertEqual(VARIANTS[1].setup_mode, baseline.setup_mode)
        self.assertEqual(VARIANTS[1].five_break_bars, baseline.five_break_bars)
        self.assertEqual(VARIANTS[2].bias_mode, baseline.bias_mode)
        self.assertEqual(VARIANTS[2].five_break_bars, baseline.five_break_bars)
        self.assertEqual(VARIANTS[3].bias_mode, baseline.bias_mode)
        self.assertEqual(VARIANTS[3].setup_mode, baseline.setup_mode)

    def test_baseline_is_exact_original_candle_only_evaluator(self):
        h = histories()
        original = evaluate_v2_price_only("BTCUSDT", h, EVAL)
        diagnostic = evaluate_variant("BTCUSDT", h, EVAL, VARIANT_BY_NAME["BASELINE_V2A"])
        self.assertEqual(original, diagnostic)
        self.assertEqual(original.action, "CANDIDATE_PRICE_ONLY")

    def test_1h_only_passes_when_4h_is_flat(self):
        h = histories()
        h["4h"] = [
            {**bar, "close": 100.0, "high": 100.2, "low": 99.8}
            for bar in h["4h"]
        ]
        baseline = evaluate_variant("BTCUSDT", h, EVAL, VARIANT_BY_NAME["BASELINE_V2A"])
        single = evaluate_variant("BTCUSDT", h, EVAL, VARIANT_BY_NAME["ONE_HOUR_ONLY"])
        self.assertEqual(baseline.action, "WAIT")
        self.assertEqual(single.action, "CANDIDATE_PRICE_ONLY")
        self.assertEqual(single.bias, "BULLISH_1H_ONLY_RESEARCH")

    def test_5m_two_bar_trigger_when_3bar_does_not(self):
        h = histories()
        h["5m"][-4]["high"] = h["5m"][-1]["close"] + 0.5
        strict = evaluate_variant("BTCUSDT", h, EVAL, VARIANT_BY_NAME["BASELINE_V2A"])
        two = evaluate_variant("BTCUSDT", h, EVAL, VARIANT_BY_NAME["FIVE_MIN_2BAR"])
        self.assertEqual(strict.action, "WAIT")
        self.assertEqual(two.action, "CANDIDATE_PRICE_ONLY")

    def test_15m_breakout_retest_uses_prior_resistance_and_retest(self):
        fifteen = [
            {"close": 100.0, "high": 101.0, "low": 99.0, "volume": 10.0}
            for _ in range(40)
        ]
        fifteen[-6].update(close=102.0, high=102.5, low=100.5)
        fifteen[-4].update(close=101.2, high=101.6, low=101.0)
        fifteen[-2].update(close=102.0, high=102.2, low=101.6)
        fifteen[-1].update(close=103.0, high=103.2, low=102.0)
        self.assertTrue(breakout_retest(fifteen))
        fifteen[-4].update(close=99.0, high=101.6, low=97.0)
        self.assertFalse(breakout_retest(fifteen))

    def test_no_future_candles_accepted_by_any_variant(self):
        h = histories()
        h["1h"][-1]["time"] += 60 * 60_000
        for variant in VARIANTS:
            with self.subTest(variant=variant.name):
                with self.assertRaises(ValueError):
                    evaluate_variant("BTCUSDT", h, EVAL, variant)


class ForensicsAndWindowTests(unittest.TestCase):
    def test_stop_forensics_include_fees_and_hypothetical_overshoot(self):
        d = dataset()
        start = d["analysis_start_ms"]
        index = (start + FIVE - d["warmup_start_ms"]) // FIVE
        d["symbols"]["BTCUSDT"][index].update(
            {"open": 100.2, "high": 103.0, "low": 98.0, "close": 100.0}
        )
        result = simulate_v2a(d, synthetic_trade)
        self.assertEqual(result["closed_trades"], 1)
        record = result["trade_forensics"][0]
        self.assertEqual(record["symbol"], "BTCUSDT")
        self.assertEqual(record["entered_at_utc"], stamp(start + FIVE))
        self.assertEqual(record["next_bar_open"], 100.2)
        self.assertEqual(record["exit_reason"], "STOP")
        self.assertGreater(record["stop_overshoot_per_unit"], 0)
        self.assertGreater(record["fees_usd"], 0)
        self.assertLess(record["net_pnl_usd"],
                        record["stop_price_hypothetical_net_pnl_usd"])
        self.assertEqual(len(result["trade_forensics"]), 1)

    def test_valid_holdout_window_does_not_reuse_prior_open_positions(self):
        d = dataset()
        start, end = d["analysis_start_ms"], d["analysis_end_ms"]
        split = start + 4 * 24 * 60 * 60_000
        full = simulate_v2a(d, synthetic_trade)
        earlier = simulate_v2a(d, synthetic_trade, start_ms=start, end_ms=split)
        holdout = simulate_v2a(d, synthetic_trade, start_ms=split, end_ms=end)
        self.assertEqual(full["paper_entries"], 1)
        self.assertEqual(earlier["paper_entries"], 1)
        self.assertEqual(holdout["paper_entries"], 0)
        self.assertEqual(holdout["ending_marked_equity_usd"], 500)
        with self.assertRaisesRegex(ValueError, "chronological research subwindow"):
            simulate_v2a(d, synthetic_trade, start_ms=start + FIVE)

    def test_diagnostic_output_comparisons_keep_windows_fixed(self):
        d = dataset()
        stub = {
            "paper_entries": 0, "closed_trades": 0, "wins": 0, "losses": 0,
            "win_rate_pct": None, "profit_factor": None,
            "total_return_pct": 0.0, "net_realized_pnl_usd": 0.0,
            "closed_trade_fees_usd": 0.0, "max_drawdown_pct": 0.0,
            "open_positions": 0, "rejections": {}, "trade_forensics": [],
        }
        with patch("v2a_diagnostics.simulate_v2a", return_value=stub) as mocked:
            result = diagnose(d)
        self.assertEqual(len(result["variants"]), 4)
        self.assertEqual(mocked.call_count, 12)
        self.assertGreater(result["later_window"]["days"], 0)
        self.assertEqual(result["available_period"]["days"], 7)
        self.assertIn("UNAVAILABLE", result["limitations"][5].upper())
        rendered = report(result)
        self.assertIn("ONE_HOUR_ONLY", rendered)
        self.assertIn("untouched chronological holdout", rendered)


if __name__ == "__main__":
    unittest.main()
