# telegram_alert.py
import requests
from email_notifier import EmailNotifier

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


def send_email_alert(smtp_config, recipient, subject, message):
    email_notifier = EmailNotifier(
        smtp_server=smtp_config['server'],
        smtp_port=smtp_config['port'],
        username=smtp_config['username'],
        password=smtp_config['password']
    )
    return email_notifier.send_email(recipient, subject, message)
