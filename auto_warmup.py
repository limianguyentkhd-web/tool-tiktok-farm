"""
Hệ thống Tự Động Nuôi Nick TikTok (Auto Warm-Up & Topic Training Engine)
Tác dụng:
1. Kích hoạt lại độ Trust cho các nick cũ (Gmail cũ / FB cũ) mới kéo về máy.
2. Định hình tệp đề xuất (Niche Training): Tự động tìm kiếm và xem video đúng chủ đề kênh (phim, thời trang, gia dụng).
3. Mô phỏng 100% thao tác ngón tay người thật: Lướt đường cong Bezier, thời gian xem ngẫu nhiên, thả tim, xem Live.
"""

import os
import sys
import time
import json
import random
import subprocess
from datetime import datetime
from typing import List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from device_manager import DeviceManager
from human_behavior import human_tap, human_swipe, human_double_tap_like, simulate_human_watch_time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOPICS_FILE = os.path.join(BASE_DIR, "channel_topics.json")

# Danh sách từ khóa tìm kiếm định hình tệp theo từng chủ đề
NICHE_KEYWORDS = {
    "phim": [
        "review phim", "phim chieu rap", "tom tat phim hay", "marvel avengers",
        "phim hanh dong", "chi tiet thu vi trong phim", "dien anh kinh dien"
    ],
    "thoi_trang": [
        "ootd douyin", "phoi do mua dong", "outfit di choi", "thoi trang nu",
        "bien hinh douyin", "phong cach han quoc", "set do dep"
    ],
    "gia_dung": [
        "do gia dung thong minh", "review do tien ich", "meo vat cuoc song",
        "do gia dung phong bep", "mon do nen mua", "san pham tiktok shop"
    ],
    "chung": [
        "tin hot hom nay", "video hai huoc", "cuoc song thu vi", "trending tiktok"
    ]
}


class AutoWarmupEngine:
    def __init__(self, port: str = "5037"):
        self.port = port
        self.dm = DeviceManager([port])
        self.topics_map = self._load_topics()

    def _load_topics(self):
        if os.path.isfile(TOPICS_FILE):
            try:
                with open(TOPICS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _adb(self, serial: str, args: list) -> subprocess.CompletedProcess:
        cmd = ["adb"]
        if self.port != "5037":
            cmd.extend(["-P", self.port])
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

    def wake_and_open_tiktok(self, serial: str):
        """Đánh thức màn hình và mở TikTok."""
        self._adb(serial, ["shell", "input", "keyevent", "224"])
        self._adb(serial, ["shell", "input", "keyevent", "82"])
        self._adb(serial, ["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(3.5)

    def warmup_for_you(self, serial: str, duration_minutes: int = 5):
        """
        Kịch bản 1: Lướt dạo Feed For You ngẫu nhiên
        - Xem video với độ dài ngẫu nhiên (lướt nhanh 2-3s, xem vừa 8-15s, xem kỹ 20-35s)
        - Thả tim ngẫu nhiên ~25%
        - Vuốt ngón tay Bezier
        """
        print(f"\n[{serial}] 🌾 Bắt đầu phiên Lướt Feed Tự Nhiên (Thời lượng: ~{duration_minutes} phút)...")
        self.wake_and_open_tiktok(serial)

        start_time = time.time()
        max_seconds = duration_minutes * 60
        count = 0

        while time.time() - start_time < max_seconds:
            count += 1
            watch_sec, action = simulate_human_watch_time()
            rem = int(max_seconds - (time.time() - start_time))
            print(f"  [{serial}] Video {count} ({action}) - Xem {watch_sec}s | Còn lại: {rem}s")
            time.sleep(watch_sec)

            # Xác suất thả tim tự nhiên
            if "Xem kỹ" in action and random.random() < 0.35:
                print(f"  [{serial}] ❤️  Thả tim video!")
                human_double_tap_like(serial, port=self.port)
                time.sleep(random.uniform(0.6, 1.2))

            # Vuốt lên video tiếp theo
            human_swipe(serial, direction="up", port=self.port)
            time.sleep(random.uniform(0.6, 1.5))

        print(f"[{serial}] ✅ Đã hoàn thành phiên lướt dạo For You ({count} video).")

    def warmup_by_topic(self, serial: str, topic: Optional[str] = None, num_searches: int = 2):
        """
        Kịch bản 2: Tìm kiếm và xem video ĐỊNH HÌNH CHỦ ĐỀ (Niche Training)
        - Vào ô tìm kiếm của TikTok
        - Gõ từ khóa thuộc đúng ngách của kênh (Review phim, OOTD, Gia dụng)
        - Xem 3-5 video của từ khóa đó -> Giúp thuật toán TikTok định hình kênh
        """
        if not topic:
            cfg = self.topics_map.get(serial, {})
            topic = cfg.get("chu_de", "phim")

        keywords = NICHE_KEYWORDS.get(topic, NICHE_KEYWORDS["chung"])
        selected_kws = random.sample(keywords, min(num_searches, len(keywords)))

        print(f"\n[{serial}] 🎯 Bắt đầu phiên Định Hình Tệp Chủ Đề: [{topic.upper()}]")
        print(f"[{serial}] 🔍 Các từ khóa sẽ tìm kiếm: {selected_kws}")
        self.wake_and_open_tiktok(serial)

        for kw in selected_kws:
            print(f"\n[{serial}] 🔎 Đang tìm kiếm từ khóa: '{kw}'...")
            # Bấm kính lúp tìm kiếm ở góc trên bên phải
            self._adb(serial, ["shell", "input", "tap", "990", "120"])
            time.sleep(2.0)

            # Nhập từ khóa qua ADBKeyboard hoặc adb input text
            clean_kw = kw.replace(" ", "%s")
            self._adb(serial, ["shell", "input", "text", clean_kw])
            time.sleep(1.0)
            self._adb(serial, ["shell", "input", "keyevent", "66"]) # Enter / Search
            time.sleep(3.5)

            # Chọn video đầu tiên trong kết quả tìm kiếm
            self._adb(serial, ["shell", "input", "tap", "300", "550"])
            time.sleep(2.0)

            # Lướt xem 3-4 video trong chuỗi tìm kiếm này
            for v in range(1, 4):
                w = random.randint(10, 22)
                print(f"  [{serial}] -> Đang xem video chủ đề '{kw}': {w}s...")
                time.sleep(w)
                if random.random() < 0.4:
                    human_double_tap_like(serial, port=self.port)
                    print(f"  [{serial}] ❤️  Thả tim tương tác đúng chủ đề!")
                human_swipe(serial, direction="up", port=self.port)
                time.sleep(1.2)

            # Thoát về trang chính
            self._adb(serial, ["shell", "input", "keyevent", "4"])
            time.sleep(1.0)
            self._adb(serial, ["shell", "input", "keyevent", "4"])
            time.sleep(1.5)

        print(f"[{serial}] ✅ Hoàn tất định hình tệp chủ đề [{topic.upper()}] cho kênh!")

    def run_batch_warmup(self, devices: List[str], duration_minutes: int = 5, mode: str = "both"):
        """
        Chạy nuôi đồng loạt hoặc tuần tự cho toàn bộ dàn máy:
        - mode='foryou': Chỉ lướt For You
        - mode='topic': Chỉ tìm kiếm định hình tệp chủ đề
        - mode='both': Kết hợp cả lướt For You lẫn tìm kiếm tệp
        """
        print(f"\n" + "="*65)
        print(f"🌾 BẮT ĐẦU CHIẾN DỊCH NUÔI NICK TOÀN DÀN ({len(devices)} MÁY)")
        print(f"⏱️  Thời lượng mỗi máy: ~{duration_minutes} phút | Chế độ: {mode.upper()}")
        print("="*65)

        for idx, serial in enumerate(devices, 1):
            print(f"\n>>> [MÁY {idx}/{len(devices)}] Serial: {serial} <<<")
            try:
                if mode in ["foryou", "both"]:
                    self.warmup_for_you(serial, duration_minutes=duration_minutes)
                if mode in ["topic", "both"]:
                    self.warmup_by_topic(serial, num_searches=1)
            except Exception as e:
                print(f"[-] Lỗi nuôi trên máy {serial}: {e}")

            if idx < len(devices):
                pause = random.randint(3, 8)
                print(f"[*] Nghỉ {pause}s chuyển sang máy tiếp theo...")
                time.sleep(pause)

        print(f"\n🎉 HOÀN THÀNH TOÀN BỘ CHIẾN DỊCH NUÔI NICK CHO {len(devices)} MÁY!")


def show_menu():
    engine = AutoWarmupEngine()
    dm = engine.dm
    devs = dm.refresh_devices()

    while True:
        print("\n" + "="*60)
        print("         HỆ THỐNG NUÔI NICK & ĐỊNH HÌNH TỆP TIKTOK         ")
        print(f"     (Đang kết nối: {len(devs)} máy | Cổng ADB: {dm.active_port})")
        print("="*60)
        print(" [1] 🌾 Nuôi TOÀN BỘ dàn máy (Lướt For You + Thả tim ngẫu nhiên)")
        print(" [2] 🎯 Định hình tệp chủ đề TOÀN BỘ dàn máy (Tìm kiếm & xem ngách)")
        print(" [3] 🔥 Nuôi Tổng Hợp (Lướt For You + Định hình chủ đề kết hợp)")
        print(" [4] 📱 Nuôi trên 1 máy cụ thể (Chỉ định)")
        print(" [0] Quay lại menu chính")
        print("="*60)

        choice = input("👉 Lựa chọn của bạn (0-4): ").strip()
        if choice == "1":
            mins = input("Nhập số phút nuôi mỗi máy (Mặc định: 3 phút): ").strip()
            duration = int(mins) if mins.isdigit() else 3
            engine.run_batch_warmup(devs, duration_minutes=duration, mode="foryou")
        elif choice == "2":
            engine.run_batch_warmup(devs, duration_minutes=2, mode="topic")
        elif choice == "3":
            mins = input("Nhập số phút nuôi mỗi máy (Mặc định: 5 phút): ").strip()
            duration = int(mins) if mins.isdigit() else 5
            engine.run_batch_warmup(devs, duration_minutes=duration, mode="both")
        elif choice == "4":
            for idx, d in enumerate(devs, 1):
                print(f"  {idx}. {d}")
            c = input(f"Chọn máy (1-{len(devs)}): ").strip()
            if c.isdigit() and 1 <= int(c) <= len(devs):
                chosen = devs[int(c)-1]
                mins = input("Nhập số phút nuôi (Mặc định: 3): ").strip()
                duration = int(mins) if mins.isdigit() else 3
                engine.warmup_for_you(chosen, duration_minutes=duration)
                engine.warmup_by_topic(chosen, num_searches=1)
        elif choice == "0":
            break


if __name__ == '__main__':
    show_menu()
