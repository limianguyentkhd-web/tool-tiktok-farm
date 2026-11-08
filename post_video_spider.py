# -*- coding: utf-8 -*-
import os
import sys
import time
import base64
import subprocess
from farm_tracker import FarmTracker

sys.stdout.reconfigure(encoding='utf-8')

PORT = "5038"
SERIAL = "ce031713dba2c72101"
VIDEO_PATH = r"D:\TOOL TIKTOK\videos\reup_1793352953_nhen_tom_holland_buff_suc_manh.mp4"
SOURCE_URL = "https://www.youtube.com/shorts/2mUol5uHjPA"
SOURCE_CHANNEL = "https://www.youtube.com/@zim_video/shorts"
CAPTION = "Nhện Tom Holland được buff sức mạnh khủng khiếp đến mức nào? Chi tiết thú vị Spider-Man #spiderman #tomholland #marvel #mcu #avengers #shorts #xuhuong #phimhay"

def adb(args):
    cmd = ["adb", "-P", PORT, "-s", SERIAL] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

def snap(name):
    adb(["shell", f"screencap -p /sdcard/{name}.png"])
    subprocess.run(["adb", "-P", PORT, "-s", SERIAL, "pull", f"/sdcard/{name}.png", f"C:/Users/Admin/.gemini/antigravity/brain/612f5864-e377-4aa9-a143-bf7f13dcbded/{name}.png"], capture_output=True)
    print(f"  [Camera Snap] {name}.png captured.")

def main():
    print(f"\n========================================================")
    print(f"🚀 BẮT ĐẦU ĐĂNG VIDEO 3: NHỆN TOM HOLLAND LÊN KÊNH MINH")
    print(f"🎬 Video: {VIDEO_PATH}")
    print(f"✍️ Caption: {CAPTION}")
    print(f"========================================================")

    # 1. Dọn dẹp video cũ trong Camera của điện thoại
    print("[1/9] Dọn dẹp thư viện Camera...")
    adb(["shell", "rm", "-f", "/sdcard/DCIM/Camera/*.mp4"])
    time.sleep(1)

    # 2. Push video mới vào
    remote_path = f"/sdcard/DCIM/Camera/vid_{int(time.time())}_spiderman.mp4"
    print(f"[2/9] Nạp video vào máy: {remote_path}...")
    adb(["push", VIDEO_PATH, remote_path])
    adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"])
    adb(["shell", "content", "call", "--uri", "content://media/external/file", "--method", "scan_file", "--arg", remote_path])
    time.sleep(2)

    # Bật sáng màn hình
    adb(["shell", "input", "keyevent", "224"])
    adb(["shell", "input", "keyevent", "82"])

    # 3. Khởi động lại TikTok
    print("[3/9] Khởi động TikTok...")
    adb(["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.5)
    adb(["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(4.5)
    snap("step1_tiktok_home")

    # 4. Bấm nút '+' (Create)
    print("[4/9] Bấm nút '+' tạo video...")
    adb(["shell", "input", "tap", "540", "2030"])
    time.sleep(3.0)
    snap("step2_camera_open")

    # 5. Mở Album (Upload)
    print("[5/9] Mở Album ảnh/video...")
    # Thử tap nút Upload góc dưới bên phải camera
    adb(["shell", "input", "tap", "940", "1920"])
    time.sleep(1.5)
    adb(["shell", "input", "tap", "880", "1900"])
    time.sleep(2.5)
    snap("step3_album_opened")

    # 6. Chọn video đầu tiên (video vừa nạp)
    print("[6/9] Chọn video vừa nạp...")
    # Tọa độ ô chọn tick video đầu tiên
    adb(["shell", "input", "tap", "300", "320"])
    time.sleep(1.5)
    snap("step4_video_selected")

    # 7. Bấm 'Next (1)'
    print("[7/9] Bấm 'Next' chuyển sang màn hình chỉnh sửa...")
    adb(["shell", "input", "tap", "740", "1990"])
    adb(["shell", "input", "tap", "900", "2000"])
    time.sleep(4.0)
    snap("step5_editor_screen")

    # 8. Màn hình Editor -> Bấm Next sang màn hình Post
    print("[8/9] Bấm 'Next' sang màn hình điền Caption...")
    adb(["shell", "input", "tap", "740", "1990"])
    adb(["shell", "input", "tap", "900", "2000"])
    time.sleep(4.0)
    snap("step6_caption_screen")

    # 9. Điền Caption có dấu chuẩn 100%
    print("[9/9] Nhập Caption tiếng Việt...")
    # Tap ô nhập mô tả
    adb(["shell", "input", "tap", "300", "200"])
    time.sleep(1.0)
    adb(["shell", "input", "tap", "150", "310"])
    time.sleep(1.0)

    b64 = base64.b64encode((CAPTION + " ").encode("utf-8")).decode("utf-8")
    adb(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])
    time.sleep(2.0)

    # Ẩn bàn phím ảo
    adb(["shell", "input", "keyevent", "111"])
    time.sleep(1.5)
    snap("step7_caption_filled")

    # 10. Bấm nút ĐĂNG (POST)
    print("[*] 10. Bấm nút ĐĂNG BÀI...")
    adb(["shell", "input", "tap", "740", "1930"])
    time.sleep(1.0)
    adb(["shell", "input", "tap", "740", "1990"])
    adb(["shell", "input", "tap", "900", "2000"])
    time.sleep(5.0)
    snap("step8_posted_done")

    # 11. Lưu log vào FarmTracker
    try:
        tracker = FarmTracker()
        tracker.record_post(
            device_serial=SERIAL,
            tiktok_account="@nguyennminhh256",
            video_file=VIDEO_PATH,
            caption=CAPTION,
            topic="Review Phim / Spider-Man",
            source_url=SOURCE_URL,
            source_channel=SOURCE_CHANNEL,
            status="SUCCESS"
        )
        print("[+] Đã cập nhật vào cơ sở dữ liệu FarmTracker!")
    except Exception as e:
        print(f"[-] Ghi tracker lỗi: {e}")

    print("\n[🎉] HOÀN TẤT ĐĂNG VIDEO 3 LÊN KÊNH MINH THÀNH CÔNG!")

if __name__ == "__main__":
    main()
