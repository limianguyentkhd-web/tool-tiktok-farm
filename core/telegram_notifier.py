# -*- coding: utf-8 -*-
"""
Tầng 3: Báo Cáo Từ Xa Qua Telegram (Remote Telegram Notifier)
Báo cáo khi đăng video thành công hoặc chụp ảnh gửi cảnh báo khi gặp sự cố nghiêm trọng.
"""

import os
import requests
from typing import Optional

class TelegramNotifier:
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_configured():
            return False
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"[-] Lỗi gửi Telegram message: {e}")
            return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        if not self.is_configured() or not os.path.exists(photo_path):
            return False
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": self.chat_id, "caption": caption, "parse_mode": "HTML"}
                resp = requests.post(url, data=data, files=files, timeout=20)
                return resp.status_code == 200
        except Exception as e:
            print(f"[-] Lỗi gửi ảnh Telegram: {e}")
            return False
