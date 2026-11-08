import subprocess
import time
import os
import urllib.request
import ssl
import json
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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

def fetch_otp(email, email_pwd, max_wait=50):
    print(f"[*] Cho doc OTP cho {email}...")
    start_time = time.time()
    seen_ids = set()
    # Baseline
    try:
        url = f"https://megacloudx.com/api/messages?inbox={email}&password={email_pwd}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode())
        for item in data.get('results', []):
            seen_ids.add(item.get('id'))
    except Exception as e:
        print(f"[-] Init err: {e}")

    while time.time() - start_time < max_wait:
        time.sleep(3)
        try:
            url = f"https://megacloudx.com/api/messages?inbox={email}&password={email_pwd}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                data = json.loads(r.read().decode())
            results = data.get('results', [])
            for item in results:
                mid = item.get('id')
                subj = item.get('subject', '')
                if mid not in seen_ids:
                    m = re.search(r'\b(\d{6})\b', subj)
                    if m:
                        code = m.group(1)
                        print(f"[+] TIM THAY OTP MOI: {code} (subject: {subj})")
                        return code
        except Exception as e:
            pass

    # Fallback to newest msg
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
                print(f"[+] Fallback OTP: {m.group(1)}")
                return m.group(1)
    except:
        pass
    return None

# Step 1: Tap Email box (540, 300)
print("[1] Tapping Email row to send OTP...")
tap(540, 300)
time.sleep(2.0)

screencap("m3_otp_screen.png")

# Step 2: Fetch OTP
otp = fetch_otp("hmpqybusgl4490@trustlark.com", "A0u8fcAxn", max_wait=40)

if otp:
    print(f"[2] Entering OTP digits: {otp}...")
    for d in otp:
        run(["shell", "input", "text", d])
        time.sleep(0.3)
    time.sleep(4.0)
else:
    print("[-] Khong nhan duoc OTP!")

screencap("m3_logged_in_verified.png")
print("Saved m3_logged_in_verified.png")
