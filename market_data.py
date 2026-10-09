"""Read-only BTC, ETH and SOL spot price scanner (USD quotes)."""
import requests

SYMBOLS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
API_URL = "https://api.binance.us/api/v3/ticker/price"


def get_prices():
    """Fetch current indicative spot prices; no orders are placed."""
    prices = {}
    with requests.Session() as session:
        for coin, symbol in SYMBOLS.items():
            response = session.get(API_URL, params={"symbol": symbol}, timeout=15)
            response.raise_for_status()
            payload = response.json()
            if payload.get("symbol") != symbol:
                raise ValueError(f"Unexpected symbol response for {coin}")
            price = float(payload["price"])
            if not (0 < price < float("inf")):
                raise ValueError(f"Invalid price for {coin}")
            prices[coin] = price
    return prices


if __name__ == "__main__":
    for coin, price in get_prices().items():
        print(f"{coin}: ${price:,.2f}")
