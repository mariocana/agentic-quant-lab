"""Alerts to the PM (you). Telegram if configured, stdout otherwise. Stdlib only."""
from __future__ import annotations

import json
import logging
import urllib.request

from hlbridge.config import settings

log = logging.getLogger(__name__)


def notify(text: str) -> None:
    s = settings()
    if not (s.telegram_token and s.telegram_chat_id):
        print(f"[PM] {text}")
        return
    url = f"https://api.telegram.org/bot{s.telegram_token}/sendMessage"
    body = json.dumps({"chat_id": s.telegram_chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:                    # noqa: BLE001
        log.error("telegram failed (%s); message was: %s", e, text)
        print(f"[PM] {text}")
