"""V2 multi-timeframe SHADOW ONLY: deterministic, offline, zero order placement."""
import copy
import unittest

from intelligence import ema
from v2_shadow import (
    FIVE, FIFTEEN, HOUR, FOUR_HOURS, assess_depth, evaluate_v2
)

EVAL = (1_800_000_000_000 // FOUR_HOURS) * FOUR_HOURS


def series(step, values, vol=10.0):
    n = len(values)
    return [
        {"time": EVAL - (n - i) * step, "close": float(price),
         "high": float(price + 0.15), "low": float(price - 0.25),
         "volume": float(vol)}
        for i, price in enumerate(values)
    ]


def histories():
    high4 = series(FOUR_HOURS, [90 + i * 0.27 for i in range(65)])
    high1 = series(HOUR, [90 + i * 0.27 for i in range(65)])
    fifteen = series(FIFTEEN, [95 + i * 0.15 for i in range(69)] + [105.5])
    # A genuine previous-bar pullback to the computed 15m EMA20.
    support = ema([bar["close"] for bar in fifteen], 20)
    assert fifteen[-3]["close"] > support
    fifteen[-3]["low"] = support
    # A previous 15m high provides overhead structural target (not a current lookahead).
    fifteen[-9]["high"] = 110.0
    five = series(FIVE, [104.0] * 35 + [105.5])
    five[-1]["volume"] = 20.0
    return {"4h": high4, "1h": high1, "15m": fifteen, "5m": five}


def healthy_book():
    return {
        "timestamp_ms": EVAL - 500,
        "bids": [[105.50, 20.0], [105.49, 20.0]],
        "asks": [[105.51, 20.0], [105.52, 20.0], [105.53, 20.0]]
    }


class V2ShadowTests(unittest.TestCase):
    def test_full_multitimeframe_candidate_reachable_but_not_a_trade(self):
        decision = evaluate_v2("BTCUSDT", histories(), EVAL, healthy_book())
        self.assertEqual(decision.action, "CANDIDATE")
        self.assertEqual(decision.bias, "BULLISH_4H_1H")
        self.assertEqual(decision.setup, "15M_EMA20_PULLBACK")
        self.assertGreaterEqual(decision.reward_risk, 2)
        self.assertLess(decision.stop, decision.entry_reference)
        self.assertGreater(decision.target, decision.entry_reference)
        self.assertEqual(decision.to_dict()["mode"], "V2_SHADOW_RESEARCH_ONLY")
        self.assertNotIn("PAPER_BUY", str(decision.to_dict()))

    def test_no_orderbook_means_wait_even_with_perfect_price_chart(self):
        decision = evaluate_v2("BTCUSDT", histories(), EVAL)
        self.assertEqual(decision.action, "WAIT")
        self.assertIn("No contemporaneous", decision.reason)

    def test_future_and_stale_book_rejected(self):
        base = healthy_book()
        base["timestamp_ms"] = EVAL + 1
        self.assertIn("stale or future", evaluate_v2("BTCUSDT", histories(), EVAL, base).reason)
        base["timestamp_ms"] = EVAL - 10_001
        self.assertIn("stale or future", evaluate_v2("BTCUSDT", histories(), EVAL, base).reason)

    def test_excessive_spread_blocks_candidate(self):
        book = healthy_book()
        book["bids"][0][0] = 105.0
        book["bids"][1][0] = 104.99
        self.assertIn("spread too wide", evaluate_v2("BTCUSDT", histories(), EVAL, book).reason)

    def test_not_enough_visible_liquidity_blocks(self):
        book = healthy_book()
        book["asks"] = [[105.51, 0.2], [105.52, 0.2], [105.53, 0.2]]
        self.assertIn("Insufficient", evaluate_v2("BTCUSDT", histories(), EVAL, book).reason)

    def test_unsorted_and_crossed_orderbook_is_rejected(self):
        book = healthy_book()
        book["asks"][1][0] = book["asks"][0][0]
        self.assertIn("Invalid", evaluate_v2("BTCUSDT", histories(), EVAL, book).reason)
        book = healthy_book()
        book["bids"][0][0] = book["asks"][0][0] + 0.1
        self.assertIn("Invalid", evaluate_v2("BTCUSDT", histories(), EVAL, book).reason)

    def test_15m_pullback_missing_blocks(self):
        h = histories()
        h["15m"][-3]["low"] = h["15m"][-3]["close"] - 0.25
        result = evaluate_v2("BTCUSDT", h, EVAL, healthy_book())
        self.assertEqual(result.action, "WAIT")
        self.assertIn("15M", result.reason)

    def test_5m_breakout_missing_blocks(self):
        h = histories()
        h["5m"][-2]["high"] = 106.0
        result = evaluate_v2("BTCUSDT", h, EVAL, healthy_book())
        self.assertEqual(result.action, "WAIT")
        self.assertIn("5M structure", result.reason)

    def test_unconfirmed_hourly_trend_blocks(self):
        h = histories()
        h["1h"] = series(HOUR, [100.0] * 65)
        result = evaluate_v2("BTCUSDT", h, EVAL, healthy_book())
        self.assertEqual(result.action, "WAIT")
        self.assertEqual(result.bias, "NOT_BULLISH")

    def test_rejects_incomplete_current_candles_and_gaps(self):
        h = histories()
        h["5m"][-1]["time"] += FIVE
        with self.assertRaisesRegex(ValueError, "unclosed"):
            evaluate_v2("BTCUSDT", h, EVAL, healthy_book())
        h = histories()
        h["15m"][-2]["time"] -= FIFTEEN
        with self.assertRaisesRegex(ValueError, "nonchronological"):
            evaluate_v2("BTCUSDT", h, EVAL, healthy_book())

    def test_research_evaluation_does_not_modify_inputs(self):
        h = histories()
        book = healthy_book()
        h_orig = copy.deepcopy(h)
        book_orig = copy.deepcopy(book)
        evaluate_v2("BTCUSDT", h, EVAL, book)
        self.assertEqual(h, h_orig)
        self.assertEqual(book, book_orig)

    def test_book_sweep_calculates_vwap_and_price_impact(self):
        book = healthy_book()
        book["asks"] = [[105.51, 0.2], [106.0, 5.0], [107.0, 30.0]]
        # A larger book walk must show nonzero impact and trigger a rejection
        result = assess_depth(book, EVAL, 500.0)
        self.assertFalse(result.ok)
        self.assertGreater(result.buy_vwap, result.best_ask)
        self.assertGreater(result.impact_bps, 0)

    def test_unknown_symbol_and_missing_intervals_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            evaluate_v2("DOGEUSDT", histories(), EVAL, healthy_book())
        h = histories()
        del h["4h"]
        with self.assertRaisesRegex(ValueError, "complete"):
            evaluate_v2("BTCUSDT", h, EVAL, healthy_book())


if __name__ == "__main__":
    unittest.main()
