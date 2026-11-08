import os
import sys
import time
import base64
import subprocess
from farm_tracker import FarmTracker

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SERIAL = "ce031713dba2c72101"
VIDEO_PATH = r"d:\TOOL TIKTOK\videos\ready_3_Người_đàn_ông_này_mới_là_Optimus_đời_thực__shorts_42WxYeQOuW8.mp4"
SOURCE_URL = "https://www.youtube.com/shorts/42WxYeQOuW8"
SOURCE_CHANNEL = "https://www.youtube.com/@zim_video/shorts"
CAPTION = "Người đàn ông này mới chính là Optimus Prime đời thực! Giọng lồng tiếng huyền thoại của Transformers #transformers #optimusprime #shorts #fyp #dienanh"

def adb(args):
    cmd = ["adb", "-s", SERIAL] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

def run():
    print(f"\n========================================================")
    print(f"🎬 BẮT ĐẦU ĐĂNG LẠI VIDEO OPTIMUS PRIME KÈM CAPTION CHUẨN")
    print(f"📁 Video: {os.path.basename(VIDEO_PATH)}")
    print(f"📝 Caption: {CAPTION}")
    print(f"========================================================")

    # 1. Dọn dẹp video cũ trong máy điện thoại
    print("[*] 1. Dọn dẹp video cũ trong máy điện thoại...")
    adb(["shell", "rm", "-f", "/sdcard/DCIM/Camera/*.mp4"])

    # 2. Nạp video mới vào thư viện máy
    print("[*] 2. Nạp video vào thư viện máy...")
    remote_path = f"/sdcard/DCIM/Camera/vid_{int(time.time())}_optimus.mp4"
    adb(["push", VIDEO_PATH, remote_path])
    adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"])
    adb(["shell", "content", "call", "--uri", "content://media/external/file", "--method", "scan_file", "--arg", remote_path])
    print(f"[+] Đã đẩy video vào: {remote_path}")

    # Đánh thức màn hình
    adb(["shell", "input", "keyevent", "224"])
    adb(["shell", "input", "keyevent", "82"])

    # 3. Mở TikTok từ đầu
    print("[*] 3. Khởi động lại TikTok sạch...")
    adb(["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.5)
    adb(["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(4.5)

    # 4. Bấm nút '+' (Create)
    print("[*] 4. Bấm nút '+' (Create)...")
    adb(["shell", "input", "tap", "540", "2030"])
    time.sleep(3.0)

    # 5. Mở Album (Upload)
    print("[*] 5. Mở Album (Upload)...")
    adb(["shell", "input", "tap", "90", "1920"])
    time.sleep(1.0)
    adb(["shell", "input", "tap", "417", "563"])
    time.sleep(2.5)

    # 6. Chọn hình tròn tick của video đầu tiên
    print("[*] 6. Chọn video mới nạp...")
    adb(["shell", "input", "tap", "300", "320"])
    time.sleep(1.5)

    # 7. Bấm 'Next (1)'
    print("[*] 7. Bấm 'Next (1)'...")
    adb(["shell", "input", "tap", "740", "1990"])
    time.sleep(4.0)

    # 8. Màn hình chỉnh sửa -> Bấm Next
    print("[*] 8. Bấm 'Next' sang màn hình Đăng...")
    adb(["shell", "input", "tap", "740", "1990"])
    time.sleep(3.5)

    # 9. Nhập Caption với cơ chế ép nhận con trỏ 100%
    print("[*] 9. Nhập Caption tiếng Việt có dấu...")
    # Bước 9.1: Bấm nút # Hashtags để ép TikTok focus con trỏ vào ô nhập
    adb(["shell", "input", "tap", "150", "310"])
    time.sleep(1.0)
    # Bước 9.2: Gõ caption qua ADBKeyboard
    b64 = base64.b64encode((CAPTION + " ").encode("utf-8")).decode("utf-8")
    adb(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])
    time.sleep(2.0)

    # Bước 9.3: Đóng bàn phím ảo bằng phím ESC (111) an toàn
    adb(["shell", "input", "keyevent", "111"])
    time.sleep(1.5)

    # 10. Bấm nút ĐĂNG (POST)
    print("[*] 10. Bấm nút ĐĂNG (POST)...")
    adb(["shell", "input", "tap", "740", "1930"])
    time.sleep(1.0)
    adb(["shell", "input", "tap", "740", "1990"])
    time.sleep(5.0)

    # 11. Ghi nhận lịch sử
    tracker = FarmTracker()
    tracker.record_post(
        device_serial=SERIAL,
        tiktok_account="@nguyennminhh256",
        video_file=VIDEO_PATH,
        caption=CAPTION,
        topic="Review Phim / Transformers",
        source_url=SOURCE_URL,
        source_channel=SOURCE_CHANNEL,
        status="SUCCESS"
    )
    print("[+] 🎉 ĐÃ HOÀN TẤT ĐĂNG LẠI VIDEO KÈM CAPTION THÀNH CÔNG!")

if __name__ == '__main__':
    run()
