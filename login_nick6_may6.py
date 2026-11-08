import urllib.request
import ssl
import json
import time
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

ACC6 = {
    "port": 5037,
    "serial": "ce031713ed1e10540d",
    "user": "user2810657457111",
    "pass": "@L00ggzhItTJd4",
    "email": "gwjtdjwym7461@megacloudx.com",
    "email_pwd": "QYmylGisw"
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def adb(cmd_list):
    full = [ADB, "-P", str(ACC6["port"]), "-s", ACC6["serial"]] + cmd_list
    res = subprocess.run(full, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()

def dump_ui():
    adb(["shell", "uiautomator", "dump", "/sdcard/d6.xml"])
    res = adb(["shell", "cat", "/sdcard/d6.xml"])
    try:
        return ET.fromstring(res)
    except:
        return None

def find_elem(root, text_sub=None, desc_sub=None, res_id=None):
    if root is None: return None
    for n in root.iter():
        if text_sub and text_sub.lower() in (n.get('text', '') or '').lower(): return n
        if desc_sub and desc_sub.lower() in (n.get('content-desc', '') or '').lower(): return n
        if res_id and res_id == n.get('resource-id', ''): return n
    return None

def get_center(bounds_str):
    m = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
    if len(m) == 2:
        return (int(m[0][0]) + int(m[1][0])) // 2, (int(m[0][1]) + int(m[1][1])) // 2
    return None

def fetch_otp(email, email_pwd, max_wait=35):
    print(f"[*] Đang lắng nghe hòm thư megacloudx.com cho {email}...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        time.sleep(3)
        try:
            url = f"https://megacloudx.com/api/messages?inbox={email}&password={email_pwd}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                data = json.loads(r.read().decode())
            results = data.get('results', [])
            if results:
                subj = results[0].get('subject', '')
                m = re.search(r'\b(\d{6})\b', subj)
                if m:
                    print(f"[✓] ĐÃ LẤY ĐƯỢC MÃ OTP: {m.group(1)} (từ subject: '{subj}')")
                    return m.group(1)
        except Exception as e:
            pass
    return None

def dismiss_popups():
    for _ in range(5):
        time.sleep(1)
        root = dump_ui()
        if root is None: break
        allow_btn = find_elem(root, text_sub="Allow") or find_elem(root, text_sub="Don't allow")
        if allow_btn:
            cx, cy = get_center(allow_btn.get('bounds'))
            print(f"[*] Bấm popup button ({cx}, {cy})...")
            adb(["shell", "input", "tap", str(cx), str(cy)])
            continue
        got_btn = find_elem(root, text_sub="Got it") or find_elem(root, text_sub="Not now")
        if got_btn:
            cx, cy = get_center(got_btn.get('bounds'))
            print(f"[*] Bấm Got it / Not now ({cx}, {cy})...")
            adb(["shell", "input", "tap", str(cx), str(cy)])
            continue
        break

def do_login():
    print(f"[*] Đăng nhập Nick 6: {ACC6['user']} trên máy {ACC6['serial']}...")
    
    # Check if Cancel button on passkey is visible
    root = dump_ui()
    cancel_btn = find_elem(root, text_sub="Cancel")
    if cancel_btn:
        cx, cy = get_center(cancel_btn.get('bounds'))
        print(f"[*] Đóng popup Passkey ({cx}, {cy})...")
        adb(["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(1.5)
        
    # Check if on Login screen or Profile
    root = dump_ui()
    opt_user = find_elem(root, text_sub="Use phone / email / username")
    if opt_user:
        cx, cy = get_center(opt_user.get('bounds'))
        print(f"[*] Chọn Use phone/email/username ({cx}, {cy})...")
        adb(["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(2)
    else:
        # try tapping the first option
        adb(["shell", "input", "tap", "524", "938"])
        time.sleep(2)
        
    # Tab Email / Username
    root = dump_ui()
    tab_email = find_elem(root, text_sub="Email / Username")
    if tab_email:
        cx, cy = get_center(tab_email.get('bounds'))
        print(f"[*] Chọn tab Email/Username ({cx}, {cy})...")
        adb(["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(1.5)
    else:
        adb(["shell", "input", "tap", "791", "252"])
        time.sleep(1.5)
        
    # Type Username
    print(f"[*] Nhập username: {ACC6['user']}...")
    adb(["shell", "input", "tap", "540", "432"])
    time.sleep(0.5)
    adb(["shell", "input", "text", ACC6['user']])
    time.sleep(0.5)
    
    # Continue
    print("[*] Bấm Continue...")
    adb(["shell", "input", "tap", "540", "1128"])
    time.sleep(3.5)
    
    # Type Password
    print(f"[*] Nhập password...")
    adb(["shell", "input", "tap", "500", "521"])
    time.sleep(0.5)
    escaped_pwd = ACC6['pass'].replace("@", r"\@")
    adb(["shell", "input", "text", escaped_pwd])
    time.sleep(0.5)
    
    # Submit Password
    print("[*] Gửi mật khẩu...")
    adb(["shell", "input", "tap", "540", "1128"])
    time.sleep(4)
    
    # Check OTP verify
    root = dump_ui()
    verify_node = find_elem(root, text_sub="Verify it") or find_elem(root, text_sub="Email")
    if verify_node:
        print("[!] Cần xác minh Email! Bấm chọn Email...")
        adb(["shell", "input", "tap", "539", "673"])
        time.sleep(3)
        otp = fetch_otp(ACC6['email'], ACC6['email_pwd'])
        if otp:
            adb(["shell", "input", "tap", "885", "760"])
            time.sleep(0.3)
            for _ in range(8):
                adb(["shell", "input", "keyevent", "67"])
                time.sleep(0.05)
            print(f"[*] Điền mã OTP: {otp}...")
            for d in otp:
                adb(["shell", "input", "text", d])
                time.sleep(0.2)
            time.sleep(4)
    
    # Click Continue if still on password screen
    adb(["shell", "input", "tap", "500", "508"])
    time.sleep(4)
    
    dismiss_popups()
    
    # Screencap final state
    art_dir = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"
    with open(f"{art_dir}\\may6_login_result.png", "wb") as f:
        subprocess.run([ADB, "-P", str(ACC6["port"]), "-s", ACC6["serial"], "exec-out", "screencap", "-p"], stdout=f)
    print("[✓] Đã chụp ảnh kết quả login: may6_login_result.png")

if __name__ == "__main__":
    do_login()
