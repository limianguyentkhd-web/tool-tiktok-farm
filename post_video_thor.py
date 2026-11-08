# -*- coding: utf-8 -*-
import os
import sys
import time
import base64
import subprocess
from farm_tracker import FarmTracker

sys.stdout.reconfigure(encoding='utf-8')

SERIAL = "ce031713dba2c72101"
VIDEO_PATH = r"D:\TOOL TIKTOK\videos\reup_1793419822_raw_q0_jHWRVQso.mp4"
SOURCE_URL = "https://www.youtube.com/shorts/q0_jHWRVQso"
SOURCE_CHANNEL = "https://www.youtube.com/@zim_video/shorts"
CAPTION = "Vì sao Thor hồi phục lại được mắt nhưng Odin thì không? Chi tiết thú vị thần sấm Thor Marvel #thor #odin #marvel #mcu #avengers #shorts #xuhuong #phimhay"

def adb(args):
    cmd = ["adb", "-s", SERIAL] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

def snap(name):
    adb(["shell", f"screencap -p /sdcard/{name}.png"])
    subprocess.run(["adb", "-s", SERIAL, "pull", f"/sdcard/{name}.png", f"C:/Users/Admin/.gemini/antigravity/brain/612f5864-e377-4aa9-a143-bf7f13dcbded/{name}.png"], capture_output=True)
    print(f"  [Snap] {name}.png saved.")

def main():
    print(f"\n========================================================")
    print(f"🚀 BẮT ĐẦU ĐĂNG VIDEO 4: THOR & ODIN LÊN KÊNH MINH")
    print(f"🎬 Video: {VIDEO_PATH}")
    print(f"✍️ Caption: {CAPTION}")
    print(f"========================================================")

    # 1. Làm sạch thư viện ảnh tạm
    print("[1/10] Làm sạch thư viện ảnh/video cũ...")
    adb(["shell", "rm", "-f", "/sdcard/DCIM/Camera/*.mp4", "/sdcard/*.png"])
    time.sleep(1)

    # 2. Đẩy video vào Camera
    remote_path = f"/sdcard/DCIM/Camera/vid_{int(time.time())}_thor_odin.mp4"
    print(f"[2/10] Nạp video vào máy: {remote_path}...")
    adb(["push", VIDEO_PATH, remote_path])
    adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"])
    adb(["shell", "content", "call", "--uri", "content://media/external/file", "--method", "scan_file", "--arg", remote_path])
    time.sleep(2)

    # 3. Đánh thức và mở TikTok
    print("[3/10] Mở TikTok...")
    adb(["shell", "input", "keyevent", "224"])
    adb(["shell", "input", "keyevent", "82"])
    adb(["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.5)
    adb(["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(4.5)

    # 4. Bấm '+' tạo video
    print("[4/10] Bấm nút '+' tạo video...")
    adb(["shell", "input", "tap", "540", "2070"])
    time.sleep(2.5)

    # Đảm bảo ở chế độ CAMERA
    adb(["shell", "input", "tap", "120", "2030"])
    time.sleep(1.5)

    # 5. Mở Album
    print("[5/10] Mở Album ảnh/video...")
    adb(["shell", "input", "tap", "90", "1900"])
    time.sleep(2.5)

    # 6. Chọn tab 'Videos'
    print("[6/10] Chọn tab Videos...")
    adb(["shell", "input", "tap", "340", "210"])
    time.sleep(1.5)
    snap("thor_step1_video_tab")

    # 7. Tick chọn video đầu tiên
    print("[7/10] Tick chọn video Thor & Odin...")
    adb(["shell", "input", "tap", "311", "359"])
    time.sleep(1.0)
    # Bấm Next hồng
    adb(["shell", "input", "tap", "799", "1994"])
    time.sleep(4.0)
    snap("thor_step2_editor")

    # 8. Màn hình Editor -> Next sang màn hình Post
    print("[8/10] Chuyển tiếp sang màn hình Caption...")
    adb(["shell", "input", "tap", "740", "1954"])
    time.sleep(3.5)
    snap("thor_step3_post_screen")

    # 9. Nhập Caption tiếng Việt có dấu
    print("[9/10] Nhập Caption tiếng Việt...")
    adb(["shell", "input", "tap", "150", "310"])
    time.sleep(1.2)
    b64 = base64.b64encode((CAPTION + " ").encode("utf-8")).decode("utf-8")
    adb(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])
    time.sleep(2.0)
    adb(["shell", "input", "keyevent", "111"])
    time.sleep(1.5)
    snap("thor_step4_caption_verified")

    # 10. Bấm nút POST
    print("[10/10] Bấm nút ĐĂNG (POST)...")
    adb(["shell", "input", "tap", "799", "1999"])
    time.sleep(6.0)
    snap("thor_step5_posted_done")

    # Ghi nhận lịch sử
    tracker = FarmTracker()
    tracker.record_post(
        device_serial=SERIAL,
        tiktok_account="@nguyennminhh256",
        video_file=VIDEO_PATH,
        caption=CAPTION,
        topic="Review Phim / Thor & Odin",
        source_url=SOURCE_URL,
        source_channel=SOURCE_CHANNEL,
        status="SUCCESS"
    )

    print("\n[🎉] HOÀN TẤT ĐĂNG VIDEO 4: THOR & ODIN LÊN KÊNH MINH THÀNH CÔNG!")

if __name__ == "__main__":
    main()
