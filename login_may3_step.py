import subprocess
import time
import os
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

def fetch_otp(email, email_pwd, max_wait=45):
    print(f"[*] Đang lắng nghe OTP cho {email}...")
    start_time = time.time()
    seen = set()
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
                    mid = item.get('id')
                    subj = item.get('subject', '')
                    m = re.search(r'\b(\d{6})\b', subj)
                    if m:
                        print(f"[✓] ĐÃ LẤY ĐƯỢC OTP: {m.group(1)} (từ subject: '{subj}')")
                        return m.group(1)
        except Exception as e:
            pass
    return None

# Step 1: Tap "Use phone / email / username"
print("[1] Tapping Use phone / email / username...")
tap(540, 300)
time.sleep(3.0)

# Step 2: Tap Email / Username tab (790, 252)
print("[2] Tapping Email / Username tab...")
tap(790, 252)
time.sleep(2.0)

# Step 3: Tap username field (540, 432)
print("[3] Entering username...")
tap(540, 432)
time.sleep(0.5)
run(["shell", "input", "text", "user3607950285377"])
time.sleep(1.0)

# Step 4: Tap Continue (540, 1128)
print("[4] Tapping Continue...")
tap(540, 1128)
time.sleep(3.5)

screencap("m3_login_pass_screen.png")
print("Saved m3_login_pass_screen.png")
