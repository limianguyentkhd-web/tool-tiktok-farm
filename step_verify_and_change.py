import sys
import subprocess
import time
import json
import urllib.request
import ssl
import re
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

SERIAL = "9889da304447393259"
INBOX = "pnbuohvf4532@primehubcloud.com"
PWD = "wjVnW4mAk"
NEW_EMAIL = "limianguyentkhd@gmail.com"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def run_adb(args):
    return subprocess.run(["adb", "-s", SERIAL] + args, capture_output=True, text=True)

def tap(x, y):
    run_adb(["shell", "input", "tap", str(x), str(y)])
    time.sleep(1)

def get_elements():
    run_adb(["shell", "uiautomator", "dump", "/sdcard/ui.xml"])
    run_adb(["pull", "/sdcard/ui.xml", "current_ui.xml"])
    tree = ET.parse("current_ui.xml")
    root = tree.getroot()
    elements = []
    for node in root.iter():
        text = node.attrib.get("text", "")
        desc = node.attrib.get("content-desc", "")
        bounds = node.attrib.get("bounds", "")
        if text or desc:
            elements.append((text, desc, bounds))
    return elements

def get_existing_msg_ids():
    url = f"https://megacloudx.com/api/messages?inbox={INBOX}&password={PWD}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode())
            return [m['id'] for m in data.get('results', [])]
    except Exception as e:
        print(f"Lỗi lấy inbox: {e}", flush=True)
        return []

def get_new_otp(old_ids):
    print("Đang lắng nghe mã OTP mới từ megacloudx.com...", flush=True)
    for attempt in range(20):
        time.sleep(3)
        url = f"https://megacloudx.com/api/messages?inbox={INBOX}&password={PWD}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                data = json.loads(r.read().decode())
                results = data.get('results', [])
                for res in results:
                    msg_id = res['id']
                    if msg_id not in old_ids:
                        print(f"Có email mới ID: {msg_id}! Đang đọc mã...", flush=True)
                        detail_url = f"https://megacloudx.com/api/message/{msg_id}"
                        req_det = urllib.request.Request(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req_det, context=ctx, timeout=8) as r_det:
                            det_data = json.loads(r_det.read().decode())
                            body = det_data.get('text_body', '') + ' ' + det_data.get('html_body', '') + ' ' + det_data.get('subject', '')
                            matches = re.findall(r'\b\d{6}\b', body)
                            if matches:
                                print(f"===> OTP NHẬN ĐƯỢC: {matches[0]}", flush=True)
                                return matches[0]
        except Exception as e:
            print(f"Chờ mail... ({e})", flush=True)
    return None

old_ids = get_existing_msg_ids()
print(f"Danh sách thư cũ: {len(old_ids)} thư", flush=True)

# 1. Chọn phương thức xác minh p***2@primehubcloud.com
print("Chọn email p***2@primehubcloud.com (tap 540, 650)...", flush=True)
tap(540, 650)
time.sleep(1)

# 2. Bấm Next
print("Bấm nút Next (tap 540, 1904)...", flush=True)
tap(540, 1904)
time.sleep(2)

# Lấy UI sau khi bấm Next
elements = get_elements()
print("UI sau khi bấm Next:", flush=True)
for t, d, b in elements:
    if t or d:
        print(f"  {t!r} | {d!r} | {b}", flush=True)

# 3. Lấy OTP từ mail cũ
otp = get_new_otp(old_ids)
if not otp:
    print("Không nhận được OTP từ mail cũ!", flush=True)
    sys.exit(1)

# 4. Nhập OTP
print(f"Nhập mã OTP {otp}...", flush=True)
for d in otp:
    run_adb(["shell", "input", "keyevent", f"KEYCODE_{d}"])
    time.sleep(0.3)

time.sleep(3)

# 5. Kiểm tra UI màn hình nhập mail mới
elements_new = get_elements()
print("UI sau khi nhập OTP xác minh:", flush=True)
for t, d, b in elements_new:
    if t or d:
        print(f"  {t!r} | {d!r} | {b}", flush=True)
