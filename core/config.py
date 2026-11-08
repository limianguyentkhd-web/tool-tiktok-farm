# -*- coding: utf-8 -*-
"""
Module Quản lý Cấu hình Hệ thống (System Configuration)
Lưu trữ và đồng bộ cài đặt của Tool.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "adb_path": r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe",
    "adb_ports": ["5037", "5038", "5039"],
    "gemini_api_key": "",
    "gemini_model": "gemini-2.5-flash",
    "enable_ai_vision": True,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "enable_telegram": False,
    "auto_dismiss_popups": True,
    "action_timeout_seconds": 45,
    "max_retries_before_ai": 2,
    "human_swipe_min_ms": 300,
    "human_swipe_max_ms": 700
}

def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[!] Lỗi đọc config.json: {e}")
    else:
        save_config(config)
    return config

def save_config(config: dict) -> bool:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[-] Lỗi lưu config.json: {e}")
        return False
