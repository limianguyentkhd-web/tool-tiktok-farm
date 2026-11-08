# -*- coding: utf-8 -*-
"""
Module Quản lý Hồ sơ Tài khoản & Kênh Nguồn (Account & Profile Manager)
Đảm bảo mỗi máy có 1 kênh nguồn riêng, 1 kho video riêng, không bao giờ đăng trùng lặp.
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_JSON = os.path.join(BASE_DIR, "tai_khoan_farm.json")

class AccountProfileManager:
    def __init__(self, json_file: str = ACCOUNTS_JSON):
        self.json_file = json_file
        self.accounts: List[Dict] = []
        self.load_accounts()

    def load_accounts(self) -> List[Dict]:
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    self.accounts = json.load(f)
            except Exception as e:
                print(f"[!] Lỗi đọc {self.json_file}: {e}")
                self.accounts = []
        else:
            self.accounts = []
        return self.accounts

    def save_accounts(self) -> bool:
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[-] Lỗi lưu tài khoản: {e}")
            return False

    def get_by_serial(self, serial: str) -> Optional[Dict]:
        for acc in self.accounts:
            if acc.get("serial") == serial:
                return acc
        return None

    def upsert_account(self, profile: Dict):
        serial = profile.get("serial")
        for i, acc in enumerate(self.accounts):
            if acc.get("serial") == serial:
                self.accounts[i].update(profile)
                self.save_accounts()
                return
        self.accounts.append(profile)
        self.save_accounts()

    def update_post_success(self, serial: str, video_title: str, source_url: str):
        """Cập nhật trạng thái sau khi máy đăng video thành công."""
        acc = self.get_by_serial(serial)
        if acc:
            acc["total_posts"] = acc.get("total_posts", 0) + 1
            acc["last_posted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            acc["last_video_title"] = video_title
            acc["last_source_url"] = source_url
            acc["status"] = "Đã đăng xong"
            
            # Lưu lịch sử để không cào trùng
            posted_history = acc.setdefault("posted_history", [])
            if source_url and source_url not in posted_history:
                posted_history.append(source_url)
            self.save_accounts()

    def update_status(self, serial: str, status: str, note: str = ""):
        acc = self.get_by_serial(serial)
        if acc:
            acc["status"] = status
            if note:
                acc["note"] = note
            self.save_accounts()

    def is_source_already_posted(self, serial: str, source_url: str) -> bool:
        acc = self.get_by_serial(serial)
        if not acc:
            return False
        history = acc.get("posted_history", [])
        return source_url in history or acc.get("last_source_url") == source_url
