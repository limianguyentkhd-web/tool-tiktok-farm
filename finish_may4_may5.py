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

ACCOUNTS_REMAINING = [
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
    adb(port, serial, ["shell", "uiautomator", "dump", "/sdcard/d2.xml"])
    res = adb(port, serial, ["shell", "cat", "/sdcard/d2.xml"])
    try:
        return ET.fromstring(res)
    except:
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
        except Exception:
            pass
    return None

def login_device(acc):
    port = acc["port"]
    serial = acc["serial"]
    username = acc["user"]
    pwd = acc["pass"]
    email = acc["email"]
    email_pwd = acc["email_pwd"]
    
    print(f"\n[*] Đang đăng nhập Máy {acc['id']} ({serial}) - Nick: {username}")
    
    # 1. Tap Continue with email / username
    print("[1] Bấm 'Continue with email / username' (540, 1140)...")
    adb(port, serial, ["shell", "input", "tap", "540", "1140"])
    time.sleep(2)
    
    # Check if Email/Username tab needs to be selected
    adb(port, serial, ["shell", "input", "tap", "791", "252"])
    time.sleep(1)
    
    # 2. Enter username
    print(f"[2] Nhập username {username}...")
    adb(port, serial, ["shell", "input", "tap", "540", "432"])
    time.sleep(0.5)
    adb(port, serial, ["shell", "input", "text", username])
    time.sleep(0.5)
    
    # 3. Tap Continue
    adb(port, serial, ["shell", "input", "tap", "540", "1128"])
    time.sleep(3)
    
    # 4. Enter password
    print(f"[3] Nhập password...")
    adb(port, serial, ["shell", "input", "tap", "500", "521"])
    time.sleep(0.5)
    escaped = pwd.replace("@", r"\@")
    adb(port, serial, ["shell", "input", "text", escaped])
    time.sleep(0.5)
    
    # 5. Tap Continue
    adb(port, serial, ["shell", "input", "tap", "540", "1128"])
    time.sleep(4)
    
    # 6. Check for OTP
    root = dump_ui(port, serial)
    xml_str = adb(port, serial, ["shell", "cat", "/sdcard/d2.xml"])
    if "Verify it" in xml_str or "Email" in xml_str:
        print("[!] Có bước Verify Email OTP, bấm chọn Email...")
        adb(port, serial, ["shell", "input", "tap", "539", "673"])
        time.sleep(3)
        otp = fetch_otp(email, email_pwd)
        if otp:
            # Clear boxes
            adb(port, serial, ["shell", "input", "tap", "885", "760"])
            time.sleep(0.3)
            for _ in range(8):
                adb(port, serial, ["shell", "input", "keyevent", "67"])
                time.sleep(0.05)
            print(f"[*] Nhập mã OTP {otp}...")
            for d in otp:
                adb(port, serial, ["shell", "input", "text", d])
                time.sleep(0.2)
            time.sleep(4)
            
    # Red Continue on password screen if needed
    adb(port, serial, ["shell", "input", "tap", "500", "508"])
    time.sleep(3)
    
    # Dismiss location & policies
    adb(port, serial, ["shell", "input", "tap", "723", "1310"]) # Allow
    time.sleep(1)
    adb(port, serial, ["shell", "input", "tap", "540", "1409"]) # Got it
    time.sleep(1)
    adb(port, serial, ["shell", "input", "tap", "500", "1160"]) # Agree and continue
    time.sleep(1)
    
    # Press Home
    adb(port, serial, ["shell", "input", "keyevent", "3"])
    print(f"[✓] HOÀN TẤT MÁY {acc['id']} ({serial})!")

for acc in ACCOUNTS_REMAINING:
    login_device(acc)
    time.sleep(2)

print("\n[✓] TẤT CẢ CÁC MÁY ĐÃ ĐƯỢC XỬ LÝ XONG!")
