# -*- coding: utf-8 -*-
"""
Hệ thống Tự Động Nuôi Nick TikTok Đa Thiết Bị (5 Máy Farm)
Chạy song song 5 luồng cho 5 thiết bị:
- May_1: 9889da304447393259 (Port 5038)
- May_2: 988a17344c564b5657 (Port 5038)
- May_3: ce01182188dbdcee0c (Port 5037)
- May_4: ce011821c38b263b05 (Port 5037)
- May_5: ce011821c45dc4060c (Port 5038)
Lưu ý: Thiết bị ce031713dba2c72101 tuyệt đối không can thiệp.
"""

import sys
import os
import time
import random
import threading
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

# Import các hàm tương tác mô phỏng người thật
from human_behavior import human_tap, human_swipe, human_double_tap_like, simulate_human_watch_time

TARGET_DEVICES = [
    {"name": "May_1", "port": "5038", "serial": "9889da304447393259"},
    {"name": "May_2", "port": "5038", "serial": "988a17344c564b5657"},
    {"name": "May_3", "port": "5037", "serial": "ce01182188dbdcee0c"},
    {"name": "May_4", "port": "5037", "serial": "ce011821c38b263b05"},
    {"name": "May_5", "port": "5038", "serial": "ce011821c45dc4060c"},
]

STOP_EVENT = threading.Event()

def run_adb(port: str, serial: str, args: list) -> subprocess.CompletedProcess:
    cmd = ["adb", "-P", port, "-s", serial] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

def check_and_dismiss_popups(port: str, serial: str, name: str):
    """Tự động phát hiện và đóng các thông báo chính sách, popup Got it, OK, Not now"""
    try:
        run_adb(port, serial, ["shell", "uiautomator", "dump", "/sdcard/p_check.xml"])
        xml_str = run_adb(port, serial, ["shell", "cat", "/sdcard/p_check.xml"]).stdout
        if not xml_str or "<hierarchy" not in xml_str:
            return
        import xml.etree.ElementTree as ET
        import re
        root = ET.fromstring(xml_str)
        target_texts = ["got it", "ok", "not now", "later", "agree", "đồng ý", "để sau", "bỏ qua", "allow", "don't allow", "don’t allow"]
        for elem in root.iter():
            txt = (elem.get("text", "") or elem.get("content-desc", "")).strip().lower()
            if any(t in txt for t in target_texts):
                bounds = elem.get("bounds", "")
                m = re.findall(r'\[(\d+),(\d+)\]', bounds)
                if len(m) == 2:
                    cx = (int(m[0][0]) + int(m[1][0])) // 2
                    cy = (int(m[0][1]) + int(m[1][1])) // 2
                    print(f"[{name}] ⚡ Đóng popup: '{txt}' tại ({cx}, {cy})", flush=True)
                    human_tap(serial, cx, cy, port=port)
                    time.sleep(1.0)
                    return
    except Exception:
        pass

def wake_and_launch_tiktok(port: str, serial: str, name: str):
    """Bật sáng màn hình và mở ứng dụng TikTok"""
    run_adb(port, serial, ["shell", "input", "keyevent", "224"])
    run_adb(port, serial, ["shell", "input", "keyevent", "82"])
    time.sleep(0.5)
    run_adb(port, serial, ["shell", "am", "start", "-n", "com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity"])
    time.sleep(4.0)
    check_and_dismiss_popups(port, serial, name)

def worker_warmup(dev: dict, max_videos: int = 100):
    name = dev["name"]
    port = dev["port"]
    serial = dev["serial"]

    print(f"[{name}] 🚀 Khởi động luồng nuôi nick TikTok trên {serial} (Port {port})...", flush=True)
    wake_and_launch_tiktok(port, serial, name)

    video_count = 0
    while not STOP_EVENT.is_set() and video_count < max_videos:
        video_count += 1
        watch_sec, action = simulate_human_watch_time()
        print(f"[{name}] 🎬 Video #{video_count:03d} ({action}) - Đang xem {watch_sec}s...", flush=True)

        # Chờ thời lượng xem video
        for _ in range(int(watch_sec)):
            if STOP_EVENT.is_set():
                break
            time.sleep(1)
        time.sleep(watch_sec - int(watch_sec))

        if STOP_EVENT.is_set():
            break

        # Tương tác tự nhiên: Thả tim ~25%
        if "Xem kỹ" in action and random.random() < 0.35:
            print(f"[{name}] ❤️ Thả tim video #{video_count:03d}!", flush=True)
            human_double_tap_like(serial, port=port)
            time.sleep(random.uniform(0.6, 1.2))

        # Đôi khi mở xem bình luận (10%)
        if random.random() < 0.10:
            print(f"[{name}] 💬 Mở xem bình luận...", flush=True)
            # Tọa độ nút bình luận bên phải màn hình
            human_tap(serial, 980, 1260, port=port)
            time.sleep(random.uniform(2.5, 4.5))
            # Cuộn xem comment
            human_swipe(serial, direction="up", port=port)
            time.sleep(random.uniform(1.5, 2.5))
            # Bấm back đóng comment
            run_adb(port, serial, ["shell", "input", "keyevent", "4"])
            time.sleep(random.uniform(0.8, 1.5))

        # Kiểm tra popup định kỳ mỗi 3 video
        if video_count % 3 == 0:
            check_and_dismiss_popups(port, serial, name)

        # Vuốt sang video tiếp theo bằng đường cong Bezier
        human_swipe(serial, direction="up", port=port)
        time.sleep(random.uniform(0.8, 2.0))

    print(f"[{name}] 🏁 Hoàn thành phiên nuôi nick ({video_count} video).", flush=True)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto Warmup 5 TikTok Devices")
    parser.add_argument("--videos", type=int, default=50, help="Số video mỗi máy lướt xem (mặc định 50)")
    args = parser.parse_args()

    print("=" * 65)
    print("🌾 HỆ THỐNG NUÔI NICK TIKTOK SONG SONG 5 MÁY (PHẦN CỨNG THẬT)")
    print(f"🎯 Mục tiêu: {args.videos} video / máy")
    print(f"📱 Danh sách máy: {[d['name'] + ' (' + d['serial'] + ')' for d in TARGET_DEVICES]}")
    print("=" * 65)

    threads = []
    for d in TARGET_DEVICES:
        t = threading.Thread(target=worker_warmup, args=(d, args.videos), daemon=True)
        threads.append(t)
        t.start()
        time.sleep(1.0) # Khởi động cách nhau 1s tránh nghẽn ADB

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n⚠️ Người dùng yêu cầu dừng nuôi nick!")
        STOP_EVENT.set()

    print("\n✅ ĐÃ HOÀN THÀNH TIẾN TRÌNH NUÔI NICK TRÊN CẢ 5 THIẾT BỊ!")

if __name__ == "__main__":
    main()
