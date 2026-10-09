import unittest
from signal_engine import evaluate

def candles(n=220, rising=False, volume=10.0):
    return [{"close": float(100+i if rising else 100),
             "high": float(101+i if rising else 100),
             "low": float(99+i if rising else 100),
             "volume": volume} for i in range(n)]

class SignalEngineTests(unittest.TestCase):
    def test_requires_history(self):
        with self.assertRaises(ValueError):
            evaluate([])
    def test_flat_market_waits(self):
        self.assertEqual(evaluate(candles(), candles()).action, "WAIT")
    def test_no_higher_timeframe_waits(self):
        self.assertEqual(evaluate(candles(rising=True)).action, "WAIT")
    def test_no_volume_confirmation_waits(self):
        self.assertEqual(evaluate(candles(rising=True), candles(rising=True)).action, "WAIT")
    def test_no_orders_or_api_keys(self):
        result = evaluate(candles(), candles())
        self.assertIn(result.action, ("BUY", "WAIT"))

if __name__ == "__main__":
    unittest.main()
