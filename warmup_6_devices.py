# -*- coding: utf-8 -*-
"""
Hệ thống Tự Động Nuôi Nick TikTok Đa Thiết Bị (6 Máy Farm)
Chạy song song 6 luồng cho 6 thiết bị:
- May_1: 9889da304447393259 (Có Proxy)
- May_2: 988a17344c564b5657 (Có Proxy)
- May_3: ce01182188dbdcee0c (Có Proxy)
- May_4: ce011821c38b263b05 (Có Proxy)
- May_5: ce011821c45dc4060c (Có Proxy)
- May_6: ce031713ed1e10540d (Không Proxy - IP Gốc)

Lưu ý: Thiết bị ce031713dba2c72101 tuyệt đối không can thiệp (máy mẫu).
"""

import sys
import os
import time
import random
import threading
import subprocess
import signal

sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

TARGETS = [
    {"name": "May_1", "serial": "9889da304447393259", "has_proxy": True, "nick": "@hieunh.daily26"},
    {"name": "May_2", "serial": "988a17344c564b5657", "has_proxy": True, "nick": "@thuyhuyen.ootd26"},
    {"name": "May_3", "serial": "ce01182188dbdcee0c", "has_proxy": True, "nick": "@xuanlan.daily26"},
    {"name": "May_4", "serial": "ce011821c38b263b05", "has_proxy": True, "nick": "@bachvan.daily26"},
    {"name": "May_5", "serial": "ce011821c45dc4060c", "has_proxy": True, "nick": "@thuytrang.daily26"},
    {"name": "May_6", "serial": "ce031713ed1e10540d", "has_proxy": False, "nick": "@user2810657457111 (Trang Hoa)"},
]

STOP_EVENT = threading.Event()

def get_device_port_map():
    port_map = {}
    for p in ["5037", "5038", "5039"]:
        try:
            res = subprocess.run([ADB, "-P", p, "devices"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines():
                if "\tdevice" in line:
                    s = line.split("\t")[0].strip()
                    port_map[s] = p
        except Exception:
            pass
    return port_map

def run_adb(port: str, serial: str, args: list, timeout: int = 10) -> subprocess.CompletedProcess:
    cmd = [ADB, "-P", port, "-s", serial] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=str(e))

def human_swipe(port: str, serial: str):
    """Vuốt chuyển video mô phỏng ngón tay người thật với độ trễ và tọa độ ngẫu nhiên"""
    start_x = random.randint(480, 600)
    start_y = random.randint(1550, 1750)
    end_x = start_x + random.randint(-40, 40)
    end_y = random.randint(350, 520)
    duration = random.randint(220, 380)
    run_adb(port, serial, ["shell", "input", "swipe", str(start_x), str(start_y), str(end_x), str(end_y), str(duration)])

def human_tap(port: str, serial: str, x: int, y: int):
    jitter_x = x + random.randint(-6, 6)
    jitter_y = y + random.randint(-6, 6)
    duration = random.randint(80, 150)
    run_adb(port, serial, ["shell", "input", "swipe", str(jitter_x), str(jitter_y), str(jitter_x), str(jitter_y), str(duration)])

def human_double_tap_like(port: str, serial: str):
    cx = 540 + random.randint(-40, 40)
    cy = 1050 + random.randint(-40, 40)
    human_tap(port, serial, cx, cy)
    time.sleep(random.uniform(0.08, 0.15))
    human_tap(port, serial, cx, cy)

def check_and_dismiss_popups(port: str, serial: str, name: str):
    """Đóng các popup thông báo thường gặp trên TikTok và thoát màn hình Shop/Terms/Live nếu bị kẹt"""
    try:
        # Kiểm tra focus hiện tại
        focus_res = run_adb(port, serial, ["shell", "dumpsys", "window"], timeout=4).stdout
        if "SparkActivity" in focus_res:
            print(f"[{name}] ⚡ Phát hiện kẹt màn hình WebView/Shop Terms - Thoát về feed...", flush=True)
            run_adb(port, serial, ["shell", "input", "tap", "70", "180"])
            time.sleep(0.5)
            run_adb(port, serial, ["shell", "input", "keyevent", "4"])
            time.sleep(0.5)
            run_adb(port, serial, ["shell", "input", "tap", "108", "2070"])
            return

        if "LivePlayActivity" in focus_res:
            print(f"[{name}] ⚡ Đang ở màn hình Live - Thoát về For You feed...", flush=True)
            run_adb(port, serial, ["shell", "input", "keyevent", "4"])
            time.sleep(0.5)
            run_adb(port, serial, ["shell", "input", "tap", "108", "2070"])
            return

        run_adb(port, serial, ["shell", "uiautomator", "dump", "/sdcard/p_check.xml"], timeout=6)
        xml_str = run_adb(port, serial, ["shell", "cat", "/sdcard/p_check.xml"], timeout=4).stdout
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
                    human_tap(port, serial, cx, cy)
                    time.sleep(1.0)
                    return
        # Fallback check for contacts popup
        if "syncing your phone contacts" in xml_str.lower():
            print(f"[{name}] ⚡ Đóng popup Sync contacts tại (330, 1280)...", flush=True)
            human_tap(port, serial, 330, 1280)
            time.sleep(1.0)
    except Exception:
        pass

def ensure_proxy_status(port: str, serial: str, has_proxy: bool, name: str):
    if has_proxy:
        # Kiểm tra xem VPN đã bật chưa
        route = run_adb(port, serial, ["shell", "ip", "route"]).stdout
        if "tun" not in route:
            print(f"[{name}] 🌐 Kích hoạt v2rayNG Proxy cho {serial}...", flush=True)
            run_adb(port, serial, ["shell", "am", "start", "-n", "com.v2ray.ang/com.v2ray.ang.ui.MainActivity"])
            time.sleep(1.5)
            # Bấm FAB
            run_adb(port, serial, ["shell", "input", "tap", "964", "1925"])
            time.sleep(1.5)
            run_adb(port, serial, ["shell", "input", "tap", "750", "1350"])
            time.sleep(1.0)
        else:
            print(f"[{name}] [✓] Proxy VPN đang hoạt động!", flush=True)
    else:
        # Máy không proxy: Dừng v2rayNG
        print(f"[{name}] 🏠 Chạy IP Gốc (Không Proxy) - Đảm bảo v2rayNG tắt...", flush=True)
        run_adb(port, serial, ["shell", "am", "force-stop", "com.v2ray.ang"])

def wake_and_launch_tiktok(port: str, serial: str, name: str):
    run_adb(port, serial, ["shell", "input", "keyevent", "224"])
    run_adb(port, serial, ["shell", "input", "keyevent", "82"])
    time.sleep(0.5)
    run_adb(port, serial, ["shell", "am", "start", "-n", "com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity"])
    time.sleep(4.0)
    check_and_dismiss_popups(port, serial, name)

def worker_warmup(dev: dict, port: str, max_videos: int = 250):
    name = dev["name"]
    serial = dev["serial"]
    nick = dev["nick"]
    has_proxy = dev["has_proxy"]

    print(f"[{name}] 🚀 Bắt đầu nuôi nick {nick} trên {serial} (Port {port})...", flush=True)
    ensure_proxy_status(port, serial, has_proxy, name)
    wake_and_launch_tiktok(port, serial, name)

    video_count = 0
    while not STOP_EVENT.is_set() and video_count < max_videos:
        video_count += 1
        
        # Mô phỏng thời gian xem ngẫu nhiên
        rand = random.random()
        if rand < 0.20:
            watch_sec = random.uniform(3.5, 6.5)
            action = "Lướt nhanh"
        elif rand < 0.75:
            watch_sec = random.uniform(9.0, 18.0)
            action = "Xem vừa"
        else:
            watch_sec = random.uniform(22.0, 40.0)
            action = "Xem kỹ"

        print(f"[{name}] 🎬 Video #{video_count:03d} ({action}) - Đang xem {watch_sec:.1f}s...", flush=True)

        # Chờ thời gian xem
        elapsed = 0
        while elapsed < watch_sec and not STOP_EVENT.is_set():
            time.sleep(1)
            elapsed += 1

        if STOP_EVENT.is_set():
            break

        # Thả tim ngẫu nhiên
        if action == "Xem kỹ" and random.random() < 0.40:
            print(f"[{name}] ❤️ Thả tim video #{video_count:03d}!", flush=True)
            human_double_tap_like(port, serial)
            time.sleep(random.uniform(0.8, 1.5))
        elif action == "Xem vừa" and random.random() < 0.20:
            print(f"[{name}] ❤️ Thả tim video #{video_count:03d}!", flush=True)
            human_double_tap_like(port, serial)
            time.sleep(random.uniform(0.8, 1.5))

        # Đôi khi mở xem bình luận hoặc pause nhẹ
        if action == "Xem kỹ" and random.random() < 0.15:
            # Nhấp xem comment
            run_adb(port, serial, ["shell", "input", "tap", "980", "1430"])
            time.sleep(random.uniform(2.5, 4.5))
            # Đóng comment
            run_adb(port, serial, ["shell", "input", "tap", "980", "650"])
            time.sleep(0.5)

        # Định kỳ kiểm tra đóng popup
        if video_count % 8 == 0:
            check_and_dismiss_popups(port, serial, name)

        # Vuốt sang video tiếp theo
        human_swipe(port, serial)
        time.sleep(random.uniform(0.5, 1.2))

    print(f"[{name}] 🏁 Đã hoàn thành phiên nuôi ({video_count} videos).", flush=True)

def main():
    print("=" * 65)
    print("   HỆ THỐNG NUÔI NICK TIKTOK TỰ ĐỘNG - 6 MÁY SIMULTANEOUS   ")
    print("=" * 65)

    port_map = get_device_port_map()
    threads = []

    for dev in TARGETS:
        s = dev["serial"]
        p = port_map.get(s)
        if not p:
            print(f"[-] Không tìm thấy thiết bị {dev['name']} ({s}) trên các cổng ADB!", flush=True)
            continue
        
        t = threading.Thread(target=worker_warmup, args=(dev, p), daemon=True)
        threads.append(t)
        t.start()
        time.sleep(2.0)  # Giãn cách khởi động giữa các máy để tránh nghẽn

    print(f"\n[✓] Đã kích hoạt toàn bộ {len(threads)} máy! Đang chạy song song...")
    print("[*] Nhấn Ctrl+C để dừng an toàn.\n")

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Đang gửi tín hiệu dừng tới tất cả các luồng...")
        STOP_EVENT.set()
        for t in threads:
            t.join(timeout=3)
        print("[✓] Toàn bộ hệ thống đã dừng an toàn.")

if __name__ == "__main__":
    main()
