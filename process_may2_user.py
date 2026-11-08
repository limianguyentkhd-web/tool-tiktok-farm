import subprocess
import time
import os
import base64
import xml.etree.ElementTree as ET

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
PORT = "5038"
SERIAL = "988a17344c564b5657"
ART_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

def run(args):
    return subprocess.run([ADB, "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True, errors="replace")

def tap(x, y):
    run(["shell", "input", "tap", str(x), str(y)])

def screencap(name):
    outpath = os.path.join(ART_DIR, name)
    with open(outpath, "wb") as f:
        subprocess.run([ADB, "-P", PORT, "-s", SERIAL, "exec-out", "screencap", "-p"], stdout=f)

def dump_ui(name="dump.xml"):
    run(["shell", "uiautomator", "dump", f"/sdcard/{name}"])
    local = os.path.join(ART_DIR, name)
    run(["pull", f"/sdcard/{name}", local])
    return local

# STEP 1: CHANGE USERNAME
print("[1] Opening Edit Profile...")
tap(76, 131)
time.sleep(2)

print("[2] Tapping Username row (500, 850)...")
tap(500, 850)
time.sleep(2)

# Clear old username
run(["shell", "input", "tap", "895", "310"])
time.sleep(0.3)
run(["shell", "input", "keycombination", "113", "29"])
time.sleep(0.2)
run(["shell", "input", "keyevent", "67"])
time.sleep(0.5)

# Try thuyhuyen.ootd26 directly or thuyhuyen.ootd
user_target = "thuyhuyen.ootd26"
print(f"[3] Typing {user_target}...")
run(["shell", "input", "text", user_target])
time.sleep(1.5)

# Tap Save (990, 120)
print("[4] Tapping Save...")
tap(990, 120)
time.sleep(1.5)

# Tap Confirm (723, 1235)
print("[5] Tapping Confirm...")
tap(723, 1235)
time.sleep(2.0)

# Back to Profile
run(["shell", "input", "keyevent", "4"])
time.sleep(1.5)

screencap("m2_profile_updated.png")
print("Saved m2_profile_updated.png")
