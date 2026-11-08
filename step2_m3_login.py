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

def run(args):
    return subprocess.run([ADB, "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True, errors="replace")

def tap(x, y):
    run(["shell", "input", "tap", str(x), str(y)])

def screencap(name):
    outpath = os.path.join(ART_DIR, name)
    with open(outpath, "wb") as f:
        subprocess.run([ADB, "-P", PORT, "-s", SERIAL, "exec-out", "screencap", "-p"], stdout=f)

# 1. Tap Email / Username tab (792, 253)
print("[1] Tapping Email / Username tab...")
tap(792, 253)
time.sleep(2.0)

# 2. Tap Username text box (500, 420)
print("[2] Tapping Username text box...")
tap(500, 420)
time.sleep(1.0)

# 3. Enter username
username = "user3607950285377"
print(f"[3] Entering {username}...")
run(["shell", "input", "text", username])
time.sleep(1.5)

# 4. Tap Continue (540, 1950) or check where Continue is
# Let's dump UI to see where Continue is and what else is on screen
screencap("m3_username_entered.png")
