import unittest
from paper_cycle import format_event

class PaperCycleTests(unittest.TestCase):
    def test_buy_explicitly_paper_only(self):
        msg = format_event({"symbol":"BTCUSDT","action":"PAPER_BUY",
                            "entry":100,"stop":95,"target":115})
        self.assertIn("PAPER BUY", msg)
        self.assertIn("no real order", msg)

    def test_sell_displays_net_pnl(self):
        msg = format_event({"symbol":"SOLUSDT","action":"PAPER_SELL",
                            "trade":{"exit":102,"net_pnl":-1.25,"reason":"STOP"}})
        self.assertIn("-1.25", msg)
        self.assertIn("SIMULATION ONLY", msg)

    def test_reject_unknown_event(self):
        with self.assertRaises(ValueError):
            format_event({"symbol":"BTCUSDT","action":"LIVE_BUY"})

if __name__ == "__main__":
    unittest.main()
