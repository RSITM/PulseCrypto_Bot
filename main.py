
import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_alert(message):
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("Telegram credentials not configured")

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": message},
        timeout=15
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    send_alert("🚀 PulseCrypto is online! Telegram test successful.")
