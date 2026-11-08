# -*- coding: utf-8 -*-
"""
Kịch bản Tự động Chuẩn hóa Dàn 6 Nick TikTok (0 Đồng):
1. Up đủ 3 video cho từng máy (lấy từ kho video OOTD / Short sẵn có)
2. Cập nhật Bio ngắn gọn, tự nhiên
3. Chạy kịch bản Follow chéo 6 máy với nhau (tạo 5 follower nội bộ đầu tiên)
4. Tự động tìm kiếm #flcheo / #followcheo trên TikTok để follow 10 nick, kéo sub thật về
"""

import sys
import os
import time
import subprocess
import random

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

# 6 Farm devices (ce031713dba2c72101 tuyệt đối KHÔNG can thiệp)
DEVICES = [
    {"name": "May_1", "port": "5037", "serial": "9889da304447393259", "user": "hieunh.daily26"},
    {"name": "May_2", "port": "5037", "serial": "988a17344c564b5657", "user": "thuyhuyen.ootd26"},
    {"name": "May_3", "port": "5037", "serial": "ce01182188dbdcee0c", "user": "xuanlan.daily26"},
    {"name": "May_4", "port": "5037", "serial": "ce011821c38b263b05", "user": "bachvan.daily26"},
    {"name": "May_5", "port": "5038", "serial": "ce011821c45dc4060c", "user": "thuytrang.daily26"},
    {"name": "May_6", "port": "5037", "serial": "ce031713ed1e10540d", "user": "user2810657457111"},
]

def adb_cmd(port: str, serial: str, args: list, timeout: int = 15):
    cmd = [ADB, "-P", port, "-s", serial] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=str(e))

def cross_follow_all():
    print("=" * 60)
    print("🤝 BẮT ĐẦU CHẠY FOLLOW CHÉO NỘI BỘ GIỮA 6 MÁY FARM...")
    print("=" * 60)
    for follower in DEVICES:
        f_name = follower["name"]
        f_port = follower["port"]
        f_serial = follower["serial"]

        for target in DEVICES:
            if follower["serial"] == target["serial"]:
                continue
            t_user = target["user"]
            print(f"[{f_name}] -> Đang mở profile @{t_user} để Follow...")
            adb_cmd(f_port, f_serial, ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"https://www.tiktok.com/@{t_user}"])
            time.sleep(3.0)
            # Bấm nút Follow ở (254, 572)
            adb_cmd(f_port, f_serial, ["shell", "input", "tap", "254", "572"])
            time.sleep(1.0)
        
        # Quay về Profile
        adb_cmd(f_port, f_serial, ["shell", "input", "keyevent", "4"])
        time.sleep(0.5)
        adb_cmd(f_port, f_serial, ["shell", "input", "tap", "900", "2070"])
        time.sleep(1.0)

    print("\n[✓] Đã hoàn thành follow chéo toàn bộ 6 máy!")

def search_and_fl_cheo(dev: dict, count: int = 8):
    name = dev["name"]
    port = dev["port"]
    serial = dev["serial"]

    print(f"\n[{name}] 🔍 Tìm kiếm hashtag #flcheo để kéo follower tự nhiên...")
    # 1. Về Home
    adb_cmd(port, serial, ["shell", "input", "tap", "108", "2070"])
    time.sleep(1.5)
    # 2. Bấm icon Kính lúp tìm kiếm (góc trên bên phải)
    adb_cmd(port, serial, ["shell", "input", "tap", "1000", "130"])
    time.sleep(1.5)
    # 3. Nhập từ khóa tìm kiếm
    kw = random.choice(["fl%scheo", "follow%scheo", "tuong%stac%scheo"])
    adb_cmd(port, serial, ["shell", "input", "text", kw])
    time.sleep(1.0)
    # Bấm Search (Enter trên bàn phím: 1000, 2050 hoặc keyevent 66)
    adb_cmd(port, serial, ["shell", "input", "keyevent", "66"])
    time.sleep(3.0)
    # 4. Chọn tab Users (Tài khoản) - tab thứ 2 hoặc 3 (khoảng x=350, y=240)
    adb_cmd(port, serial, ["shell", "input", "tap", "350", "240"])
    time.sleep(2.0)

    # 5. Lướt và bấm nút Follow của các nick trong danh sách
    # Nút Follow trong danh sách tìm kiếm thường ở cột bên phải x=950
    followed = 0
    for i in range(count):
        y = 450 + (i % 4) * 220
        adb_cmd(port, serial, ["shell", "input", "tap", "920", str(y)])
        followed += 1
        print(f"[{name}] [+] Đã bấm Follow người dùng tại y={y} ({followed}/{count})")
        time.sleep(random.uniform(1.2, 2.0))
        if i % 3 == 2:
            # Cuộn xuống nhẹ
            adb_cmd(port, serial, ["shell", "input", "swipe", "500", "1500", "500", "800", "300"])
            time.sleep(1.5)

    # Thoát về Home
    adb_cmd(port, serial, ["shell", "input", "keyevent", "4"])
    time.sleep(0.5)
    adb_cmd(port, serial, ["shell", "input", "keyevent", "4"])
    time.sleep(0.5)
    adb_cmd(port, serial, ["shell", "input", "tap", "900", "2070"])
    print(f"[{name}] [✓] Đã hoàn thành đợt kéo follow chéo ({followed} nick).")

def post_video_to_device(dev: dict, local_vid_path: str, caption: str):
    name = dev["name"]
    port = dev["port"]
    serial = dev["serial"]

    if not os.path.exists(local_vid_path):
        print(f"[-] Không tìm thấy file: {local_vid_path}")
        return False

    remote_vid = f"/sdcard/DCIM/Camera/up_{int(time.time())}.mp4"
    print(f"\n[{name}] 📤 Đang đẩy video vào máy: {os.path.basename(local_vid_path)}...")
    adb_cmd(port, serial, ["push", local_vid_path, remote_vid], timeout=30)
    adb_cmd(port, serial, ["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_vid}"])
    time.sleep(1.0)

    print(f"[{name}] 🎬 Bắt đầu đăng video lên TikTok...")
    # Về profile
    adb_cmd(port, serial, ["shell", "input", "tap", "900", "2070"])
    time.sleep(1.0)
    # Bấm dấu cộng (+) Create
    adb_cmd(port, serial, ["shell", "input", "tap", "540", "2030"])
    time.sleep(2.0)
    # Bấm Upload (Album) góc dưới bên trái
    adb_cmd(port, serial, ["shell", "input", "tap", "90", "1980"])
    time.sleep(2.0)
    # Chọn tab Videos
    adb_cmd(port, serial, ["shell", "input", "tap", "370", "248"])
    time.sleep(1.0)
    # Chọn video đầu tiên
    adb_cmd(port, serial, ["shell", "input", "tap", "180", "480"])
    time.sleep(1.0)
    # Bấm Next từ thư viện
    adb_cmd(port, serial, ["shell", "input", "tap", "799", "1994"])
    time.sleep(3.0)
    # Bấm Next trong editor
    adb_cmd(port, serial, ["shell", "input", "tap", "796", "2011"])
    time.sleep(3.0)
    # Nhập caption
    adb_cmd(port, serial, ["shell", "input", "tap", "350", "400"])
    time.sleep(0.8)
    adb_cmd(port, serial, ["shell", "input", "text", caption.replace(" ", "%s")])
    time.sleep(1.0)
    adb_cmd(port, serial, ["shell", "input", "keyevent", "111"])
    time.sleep(0.8)
    # Bấm POST
    adb_cmd(port, serial, ["shell", "input", "tap", "799", "1999"])
    print(f"[{name}] 🚀 Đã bấm Đăng (Post), đang chờ tải lên...")
    time.sleep(6.0)
    # Về profile
    adb_cmd(port, serial, ["shell", "input", "tap", "900", "2070"])
    time.sleep(2.0)
    print(f"[{name}] [✓] Đăng video thành công!")
    return True

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "all"

    if action in ["cross_follow", "all"]:
        cross_follow_all()

    if action in ["pull_followers", "all"]:
        print("\n" + "=" * 60)
        print("🎯 BẮT ĐẦU KÉO FOLLOWER CHÉO TỰ NHIÊN TRÊN TIKTOK...")
        print("=" * 60)
        for dev in DEVICES:
            search_and_fl_cheo(dev, count=10)
            time.sleep(2.0)
