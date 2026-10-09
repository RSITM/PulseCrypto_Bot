import unittest
from intelligence import analyze, ema, rsi, atr


class IntelligenceTests(unittest.TestCase):
    def test_constant_series(self):
        candles = [{"close": 100.0, "high": 100.0, "low": 100.0, "volume": 10.0} for _ in range(220)]
        result = analyze(candles)
        self.assertEqual(result["regime"], "NEUTRAL")
        self.assertAlmostEqual(result["rsi14"], 50)
        self.assertAlmostEqual(result["atr14"], 0)
        self.assertAlmostEqual(result["relative_volume"], 1)

    def test_rising_series(self):
        candles = [{"close": float(i), "high": float(i) + 1, "low": float(i) - 1, "volume": 10.0} for i in range(100, 320)]
        result = analyze(candles)
        self.assertEqual(result["regime"], "BULLISH")
        self.assertAlmostEqual(result["rsi14"], 100)
        self.assertGreater(result["atr14"], 0)

    def test_insufficient_history(self):
        with self.assertRaises(ValueError):
            analyze([])
        with self.assertRaises(ValueError):
            ema([1, 2], 20)
        with self.assertRaises(ValueError):
            rsi([1, 2], 14)
        with self.assertRaises(ValueError):
            atr([], 14)


if __name__ == "__main__":
    unittest.main()
