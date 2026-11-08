# -*- coding: utf-8 -*-
"""
Tự động đăng 2 video cho các máy 2, 3, 4, 5, 6 để đạt 3 video/kênh
"""
import sys
import os
import time
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

POST_JOBS = [
    {
        "name": "May_2", "port": "5037", "serial": "988a17344c564b5657",
        "videos": [
            (r"d:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids\may2_7690745570076825050.mp4", "Outfit mua thu nhe nhang #ootd #fashion #fyp"),
            (r"d:\TOOL TIKTOK\videos\ootd_douyin\ready_may2_ootd.mp4", "Style dao pho cuoi tuan cuc xinh #style #viral #xuhuong")
        ]
    },
    {
        "name": "May_3", "port": "5037", "serial": "ce01182188dbdcee0c",
        "videos": [
            (r"d:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids\may3_7700576071301859226.mp4", "Goi y phoi do di choi sieu xinh #ootdvietnam #viral"),
            (r"d:\TOOL TIKTOK\videos\ootd_douyin\ready_may3_ootd.mp4", "Outfit don gian ma cuon lam nha #fyp #trending")
        ]
    },
    {
        "name": "May_4", "port": "5037", "serial": "ce011821c38b263b05",
        "videos": [
            (r"d:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids\may4_clean.mp4", "Tone mau yeu thich cua tuan nay #outfitideas #ootd"),
            (r"d:\TOOL TIKTOK\videos\ootd_douyin\ready_may4_ootd.mp4", "Ngay moi tran day nang luong #styleinspo #fyp")
        ]
    },
    {
        "name": "May_5", "port": "5038", "serial": "ce011821c45dc4060c",
        "videos": [
            (r"d:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids\may5_7700174739202113458.mp4", "Phong cach nhe nhang ngay nang #ootdfashion #trending"),
            (r"d:\TOOL TIKTOK\videos\ootd_douyin\ready_may5_ootd.mp4", "Xinh xan moi ngay cung outfit nay #viral #xuhuong")
        ]
    },
    {
        "name": "May_6", "port": "5037", "serial": "ce031713ed1e10540d",
        "videos": [
            (r"d:\TOOL TIKTOK\videos\ready_avengers_doctor_doom.mp4", "Khoanh khac dinh cao trong phim #marvel #shorts #viral"),
            (r"d:\TOOL TIKTOK\videos\ready_wakanda_standard.mp4", "Cong nghe sieu dinh cao cua Wakanda #avengers #fyp")
        ]
    },
]

def adb_cmd(port: str, serial: str, args: list, timeout: int = 25):
    cmd = [ADB, "-P", port, "-s", serial] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=str(e))

def upload_one_video(port: str, serial: str, name: str, local_path: str, caption: str):
    if not os.path.exists(local_path):
        print(f"[{name}] ❌ Khong tim thay file: {local_path}")
        return False

    remote = f"/sdcard/DCIM/Camera/up_{int(time.time())}.mp4"
    print(f"[{name}] 📤 Dang day video {os.path.basename(local_path)}...")
    adb_cmd(port, serial, ["push", local_path, remote], timeout=40)
    adb_cmd(port, serial, ["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote}"])
    time.sleep(1.0)

    print(f"[{name}] 🎬 Tien trinh dang bai tren TikTok...")
    # Profile tab
    adb_cmd(port, serial, ["shell", "input", "tap", "900", "2070"])
    time.sleep(1.0)
    # Create button (+)
    adb_cmd(port, serial, ["shell", "input", "tap", "540", "2030"])
    time.sleep(2.0)
    # Upload album (bottom left)
    adb_cmd(port, serial, ["shell", "input", "tap", "90", "1980"])
    time.sleep(2.0)
    # Videos tab
    adb_cmd(port, serial, ["shell", "input", "tap", "370", "248"])
    time.sleep(1.0)
    # First video
    adb_cmd(port, serial, ["shell", "input", "tap", "180", "480"])
    time.sleep(1.0)
    # Next from gallery
    adb_cmd(port, serial, ["shell", "input", "tap", "799", "1994"])
    time.sleep(3.0)
    # Next in editor
    adb_cmd(port, serial, ["shell", "input", "tap", "796", "2011"])
    time.sleep(3.0)
    # Caption box
    adb_cmd(port, serial, ["shell", "input", "tap", "350", "400"])
    time.sleep(0.8)
    adb_cmd(port, serial, ["shell", "input", "text", caption.replace(" ", "%s")])
    time.sleep(1.0)
    adb_cmd(port, serial, ["shell", "input", "keyevent", "111"])
    time.sleep(0.8)
    # Post button
    adb_cmd(port, serial, ["shell", "input", "tap", "799", "1999"])
    print(f"[{name}] 🚀 Da bam Post!")
    time.sleep(6.0)
    # Back to profile
    adb_cmd(port, serial, ["shell", "input", "tap", "900", "2070"])
    time.sleep(2.0)
    print(f"[{name}] ✅ Dang video thanh cong!")
    return True

def run_all():
    for job in POST_JOBS:
        name = job["name"]
        port = job["port"]
        serial = job["serial"]
        print(f"\n==================================================")
        print(f"BẮT ĐẦU ĐĂNG 2 VIDEO CHO {name} ({serial})")
        print(f"==================================================")
        for idx, (v_path, cap) in enumerate(job["videos"]):
            print(f"\n--- {name}: Video {idx+1}/2 ---")
            upload_one_video(port, serial, name, v_path, cap)
            time.sleep(3.0)

if __name__ == "__main__":
    run_all()
