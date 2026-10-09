import unittest
from unittest.mock import Mock, patch
from market_data import get_prices


class MarketDataTests(unittest.TestCase):
    @patch("market_data.requests.Session")
    def test_prices(self, session_class):
        session = session_class.return_value.__enter__.return_value
        session.get.side_effect = [
            Mock(status_code=200, json=lambda: {"symbol": s, "price": p})
            for s, p in [("BTCUSDT", "65000"), ("ETHUSDT", "3000"), ("SOLUSDT", "150")]
        ]
        self.assertEqual(get_prices(), {"BTC": 65000.0, "ETH": 3000.0, "SOL": 150.0})
        self.assertEqual(session.get.call_count, 3)

    @patch("market_data.requests.Session")
    def test_bad_symbol(self, session_class):
        session = session_class.return_value.__enter__.return_value
        session.get.return_value.json.return_value = {"symbol": "WRONG", "price": "1"}
        with self.assertRaises(ValueError):
            get_prices()


if __name__ == "__main__":
    unittest.main()
