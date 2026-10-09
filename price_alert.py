"""Send one read-only price snapshot to Telegram."""
from datetime import datetime, timezone
from main import send_alert
from market_data import get_prices


def format_snapshot(prices):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"PulseCrypto spot snapshot ({timestamp})", "Indicative USDT quotes (not trade signals):"]
    lines += [f"{coin}: {price:,.2f} USDT" for coin, price in prices.items()]
    return "\n".join(lines)


if __name__ == "__main__":
    send_alert(format_snapshot(get_prices()))
