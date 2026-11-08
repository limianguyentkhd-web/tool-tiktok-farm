import subprocess
import time
import os
import base64
import urllib.request
import ssl
import json
import re

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
PORT = "5037"
SERIAL = "ce01182188dbdcee0c"
ART_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def run(args):
    return subprocess.run([ADB, "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True, errors="replace")

def tap(x, y):
    run(["shell", "input", "tap", str(x), str(y)])

def screencap(name):
    outpath = os.path.join(ART_DIR, name)
    with open(outpath, "wb") as f:
        subprocess.run([ADB, "-P", PORT, "-s", SERIAL, "exec-out", "screencap", "-p"], stdout=f)

def fetch_otp(email, email_pwd, max_wait=35):
    print(f"[*] Đang lắng nghe OTP cho {email}...")
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
                for item in results:
                    subj = item.get('subject', '')
                    m = re.search(r'\b(\d{6})\b', subj)
                    if m:
                        print(f"[✓] ĐÃ LẤY ĐƯỢC OTP: {m.group(1)} (từ subject: '{subj}')")
                        return m.group(1)
        except Exception as e:
            pass
    return None

# 1. Type password
pwd = "@L63aGrj5m9POZ"
print("[1] Entering password...")
tap(400, 235)
time.sleep(0.5)
escaped = pwd.replace("@", r"\@")
run(["shell", "input", "text", escaped])
time.sleep(1.0)

# 2. Tap Continue (540, 1993)
print("[2] Tapping Continue...")
tap(540, 1993)
time.sleep(4.0)

screencap("m3_after_login_click.png")

# Check if OTP requested
otp = fetch_otp("hmpqybusgl4490@trustlark.com", "A0u8fcAxn", max_wait=20)
if otp:
    print(f"[+] Entering OTP: {otp}")
    for d in otp:
        run(["shell", "input", "text", d])
        time.sleep(0.2)
    time.sleep(4.0)

screencap("m3_final_login_result.png")
print("Saved screenshots.")
