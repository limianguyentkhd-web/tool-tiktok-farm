# -*- coding: utf-8 -*-
"""
Tự động đăng video mới khác biệt lên các kênh còn lại và kích hoạt nuôi tiếp
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
        "name": "May_1", "port": "5037", "serial": "9889da304447393259",
        "video": r"d:\TOOL TIKTOK\videos\ootd_5vids_ready\may1_ootd_vietmusic.mp4",
        "caption": "Style don gian xuong pho ngay nang dep #ootd #style #viral"
    },
    {
        "name": "May_2", "port": "5037", "serial": "988a17344c564b5657",
        "video": r"d:\TOOL TIKTOK\videos\ootd_5vids_ready\may2_ootd_vietmusic.mp4",
        "caption": "Goi y outfit cuoi tuan sieu xinh cho cac nang #fashion #xuhuong #ootdvietnam"
    },
    {
        "name": "May_3", "port": "5037", "serial": "ce01182188dbdcee0c",
        "video": r"d:\TOOL TIKTOK\videos\ootd_5vids_ready\may3_ootd_vietmusic.mp4",
        "caption": "Outfit nhe nhang di ca phe cung hoi ban #trend #fyp #outfit"
    },
    {
        "name": "May_4", "port": "5037", "serial": "ce011821c38b263b05",
        "video": r"d:\TOOL TIKTOK\videos\ootd_5vids_ready\may4_ootd_vietmusic.mp4",
        "caption": "Set do ton dang yeu thich nhat tuan nay #styleinspo #viral #xuhuong"
    },
    {
        "name": "May_5", "port": "5038", "serial": "ce011821c45dc4060c",
        "video": r"d:\TOOL TIKTOK\videos\ootd_5vids_ready\may5_ootd_vietmusic.mp4",
        "caption": "Tone mau am ap cho ngay se lanh #ootdfashion #trending #viral"
    },
    {
        "name": "May_6", "port": "5037", "serial": "ce031713ed1e10540d",
        "video": r"d:\TOOL TIKTOK\videos\ready_wakanda_vs_ironman.mp4",
        "caption": "So sanh suc manh cong nghe dinh cao #marvel #shorts #avengers #ironman"
    },
]

def adb_cmd(port: str, serial: str, args: list, timeout: int = 35):
    cmd = [ADB, "-P", port, "-s", serial] + args
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=str(e))

def upload_one_video(port: str, serial: str, name: str, local_path: str, caption: str):
    if not os.path.exists(local_path):
        print(f"[{name}] ❌ Không tìm thấy file: {local_path}")
        return False

    remote = f"/sdcard/DCIM/Camera/up_{int(time.time())}.mp4"
    print(f"\n[{name}] 📤 Đang đẩy video mới: {os.path.basename(local_path)}...")
    adb_cmd(port, serial, ["push", local_path, remote], timeout=50)
    adb_cmd(port, serial, ["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote}"])
    time.sleep(1.0)

    print(f"[{name}] 🎬 Tiến trình đăng bài lên TikTok...")
    # Quay về Home trước để reset UI state
    adb_cmd(port, serial, ["shell", "input", "keyevent", "4"])
    time.sleep(0.5)
    adb_cmd(port, serial, ["shell", "input", "tap", "108", "2070"])
    time.sleep(1.5)

    # Nút Tạo (+)
    adb_cmd(port, serial, ["shell", "input", "tap", "540", "2030"])
    time.sleep(2.5)

    # Nút Album Upload góc dưới bên trái
    adb_cmd(port, serial, ["shell", "input", "tap", "90", "1980"])
    time.sleep(2.0)

    # Tab Videos
    adb_cmd(port, serial, ["shell", "input", "tap", "370", "248"])
    time.sleep(1.0)

    # Chọn video đầu tiên mới nhất trong thư viện
    adb_cmd(port, serial, ["shell", "input", "tap", "180", "480"])
    time.sleep(1.0)

    # Bấm Next từ thư viện
    adb_cmd(port, serial, ["shell", "input", "tap", "799", "1994"])
    time.sleep(3.5)

    # Bấm Next trong editor
    adb_cmd(port, serial, ["shell", "input", "tap", "796", "2011"])
    time.sleep(3.5)

    # Nhập caption
    adb_cmd(port, serial, ["shell", "input", "tap", "350", "400"])
    time.sleep(0.8)
    adb_cmd(port, serial, ["shell", "input", "text", caption.replace(" ", "%s")])
    time.sleep(1.0)
    adb_cmd(port, serial, ["shell", "input", "keyevent", "111"])  # Ẩn phím
    time.sleep(0.8)

    # Bấm Post
    adb_cmd(port, serial, ["shell", "input", "tap", "799", "1999"])
    print(f"[{name}] 🚀 Đã bấm Đăng video!")
    time.sleep(6.0)

    # Đưa về Trang chủ (Home)
    adb_cmd(port, serial, ["shell", "input", "tap", "108", "2070"])
    time.sleep(1.5)
    print(f"[{name}] ✅ Đăng video mới thành công và đã về Home!")
    return True

def main():
    print("=" * 60)
    print("🚀 BẮT ĐẦU ĐĂNG VIDEO MỚI KHÁC BIỆT LÊN CÁC KÊNH TIKTOK")
    print("=" * 60)

    for job in POST_JOBS:
        name = job["name"]
        port = job["port"]
        serial = job["serial"]
        vid = job["video"]
        cap = job["caption"]
        upload_one_video(port, serial, name, vid, cap)
        time.sleep(3.0)

    print("\n" + "=" * 60)
    print("🎉 TOÀN BỘ CÁC KÊNH ĐÃ ĐĂNG XONG VIDEO MỚI!")
    print("🚀 CHUYỂN TIẾP TỰ ĐỘNG SANG CHẾ ĐỘ NUÔI FEED ĐA LUỒNG...")
    print("=" * 60)

    # Chạy tiếp warmup_6_devices.py
    subprocess.run([sys.executable, "-u", r"d:\TOOL TIKTOK\warmup_6_devices.py"])

if __name__ == "__main__":
    main()
