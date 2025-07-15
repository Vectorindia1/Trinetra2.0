# telegram_alert.py
import requests

def send_telegram_alert(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("❌ Telegram error:", response.text)
        return response.status_code == 200
    except Exception as e:
        print("❌ Telegram request failed:", e)
        return False
