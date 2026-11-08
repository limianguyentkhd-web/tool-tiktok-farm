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

def type_text(text):
    run_adb(["shell", "input", "text", text])
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
        print(f"Lỗi lấy danh sách thư ban đầu: {e}")
        return []

def get_new_otp(old_ids):
    print("Đang lắng nghe mã OTP mới từ megacloudx.com...")
    for attempt in range(25):
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
                        print(f"Tìm thấy email mới (ID: {msg_id})! Đang phân tích...")
                        detail_url = f"https://megacloudx.com/api/message/{msg_id}"
                        req_det = urllib.request.Request(detail_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req_det, context=ctx, timeout=8) as r_det:
                            det_data = json.loads(r_det.read().decode())
                            body = det_data.get('text_body', '') + ' ' + det_data.get('html_body', '') + ' ' + det_data.get('subject', '')
                            # Lấy các mã 6 số
                            matches = re.findall(r'\b\d{6}\b', body)
                            if matches:
                                print(f"===> TÌM THẤY OTP: {matches[0]}")
                                return matches[0]
        except Exception as e:
            print(f"Chờ mail... ({e})")
    return None

# Bắt đầu quy trình
old_ids = get_existing_msg_ids()
print(f"Số lượng email cũ trong inbox: {len(old_ids)}")

print("Bước 1: Bấm Change email tại (540, 1408)...")
tap(540, 1408)
time.sleep(2)

elements = get_elements()
print("--- Giao diện sau khi bấm Change email ---")
for t, d, b in elements:
    print(f"TXT: {t!r} | DESC: {d!r} | BOUNDS: {b}")

# Kiểm tra xem có cần bấm 'Send code' hay TikTok đã tự gửi
# Nếu có nút 'Send code', bấm vào nó
for t, d, b in elements:
    if "send code" in t.lower() or "send code" in d.lower():
        import re as re_mod
        m = re_mod.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
        if m:
            cx = (int(m.group(1)) + int(m.group(3))) // 2
            cy = (int(m.group(2)) + int(m.group(4))) // 2
            print(f"Bấm nút Send code tại ({cx}, {cy})...")
            tap(cx, cy)
            break

otp = get_new_otp(old_ids)
if not otp:
    print("Hết thời gian chờ OTP từ mail cũ!")
    sys.exit(1)

print(f"Bước 2: Điền OTP {otp} vào màn hình xác minh...")
for digit in otp:
    run_adb(["shell", "input", "keyevent", f"KEYCODE_{digit}"])
    time.sleep(0.3)

time.sleep(3)
elements_after_otp = get_elements()
print("--- Giao diện sau khi nhập OTP mail cũ ---")
for t, d, b in elements_after_otp:
    print(f"TXT: {t!r} | DESC: {d!r} | BOUNDS: {b}")

# Kiểm tra xem đã sang màn hình nhập email mới chưa
has_email_input = False
for t, d, b in elements_after_otp:
    if any(k in t.lower() or k in d.lower() for k in ["enter email", "add email", "email address"]):
        has_email_input = True
        break

if has_email_input or any("email" in t.lower() for t, d, b in elements_after_otp):
    print(f"Bước 3: Nhập email mới {NEW_EMAIL}...")
    # Thường trường nhập email nằm ở giữa màn hình (y khoảng 400-600)
    # Tìm Edit text
    # Dùng input text
    run_adb(["shell", "input", "text", NEW_EMAIL])
    time.sleep(1)
    
    # Kiểm tra nút Send code / Next
    elements_new = get_elements()
    for t, d, b in elements_new:
        print(f"TXT: {t!r} | DESC: {d!r} | BOUNDS: {b}")
        if any(k in t.lower() or k in d.lower() for k in ["send code", "next", "continue"]):
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
            if m:
                cx = (int(m.group(1)) + int(m.group(3))) // 2
                cy = (int(m.group(2)) + int(m.group(4))) // 2
                print(f"Bấm {t or d} tại ({cx}, {cy})...")
                tap(cx, cy)
                break
    print(">>> ĐÃ GỬI OTP VỀ GMAIL CỦA BẠN! Vui lòng kiểm tra hộp thư.")
