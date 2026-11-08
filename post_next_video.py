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
    print(f"🎬 BẮT ĐẦU ĐĂNG VIDEO TIẾP THEO LÊN THIẾT BỊ [{SERIAL}]")
    print(f"📁 Video: {os.path.basename(VIDEO_PATH)}")
    print(f"📝 Caption: {CAPTION}")
    print(f"========================================================")

    print("[*] 1. Dọn dẹp video cũ trong máy điện thoại...")
    adb(["shell", "rm", "-f", "/sdcard/DCIM/Camera/*.mp4"])

    print("[*] 2. Nạp video mới vào thư viện máy...")
    remote_path = f"/sdcard/DCIM/Camera/vid_{int(time.time())}_optimus.mp4"
    adb(["push", VIDEO_PATH, remote_path])
    adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"])
    adb(["shell", "content", "call", "--uri", "content://media/external/file", "--method", "scan_file", "--arg", remote_path])
    print(f"[+] Đã đẩy video vào: {remote_path}")

    # Đánh thức màn hình
    adb(["shell", "input", "keyevent", "224"])
    adb(["shell", "input", "keyevent", "82"])

    print("[*] 3. Khởi động lại TikTok sạch...")
    adb(["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.5)
    adb(["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(4.5)

    print("[*] 4. Bấm nút '+' (Create) ở thanh dưới...")
    adb(["shell", "input", "tap", "540", "2030"])
    time.sleep(3.0)

    print("[*] 5. Mở Album (Upload) hoặc ô 'New video'...")
    adb(["shell", "input", "tap", "90", "1980"])
    time.sleep(1.0)
    adb(["shell", "input", "tap", "417", "563"])
    time.sleep(2.5)

    print("[*] 6. Chọn video MỚI NHẤT (ô đầu tiên bên trái)...")
    adb(["shell", "input", "tap", "180", "500"])
    time.sleep(1.5)

    print("[*] 7. Bấm 'Next' ở màn hình chọn video...")
    adb(["shell", "input", "tap", "932", "2025"])
    time.sleep(4.0)

    print("[*] 8. Bấm 'Next' / 'Lưu' ở màn hình biên tập video...")
    adb(["shell", "input", "tap", "796", "2011"])
    time.sleep(1.5)
    adb(["shell", "input", "tap", "996", "136"])
    time.sleep(3.5)

    print("[*] 9. Nhập Caption tiếng Việt có dấu...")
    adb(["shell", "input", "tap", "350", "400"])
    time.sleep(1.2)
    b64 = base64.b64encode((CAPTION + " ").encode("utf-8")).decode("utf-8")
    adb(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])
    time.sleep(1.5)

    # Ẩn bàn phím trước khi bấm Post
    adb(["shell", "input", "keyevent", "4"])
    time.sleep(1.0)

    print("[*] 10. Bấm nút ĐĂNG (POST)...")
    adb(["shell", "input", "tap", "799", "1999"])
    time.sleep(1.0)
    adb(["shell", "input", "tap", "800", "1980"])
    time.sleep(5.0)

    print("[*] 11. Ghi nhận lịch sử vào Cơ sở dữ liệu FarmTracker...")
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

    print("[+] 🎉 ĐÃ HOÀN TẤT ĐĂNG VIDEO TIẾP THEO THÀNH CÔNG!")

if __name__ == '__main__':
    run()
