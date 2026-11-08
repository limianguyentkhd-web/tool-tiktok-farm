import subprocess
import time
import os

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

# Step 1: Open profile
print("[1] Opening Profile...")
tap(900, 2070)
time.sleep(2.0)

# Step 2: Open edit profile
print("[2] Opening Edit Profile...")
tap(76, 131)
time.sleep(2.0)

# Step 3: Tap username row
print("[3] Tapping Username row...")
tap(500, 850)
time.sleep(2.0)

# Clear old username
run(["shell", "input", "tap", "895", "310"])
time.sleep(0.3)
run(["shell", "input", "keycombination", "113", "29"])
time.sleep(0.2)
run(["shell", "input", "keyevent", "67"])
time.sleep(0.5)

# Type new username
user_target = "minhtuan.vibes26"
print(f"[4] Typing {user_target}...")
run(["shell", "input", "text", user_target])
time.sleep(1.5)

# Tap Save
print("[5] Tapping Save...")
tap(990, 120)
time.sleep(1.5)

# Tap Confirm
print("[6] Tapping Confirm...")
tap(723, 1235)
time.sleep(2.0)

# Back to Profile
run(["shell", "input", "keyevent", "4"])
time.sleep(1.5)

screencap("m3_profile_updated.png")
print("Saved m3_profile_updated.png")
