import os
import sys
import time
import base64
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SERIAL = "ce031713dba2c72101"
VIDEO_PATH = r"d:\TOOL TIKTOK\videos\ready_1_Chi_tiết_thú_vị_trong_Avengers__shorts_qk3pEXQ43aA.mp4"

def adb(args):
    cmd = ["adb", "-s", SERIAL] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

def run():
    print(f"[*] 1. Đang dọn dẹp các video cũ trên điện thoại {SERIAL}...")
    adb(["shell", "rm", "-f", "/sdcard/DCIM/Camera/*.mp4"])
    
    print(f"[*] 2. Đang đẩy video mới (CHỮ XUÔI CHUẨN) sang điện thoại...")
    remote_path = f"/sdcard/DCIM/Camera/unflipped_{int(time.time())}.mp4"
    adb(["push", VIDEO_PATH, remote_path])
    adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"])
    adb(["shell", "content", "call", "--uri", "content://media/external/file", "--method", "scan_file", "--arg", remote_path])
    print(f"[+] Đã đẩy xong video: {remote_path}")

    # Bật màn hình
    adb(["shell", "input", "keyevent", "224"])
    adb(["shell", "input", "keyevent", "82"])

    print("[*] 3. Đang khởi động lại TikTok...")
    adb(["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.5)
    adb(["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(4.5)

    print("[*] 4. Bấm nút '+' (Create) ở giữa đáy màn hình...")
    adb(["shell", "input", "tap", "540", "2030"])
    time.sleep(3.0)

    print("[*] 5. Mở Album (Upload) góc dưới...")
    adb(["shell", "input", "tap", "90", "1980"])
    time.sleep(3.0)

    print("[*] 6. Chọn video MỚI NHẤT (ô đầu tiên bên trái)...")
    adb(["shell", "input", "tap", "180", "480"])
    time.sleep(2.0)

    print("[*] 7. Bấm 'Next' ở màn hình chọn video...")
    adb(["shell", "input", "tap", "794", "1994"])
    time.sleep(4.0)

    print("[*] 8. Bấm 'Next' ở màn hình biên tập video...")
    adb(["shell", "input", "tap", "796", "2011"])
    time.sleep(4.0)

    print("[*] 9. Nhập Caption tiếng Việt...")
    # Chạm vào ô nhập caption
    adb(["shell", "input", "tap", "350", "400"])
    time.sleep(1.5)

    caption = "Tại sao Stormbreaker lại có ý thức tự chủ? Chi tiết cực thú vị trong Avengers #marvel #thor #avengers #shorts #fyp"
    b64 = base64.b64encode(caption.encode("utf-8")).decode("utf-8")
    adb(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])
    time.sleep(1.5)

    # Ẩn bàn phím
    adb(["shell", "input", "keyevent", "4"])
    time.sleep(1.0)

    print("[*] 10. Bấm nút ĐĂNG (POST)...")
    adb(["shell", "input", "tap", "799", "1999"])
    time.sleep(5.0)

    print("[+] 🎉 ĐÃ HOÀN TẤT ĐĂNG VIDEO MỚI THÀNH CÔNG!")

if __name__ == '__main__':
    run()
