import urllib.request
import ssl
import json
import time
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
PORT = 5038
SERIAL = "9889da304447393259"

INBOX = "pnbuohvf4532@primehubcloud.com"
PWD = "wjVnW4mAk"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def adb(cmd):
    res = subprocess.run([ADB, "-P", str(PORT), "-s", SERIAL] + cmd, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()

print("[1/5] Bấm gửi mã OTP về email (tap 539 673)...")
adb(["shell", "input", "tap", "539", "673"])
time.sleep(3)

# Chờ và đọc mail từ megacloudx.com
print(f"[2/5] Đang chờ và đọc mã OTP từ megacloudx.com cho {INBOX}...")
code = None
for attempt in range(12):
    time.sleep(3)
    url = f"https://megacloudx.com/api/messages?inbox={INBOX}&password={PWD}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode())
            results = data.get('results', [])
            if results:
                msg_id = results[0]['id']
                print(f"[+] Tìm thấy email mới nhất (ID: {msg_id})! Đang lấy nội dung...")
                detail_url = f"https://megacloudx.com/api/message/{msg_id}"
                req_detail = urllib.request.Request(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_detail, context=ctx, timeout=8) as r_det:
                    det_data = json.loads(r_det.read().decode())
                    body = det_data.get('text_body', '') + ' ' + det_data.get('html_body', '') + ' ' + det_data.get('subject', '')
                    # Tìm mã 6 chữ số
                    m = re.findall(r'\b\d{6}\b', body)
                    if m:
                        code = m[0]
                        print(f"[✓] ĐÃ TÌM THẤY MÃ OTP: {code}")
                        break
    except Exception as e:
        print(f"[-] Đang thử lại... ({e})")

if not code:
    print("[-] Không nhận được mã OTP sau 36 giây!")
    sys.exit(1)

print(f"[3/5] Nhập mã OTP {code} vào TikTok...")
for digit in code:
    adb(["shell", "input", "text", digit])
    time.sleep(0.3)

time.sleep(4)
print("[4/5] Chụp ảnh kiểm tra trạng thái đăng nhập...")
adb(["shell", "screencap", "-p", "/sdcard/login_result_9889.png"])
subprocess.run([ADB, "-P", str(PORT), "-s", SERIAL, "pull", "/sdcard/login_result_9889.png", "d:/TOOL TIKTOK/login_result_9889.png"])
print("[✓] Đã lưu ảnh kết quả vào d:/TOOL TIKTOK/login_result_9889.png")
