import os
import json
from urllib.request import urlopen, Request
from urllib.error import URLError


def send_telegram(message: str) -> None:
    tokens = [t.strip() for t in os.environ.get('TELEGRAM_BOT_TOKEN', '').split(',') if t.strip()]
    chat_ids = [c.strip() for c in os.environ.get('TELEGRAM_CHAT_ID', '').split(',') if c.strip()]
    for token, chat_id in zip(tokens, chat_ids):
        try:
            payload = json.dumps({
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML',
            }).encode()
            req = Request(
                f'https://api.telegram.org/bot{token}/sendMessage',
                data=payload,
                headers={'Content-Type': 'application/json'},
            )
            urlopen(req, timeout=5)
        except (URLError, Exception):
            pass
