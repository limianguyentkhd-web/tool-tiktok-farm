import sys
import subprocess
import time
import json
import urllib.request
import ssl
import re
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

PORT = "5039"
SERIAL = "9889da304447393259"
INBOX = "pnbuohvf4532@primehubcloud.com"
PWD = "wjVnW4mAk"
NEW_EMAIL = "limianguyentkhd@gmail.com"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def run_adb(args):
    return subprocess.run(["adb", "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True)

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

def get_latest_msg_ids():
    url = f"https://megacloudx.com/api/messages?inbox={INBOX}&password={PWD}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode())
            return [m['id'] for m in data.get('results', [])]
    except Exception as e:
        print(f"Lỗi đọc mail: {e}", flush=True)
        return []

def extract_otp_from_message(msg_id):
    detail_url = f"https://megacloudx.com/api/message/{msg_id}"
    req_det = urllib.request.Request(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_det, context=ctx, timeout=8) as r_det:
        det_data = json.loads(r_det.read().decode())
        subject = det_data.get('subject', '')
        body = det_data.get('text_body', '') + ' ' + det_data.get('html_body', '')
        
        # Ưu tiên tìm trong subject trước
        m = re.findall(r'\b\d{6}\b', subject)
        if m:
            return m[0]
        # Sau đó tìm trong body loại trừ #000000
        clean_body = re.sub(r'#[0-9a-fA-F]{6}', '', body)
        m = re.findall(r'\b\d{6}\b', clean_body)
        if m:
            return m[0]
    return None

old_ids = get_latest_msg_ids()
print(f"Hiện có {len(old_ids)} mail trong inbox.", flush=True)

# Thử bấm Resend code tại (233, 872)
print("Bấm Resend code (tap 233, 872)...", flush=True)
tap(233, 872)
time.sleep(2)

otp = None
print("Chờ mã OTP mới...", flush=True)
for i in range(15):
    time.sleep(3)
    url = f"https://megacloudx.com/api/messages?inbox={INBOX}&password={PWD}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode())
            results = data.get('results', [])
            for res in results:
                if res['id'] not in old_ids:
                    print(f"Có mail mới ID: {res['id']}", flush=True)
                    otp = extract_otp_from_message(res['id'])
                    if otp:
                        break
        if otp:
            break
    except Exception as e:
        print(f"Lỗi: {e}", flush=True)

if not otp:
    print("Không lấy được mã mới, kiểm tra lại mail gần nhất...", flush=True)
    if old_ids:
        otp = extract_otp_from_message(old_ids[0])

print(f"===> MÃ OTP XÁC MINH: {otp}", flush=True)

# Bấm backspace để xóa các số cũ nếu có
print("Xóa ký tự cũ...", flush=True)
for _ in range(8):
    run_adb(["shell", "input", "keyevent", "KEYCODE_DEL"])
    time.sleep(0.1)

# Nhập mã OTP
print(f"Đang nhập OTP {otp}...", flush=True)
for ch in otp:
    run_adb(["shell", "input", "keyevent", f"KEYCODE_{ch}"])
    time.sleep(0.3)

time.sleep(3)

# Đọc UI mới
elements = get_elements()
print("--- UI SAU KHI NHẬP OTP XÁC MINH ---", flush=True)
for t, d, b in elements:
    if t or d:
        print(f"{t!r} | {d!r} | {b}", flush=True)
