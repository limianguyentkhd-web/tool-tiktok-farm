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

ACCOUNTS = [
    {
        "id": 2,
        "port": 5038,
        "serial": "988a17344c564b5657",
        "user": "user84009697968164",
        "pass": "@L88jTPasitdUg",
        "email": "dluvzhltaf7199@megacloudx.com",
        "email_pwd": "QcfAqqhXI"
    },
    {
        "id": 3,
        "port": 5037,
        "serial": "ce01182188dbdcee0c",
        "user": "user3607950285377",
        "pass": "@L63aGrj5m9POZ",
        "email": "hmpqybusgl4490@trustlark.com",
        "email_pwd": "A0u8fcAxn"
    },
    {
        "id": 4,
        "port": 5037,
        "serial": "ce011821c38b263b05",
        "user": "user5878212175691",
        "pass": "@L206ThnU0ortn",
        "email": "lcqskhcot3161@primehubcloud.com",
        "email_pwd": "wQMUXKm4I"
    },
    {
        "id": 5,
        "port": 5038,
        "serial": "ce011821c45dc4060c",
        "user": "user1251955152358",
        "pass": "@L65rnkDswvCwq",
        "email": "kehysptsc3316@trustlark.com",
        "email_pwd": "wkiHl7uhG"
    }
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def adb(port, serial, cmd_list):
    full = [ADB, "-P", str(port), "-s", serial] + cmd_list
    res = subprocess.run(full, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()

def dump_ui(port, serial):
    adb(port, serial, ["shell", "uiautomator", "dump", "/sdcard/d.xml"])
    res = adb(port, serial, ["shell", "cat", "/sdcard/d.xml"])
    try:
        return ET.fromstring(res)
    except:
        return None

def find_elem(root, text_sub=None, desc_sub=None, res_id=None):
    if root is None: return None
    for n in root.iter():
        if text_sub and text_sub in n.get('text', ''): return n
        if desc_sub and desc_sub in n.get('content-desc', ''): return n
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

def dismiss_popups(port, serial):
    for _ in range(4):
        time.sleep(1)
        root = dump_ui(port, serial)
        if root is None: break
        # Allow location
        allow_btn = find_elem(root, text_sub="Allow")
        if allow_btn:
            cx, cy = get_center(allow_btn.get('bounds'))
            print(f"[*] Bấm Allow ({cx}, {cy})...")
            adb(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
            continue
        # Got it
        got_btn = find_elem(root, text_sub="Got it")
        if got_btn:
            cx, cy = get_center(got_btn.get('bounds'))
            print(f"[*] Bấm Got it ({cx}, {cy})...")
            adb(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
            continue
        # Close live stream (X)
        close_btn = find_elem(root, desc_sub="Close") or find_elem(root, res_id="com.zhiliaoapp.musically:id/close")
        if close_btn:
            cx, cy = get_center(close_btn.get('bounds'))
            print(f"[*] Đóng live stream ({cx}, {cy})...")
            adb(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
            continue
        break

def login_account(acc):
    port = acc["port"]
    serial = acc["serial"]
    username = acc["user"]
    pwd = acc["pass"]
    email = acc["email"]
    email_pwd = acc["email_pwd"]
    
    print("\n" + "="*60)
    print(f"[*] BẮT ĐẦU ĐĂNG NHẬP MÁY {acc['id']} ({serial}) - NICK: {username}")
    print("="*60)
    
    # 1. Mở TikTok
    adb(port, serial, ["shell", "am", "start", "-n", "com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity"])
    time.sleep(3)
    
    # 2. Kiểm tra nếu chưa ở trang login
    root = dump_ui(port, serial)
    login_btn = find_elem(root, text_sub="Log in") or find_elem(root, desc_sub="Log in")
    if login_btn:
        cx, cy = get_center(login_btn.get('bounds'))
        print(f"[*] Bấm Log in ({cx}, {cy})...")
        adb(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(2)
        
    # Cancel passkey popup nếu có
    root = dump_ui(port, serial)
    cancel_btn = find_elem(root, text_sub="Cancel")
    if cancel_btn:
        cx, cy = get_center(cancel_btn.get('bounds'))
        print(f"[*] Đóng popup Passkey ({cx}, {cy})...")
        adb(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(1.5)
        
    # Chọn Use phone / email / username
    root = dump_ui(port, serial)
    opt_user = find_elem(root, text_sub="Use phone / email / username") or find_elem(root, desc_sub="Use phone / email / username")
    if opt_user:
        cx, cy = get_center(opt_user.get('bounds'))
        print(f"[*] Chọn Use phone/email/username ({cx}, {cy})...")
        adb(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(2)
    else:
        adb(port, serial, ["shell", "input", "tap", "524", "938"])
        time.sleep(2)

    # Chọn tab Email / Username
    root = dump_ui(port, serial)
    tab_email = find_elem(root, text_sub="Email / Username")
    if tab_email:
        cx, cy = get_center(tab_email.get('bounds'))
        print(f"[*] Chọn tab Email/Username ({cx}, {cy})...")
        adb(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(1.5)
    else:
        adb(port, serial, ["shell", "input", "tap", "791", "252"])
        time.sleep(1.5)

    # Nhập Username
    print(f"[*] Nhập username: {username}...")
    adb(port, serial, ["shell", "input", "tap", "540", "432"])
    time.sleep(0.5)
    adb(port, serial, ["shell", "input", "text", username])
    time.sleep(0.5)
    
    # Bấm Continue
    print("[*] Bấm Continue...")
    adb(port, serial, ["shell", "input", "tap", "540", "1128"])
    time.sleep(3)

    # Nhập Password
    print(f"[*] Nhập password cho {username}...")
    adb(port, serial, ["shell", "input", "tap", "500", "521"])
    time.sleep(0.5)
    escaped_pwd = pwd.replace("@", r"\@")
    adb(port, serial, ["shell", "input", "text", escaped_pwd])
    time.sleep(0.5)
    
    # Bấm Continue Password
    print("[*] Gửi thông tin đăng nhập...")
    adb(port, serial, ["shell", "input", "tap", "540", "1128"])
    time.sleep(4)

    # Kiểm tra xem có đòi OTP email không
    root = dump_ui(port, serial)
    verify_node = find_elem(root, text_sub="Verify it") or find_elem(root, text_sub="Email")
    if verify_node:
        print("[!] Phát hiện màn hình Verify it's really you! Bấm chọn Email...")
        adb(port, serial, ["shell", "input", "tap", "539", "673"])
        time.sleep(3)
        
        # Đọc mã OTP từ megacloudx
        otp = fetch_otp(email, email_pwd)
        if otp:
            # Focus box
            adb(port, serial, ["shell", "input", "tap", "885", "760"])
            time.sleep(0.3)
            for _ in range(8):
                adb(port, serial, ["shell", "input", "keyevent", "67"])
                time.sleep(0.05)
            # Nhập mã
            print(f"[*] Điền mã OTP {otp} vào ô...")
            for d in otp:
                adb(port, serial, ["shell", "input", "text", d])
                time.sleep(0.2)
            time.sleep(4)
        else:
            print(f"[-] Không nhận được OTP cho máy {serial}")

    # Nếu sau OTP quay lại màn Password với nút đỏ Continue
    adb(port, serial, ["shell", "input", "tap", "500", "508"])
    time.sleep(4)

    # Xử lý các popups (location, got it, v.v.)
    dismiss_popups(port, serial)
    
    # Bấm Home
    adb(port, serial, ["shell", "input", "keyevent", "3"])
    print(f"[✓] HOÀN TẤT ĐĂNG NHẬP MÁY {acc['id']} ({serial})!\n")

def main():
    print("==================================================")
    print(" BẮT ĐẦU ĐĂNG NHẬP 4 NICK CÒN LẠI VÀO 4 MÁY PROXY ")
    print("==================================================")
    for acc in ACCOUNTS:
        try:
            login_account(acc)
            time.sleep(2)
        except Exception as e:
            print(f"[-] Lỗi trên máy {acc['serial']}: {e}")

if __name__ == "__main__":
    main()
