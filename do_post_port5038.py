import os
import sys
import time
import base64
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PORT = "5038"
SERIAL = "ce031713dba2c72101"
CAPTION = "Người đàn ông này mới chính là Optimus Prime đời thực! Giọng lồng tiếng huyền thoại Transformers #transformers #optimusprime #shorts #fyp #dienanh"

def adb(args):
    cmd = ["adb", "-P", PORT, "-s", SERIAL] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

def run():
    print(f"[*] Đang thực hiện đăng bài trên cổng ADB {PORT}...")

    # 1. Bấm mở Album từ góc dưới Camera
    print("[*] 1. Mở Album...")
    adb(["shell", "input", "tap", "90", "1920"])
    time.sleep(2.5)

    # 2. Chọn hình tròn tick video 1
    print("[*] 2. Chọn video 00:48...")
    adb(["shell", "input", "tap", "300", "320"])
    time.sleep(1.5)

    # 3. Bấm Next (1)
    print("[*] 3. Bấm 'Next (1)'...")
    adb(["shell", "input", "tap", "740", "1990"])
    time.sleep(4.0)

    # 4. Màn hình chỉnh sửa -> Bấm Next
    print("[*] 4. Bấm 'Next' sang màn hình Đăng...")
    adb(["shell", "input", "tap", "740", "1990"])
    time.sleep(3.5)

    # 5. Nhập Caption tiếng Việt có dấu
    print("[*] 5. Nhập Caption...")
    # Bấm trực tiếp vào khung mô tả
    adb(["shell", "input", "tap", "300", "200"])
    time.sleep(1.0)
    # Bấm thêm nút # Hashtags để ép con trỏ nhấp nháy 100%
    adb(["shell", "input", "tap", "150", "310"])
    time.sleep(1.0)

    b64 = base64.b64encode((CAPTION + " ").encode("utf-8")).decode("utf-8")
    adb(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])
    time.sleep(2.0)

    # Đóng bàn phím an toàn bằng ESC (111)
    adb(["shell", "input", "keyevent", "111"])
    time.sleep(1.5)

    # 6. Bấm nút ĐĂNG (POST)
    print("[*] 6. Bấm ĐĂNG (POST)...")
    adb(["shell", "input", "tap", "740", "1930"])
    time.sleep(1.0)
    adb(["shell", "input", "tap", "740", "1990"])
    time.sleep(4.0)

    print("[+] 🎉 ĐÃ HOÀN TẤT ĐĂNG BÀI KÈM CAPTION!")

if __name__ == '__main__':
    run()
