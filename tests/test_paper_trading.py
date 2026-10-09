import unittest
from paper_trading import PaperAccount

class PaperTradingTests(unittest.TestCase):
    def account(self):
        a = PaperAccount()
        a.roll_day("2026-10-08")
        return a

    def test_initial_equity(self):
        a = self.account()
        self.assertAlmostEqual(a.equity({}), 500.0)

    def test_buy_and_sell_with_fees(self):
        a = self.account()
        self.assertEqual(a.open_long("BTCUSDT", 100, 95, 115), "PAPER_BUY")
        self.assertLess(a.cash, 500)
        self.assertEqual(a.close_long("BTCUSDT", 110), "PAPER_SELL")
        self.assertEqual(len(a.trades), 1)
        self.assertGreater(a.trades[0]["net_pnl"], 0)
        self.assertAlmostEqual(a.equity({}), a.cash)

    def test_unconfirmed_signal_does_not_trade(self):
        a = self.account()
        self.assertEqual(a.open_long("BTCUSDT", 100, 100, 110), "SKIP_INVALID_LEVELS")
        self.assertEqual(len(a.positions), 0)

    def test_position_limit(self):
        a = self.account()
        self.assertEqual(a.open_long("BTCUSDT", 100, 95, 115), "PAPER_BUY")
        self.assertEqual(a.open_long("BTCUSDT", 100, 95, 115), "SKIP_POSITION_LIMIT")
        self.assertEqual(a.open_long("ETHUSDT", 100, 95, 115), "PAPER_BUY")
        self.assertEqual(a.open_long("SOLUSDT", 100, 95, 115), "SKIP_POSITION_LIMIT")

    def test_conservative_stop_when_both_hit(self):
        a = self.account()
        a.open_long("BTCUSDT", 100, 95, 115)
        self.assertEqual(a.on_candle("BTCUSDT", 94, 120), "PAPER_SELL")
        self.assertEqual(a.trades[0]["reason"], "STOP")
        self.assertLess(a.trades[0]["net_pnl"], 0)

    def test_loss_limit_blocks_next_entry(self):
        a = self.account()
        a.daily_realized_pnl = -10
        self.assertEqual(a.open_long("BTCUSDT", 100, 95, 115), "SKIP_DAILY_LOSS_LIMIT")

    def test_roll_requires_marks_with_open_positions(self):
        a = self.account()
        a.open_long("BTCUSDT", 100, 95, 115)
        with self.assertRaises(ValueError):
            a.roll_day("2026-10-09")
        a.roll_day("2026-10-09", {"BTCUSDT": 100})
        self.assertEqual(a.session_day, "2026-10-09")

    def test_reject_invalid_prices(self):
        a = self.account()
        with self.assertRaises(ValueError):
            a.open_long("BTCUSDT", -1, 95, 115)
        with self.assertRaises(ValueError):
            a.on_candle("BTCUSDT", 110, 100)

if __name__ == "__main__":
    unittest.main()
