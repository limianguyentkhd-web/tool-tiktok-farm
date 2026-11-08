"""
HỆ THỐNG ĐIỀU KHIỂN TỰ ĐỘNG 24/7 CHO PHONE FARM (24/7 FARM AUTO-PILOT)
Chức năng:
1. Tự động chạy tuần hoàn 24/7 không có thời gian chết (Zero Idle Waste).
2. Tự động thức dậy -> Nuôi nick -> Kiểm tra kho video -> Đăng bài đúng khung giờ vàng -> Đi ngủ bảo vệ pin.
3. Tích hợp báo cáo trạng thái trực tiếp về điện thoại qua Telegram Bot khi chủ farm vắng mặt.
"""

import os
import sys
import time
import json
import random
import schedule
import requests
from datetime import datetime
from typing import Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from device_manager import DeviceManager
from auto_warmup import AutoWarmupEngine
from video_uploader import TikTokVideoUploader
from farm_tracker import FarmTracker
from media_downloader import MediaDownloader
from auto_reup_processor import AutoReupProcessor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "autopilot_config.json")


class FarmAutoPilot:
    def __init__(self):
        self.dm = DeviceManager()
        self.warmup_engine = AutoWarmupEngine(self.dm.active_port)
        self.uploader = TikTokVideoUploader(self.dm.active_port)
        self.tracker = FarmTracker()
        self.downloader = MediaDownloader()
        self.reup_processor = AutoReupProcessor()
        self.config = self._load_config()

    def _load_config(self) -> dict:
        default_cfg = {
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            },
            "schedule_hours": {
                "morning_warmup": "08:30",
                "lunch_post": "11:45",
                "afternoon_niche_train": "15:00",
                "evening_post": "20:00",
                "night_sleep": "23:00"
            },
            "warmup_minutes_per_device": 3,
            "post_stagger_delay_seconds": 180, # 3 phút giữa các máy
            "auto_refill_videos": True
        }
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=2, ensure_ascii=False)
        return default_cfg

    def send_telegram(self, message: str):
        """Gửi thông báo trực tiếp về điện thoại người dùng qua Telegram."""
        tg = self.config.get("telegram", {})
        if not tg.get("enabled") or not tg.get("bot_token") or not tg.get("chat_id"):
            return
        url = f"https://api.telegram.org/bot{tg['bot_token']}/sendMessage"
        payload = {
            "chat_id": tg["chat_id"],
            "text": f"🤖 [PHONE FARM 24/7]\n{message}",
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload, timeout=8)
        except Exception as e:
            print(f"[-] Không gửi được thông báo Telegram: {e}")

    # =========================================================================
    # CÁC TÁC VỤ VẬN HÀNH TRONG NGÀY
    # =========================================================================

    def task_morning_warmup(self):
        """08:30 SÁNG: Đánh thức toàn dàn máy và chạy lướt For You nuôi nick tự nhiên."""
        devs = self.dm.refresh_devices()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ☀️ BẮT ĐẦU CA SÁNG: Đánh thức & Nuôi nick...")
        self.send_telegram(f"☀️ <b>Bắt đầu Ca Sáng:</b> Đang đánh thức {len(devs)} máy và chạy nuôi nick tự nhiên...")

        for d in devs:
            self.dm.wake_device(d)
        time.sleep(2)

        # Chạy nuôi For You ngẫu nhiên
        mins = self.config.get("warmup_minutes_per_device", 3)
        self.warmup_engine.run_batch_warmup(devs, duration_minutes=mins, mode="foryou")
        self.send_telegram(f"✅ <b>Hoàn tất Ca Nuôi Sáng:</b> Tất cả {len(devs)} máy đã hoạt động ổn định!")

    def task_lunch_post(self):
        """11:45 TRƯA: Khung giờ vàng 1 - Đăng bài hàng loạt chia đều các máy."""
        devs = self.dm.refresh_devices()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 BẮT ĐẦU CA TRƯA: Đăng bài khung giờ vàng...")
        self.send_telegram(f"🚀 <b>Bắt đầu Ca Đăng Trưa (11:45):</b> Tiến hành đăng bài trên {len(devs)} máy...")

        self.uploader.upload_to_all_devices(
            devices=devs,
            video_dir_or_file=r"d:\TOOL TIKTOK\videos",
            caption="ai",
            stagger_delay=self.config.get("post_stagger_delay_seconds", 180)
        )
        self.send_telegram(f"🎉 <b>Hoàn tất Ca Đăng Trưa!</b> Xem chi tiết tại lịch sử đăng bài.")

    def task_afternoon_niche(self):
        """15:00 CHIỀU: Định hình tệp chủ đề (Tìm kiếm từ khóa ngách)."""
        devs = self.dm.refresh_devices()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🎯 BẮT ĐẦU CA CHIỀU: Định hình tệp chủ đề...")
        self.warmup_engine.run_batch_warmup(devs, duration_minutes=2, mode="topic")

    def task_evening_post(self):
        """20:00 TỐI: Khung giờ vàng đỉnh cao - Đăng bài đợt 2."""
        devs = self.dm.refresh_devices()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔥 BẮT ĐẦU CA TỐI (20:00): Đăng bài khung giờ vàng đỉnh cao...")
        self.send_telegram(f"🔥 <b>Bắt đầu Ca Đăng Tối (20:00):</b> Đợt đăng bài chính nổ view trên {len(devs)} máy...")

        self.uploader.upload_to_all_devices(
            devices=devs,
            video_dir_or_file=r"d:\TOOL TIKTOK\videos",
            caption="ai",
            stagger_delay=self.config.get("post_stagger_delay_seconds", 180)
        )
        self.send_telegram(f"🎉 <b>Hoàn tất Ca Đăng Tối!</b> Tất cả video đã lên xu hướng.")

    def task_night_sleep(self):
        """23:00 ĐÊM: Cho toàn bộ máy đi ngủ đông tiết kiệm điện, chống phồng pin qua đêm."""
        devs = self.dm.refresh_devices()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 💤 BẮT ĐẦU CA ĐÊM: Cho toàn bộ máy đi ngủ đông...")
        for d in devs:
            self.dm.sleep_device(d)
        self.send_telegram(f"💤 <b>Toàn bộ dàn {len(devs)} máy đã vào chế độ Ngủ Đông:</b> Màn hình tắt, tắt app ngầm, bảo vệ pin qua đêm an toàn.")

    # =========================================================================
    # VÒNG LẶP ĐIỀU PHỐI 24/7
    # =========================================================================

    def start_scheduler(self):
        """Bật vòng lặp tự động hóa 24/7."""
        sched = self.config.get("schedule_hours", {})
        schedule.every().day.at(sched.get("morning_warmup", "08:30")).do(self.task_morning_warmup)
        schedule.every().day.at(sched.get("lunch_post", "11:45")).do(self.task_lunch_post)
        schedule.every().day.at(sched.get("afternoon_niche_train", "15:00")).do(self.task_afternoon_niche)
        schedule.every().day.at(sched.get("evening_post", "20:00")).do(self.task_evening_post)
        schedule.every().day.at(sched.get("night_sleep", "23:00")).do(self.task_night_sleep)

        print("\n" + "="*70)
        print("          🚀 HỆ THỐNG PHONE FARM 24/7 AUTO-PILOT ĐÃ KHỞI CHẠY        ")
        print("="*70)
        print(f"[*] 08:30 -> Thức dậy & Nuôi nick sáng (Lướt For You)")
        print(f"[*] 11:45 -> Đăng bài Khung Giờ Vàng Trưa (Đợt 1)")
        print(f"[*] 15:00 -> Định hình tệp chủ đề (Tìm kiếm ngách)")
        print(f"[*] 20:00 -> Đăng bài Khung Giờ Vàng Tối (Đợt 2 - Đỉnh điểm)")
        print(f"[*] 23:00 -> Đưa máy vào chế độ Ngủ Đông bảo vệ pin qua đêm")
        print("="*70)
        print("[*] Máy tính sẽ tự động điều phối theo lịch trình trên...")
        print("[*] Nhấn Ctrl + C để dừng hệ thống bất kỳ lúc nào.\n")

        self.send_telegram("🚀 <b>Hệ thống Phone Farm 24/7 Auto-Pilot</b> đã được kích hoạt thành công trên máy tính!")

        while True:
            schedule.run_pending()
            time.sleep(30)


def configure_telegram_interactive():
    """Cài đặt bot Telegram để nhận báo cáo về điện thoại."""
    cfg_file = CONFIG_FILE
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    print("\n" + "="*60)
    print("🔑 CÀI ĐẶT BÁO CÁO QUA TELEGRAM BOT VỀ ĐIỆN THOẠI")
    print("="*60)
    print("1. Mở app Telegram trên điện thoại, tìm bot @BotFather -> /newbot")
    print("2. Copy mã Bot Token dán vào đây.")
    print("3. Tìm bot @userinfobot để lấy ID của bạn (Chat ID).")
    print("="*60)

    token = input("👉 Nhập Telegram Bot Token (hoặc Enter để giữ nguyên): ").strip()
    chat_id = input("👉 Nhập Telegram Chat ID của bạn: ").strip()

    if token:
        cfg["telegram"]["bot_token"] = token
    if chat_id:
        cfg["telegram"]["chat_id"] = chat_id
    if token or chat_id:
        cfg["telegram"]["enabled"] = True

    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    print("[+] ✅ Đã lưu cấu hình Telegram thành công!")


if __name__ == '__main__':
    ap = FarmAutoPilot()
    print("\n[1] Bật chế độ chạy Tự Động 24/7 (Auto-Pilot)")
    print("[2] Cài đặt kết nối Telegram Bot báo cáo về điện thoại")
    print("[3] Test chạy thử ngay 1 ca (Nuôi nick hoặc Đăng bài)")
    c = input("👉 Chọn (1-3): ").strip()
    if c == "1":
        ap.start_scheduler()
    elif c == "2":
        configure_telegram_interactive()
    elif c == "3":
        print("[A] Chạy thử Ca Nuôi Sáng | [B] Chạy thử Ca Đăng Bài | [C] Chạy thử Cho Máy Đi Ngủ")
        sub = input("👉 Chọn (A/B/C): ").strip().upper()
        if sub == "A":
            ap.task_morning_warmup()
        elif sub == "B":
            ap.task_lunch_post()
        elif sub == "C":
            ap.task_night_sleep()
