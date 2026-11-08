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

def get_latest_otp(exclude_ids=[]):
    print("Đang chờ mail chứa OTP từ TikTok...", flush=True)
    for attempt in range(15):
        time.sleep(3)
        url = f"https://megacloudx.com/api/messages?inbox={INBOX}&password={PWD}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                data = json.loads(r.read().decode())
                results = data.get('results', [])
                for res in results:
                    msg_id = res['id']
                    if msg_id not in exclude_ids:
                        # Lấy subject
                        detail_url = f"https://megacloudx.com/api/message/{msg_id}"
                        req_det = urllib.request.Request(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req_det, context=ctx, timeout=8) as r_det:
                            det_data = json.loads(r_det.read().decode())
                            subj = det_data.get('subject', '')
                            m = re.findall(r'\b\d{6}\b', subj)
                            if m:
                                return m[0], msg_id
                            body = det_data.get('text_body', '')
                            m2 = re.findall(r'\b\d{6}\b', body)
                            if m2:
                                return m2[0], msg_id
        except Exception as e:
            print(f"Chờ mail... ({e})", flush=True)
    return None, None

# Bấm Next để gửi mã xác minh email cũ
print("Bấm nút Next (tap 540, 1904)...", flush=True)
tap(540, 1904)
time.sleep(2)

# Lấy OTP
otp, msg_id = get_latest_otp(exclude_ids=[])
if not otp:
    print("Không lấy được OTP!", flush=True)
    sys.exit(1)

print(f"===> OTP NHẬN ĐƯỢC: {otp}", flush=True)

# Chờ 1 chút để màn hình input mã ổn định
time.sleep(2)

# Nhập mã OTP vào 6 ô
print(f"Nhập mã OTP {otp}...", flush=True)
for ch in otp:
    run_adb(["shell", "input", "keyevent", f"KEYCODE_{ch}"])
    time.sleep(0.3)

time.sleep(4)

# Chụp màn hình và dump UI
subprocess.run(f"adb -P {PORT} -s {SERIAL} exec-out screencap -p > cur_screen.png", shell=True)
subprocess.run(f'copy cur_screen.png "C:\\Users\\Admin\\.gemini\\antigravity\\brain\\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\\cur_screen.png"', shell=True)

elements = get_elements()
print("--- UI SAU KHI NHẬP OTP XÁC MINH CŨ ---", flush=True)
for t, d, b in elements:
    if t or d:
        print(f"  {t!r} | {d!r} | {b}", flush=True)

# Tìm chỗ nhập email mới nếu đã hiển thị
email_field = None
for t, d, b in elements:
    if any(k in (t+d).lower() for k in ["enter email", "email address", "email"]):
        email_field = b

print(f"Email field bounds: {email_field}", flush=True)
if email_field:
    # Tap vào ô nhập email
    # Tâm ô nhập email
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", email_field)
    if m:
        cx = (int(m.group(1)) + int(m.group(3))) // 2
        cy = (int(m.group(2)) + int(m.group(4))) // 2
        print(f"Tap vào ô nhập email tại ({cx}, {cy})...", flush=True)
        tap(cx, cy)
        time.sleep(1)
    
    print(f"Nhập email mới {NEW_EMAIL}...", flush=True)
    run_adb(["shell", "input", "text", NEW_EMAIL])
    time.sleep(2)
    
    # Bấm Send code
    elements_new = get_elements()
    for t, d, b in elements_new:
        if any(k in (t+d).lower() for k in ["send code", "next", "continue"]):
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
            if m:
                cx = (int(m.group(1)) + int(m.group(3))) // 2
                cy = (int(m.group(2)) + int(m.group(4))) // 2
                print(f"Bấm nút {t or d} tại ({cx}, {cy})...", flush=True)
                tap(cx, cy)
                break

time.sleep(3)
subprocess.run(f"adb -P {PORT} -s {SERIAL} exec-out screencap -p > cur_screen.png", shell=True)
subprocess.run(f'copy cur_screen.png "C:\\Users\\Admin\\.gemini\\antigravity\\brain\\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\\cur_screen.png"', shell=True)
print("Hoàn tất bước gửi mã về Gmail của user!")
