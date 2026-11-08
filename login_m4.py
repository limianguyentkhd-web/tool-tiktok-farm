import urllib.request
import ssl
import json
import time
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

port = "5037"
serial = "ce011821c38b263b05"
user = "user5878212175691"
pwd = r"\@L206ThnU0ortn"
email = "lcqskhcot3161@primehubcloud.com"
email_pwd = "wQMUXKm4I"

def adb(cmd):
    full = [ADB, "-P", port, "-s", serial] + cmd
    return subprocess.run(full, capture_output=True, text=True, errors="replace").stdout.strip()

print("[*] 1. Tapping Continue with email/username...")
adb(["shell", "input", "tap", "540", "1180"])
time.sleep(2)

print("[*] 2. Tapping Email/username field...")
adb(["shell", "input", "tap", "540", "700"])
time.sleep(1)
adb(["shell", "input", "text", user])
time.sleep(1)

print("[*] 3. Tapping Log in...")
adb(["shell", "input", "tap", "540", "868"])
time.sleep(2)

print("[*] 4. Typing password...")
adb(["shell", "input", "text", pwd])
time.sleep(1)

print("[*] 5. Tapping Continue button...")
adb(["shell", "input", "tap", "540", "1890"])
time.sleep(5)

# Check OTP / verification
print("[*] 6. Tapping Email verification row if present...")
adb(["shell", "input", "tap", "540", "700"])
time.sleep(3)

print("[*] 7. Polling OTP from megacloudx.com...")
url = f"https://megacloudx.com/api/messages?inbox={email}&password={email_pwd}"
otp = None
for _ in range(12):
    time.sleep(3)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx)
        data = json.loads(resp.read().decode('utf-8'))
        results = data.get('results', [])
        if results:
            subj = results[0].get('subject', '')
            m = re.search(r'\b(\d{6})\b', subj)
            if m:
                otp = m.group(1)
                print(f"[+] Found OTP: {otp} (Subject: {subj})")
                break
    except Exception as e:
        print("Polling error:", e)

if otp:
    print(f"[*] Typing OTP {otp}...")
    adb(["shell", "input", "text", otp])
    time.sleep(4)

adb(["shell", "screencap", "-p", "/sdcard/m4_logged_in.png"])
adb(["pull", "/sdcard/m4_logged_in.png", "d:\\TOOL TIKTOK\\m4_logged_in.png"])
print("[+] Finished login process for May 4!")
