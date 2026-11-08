import subprocess
import time
import os
import base64

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
PORT = "5037"
SERIAL = "ce011821c38b263b05"
ART_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

def run(args):
    return subprocess.run([ADB, "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True, errors="replace")

def tap(x, y):
    run(["shell", "input", "tap", str(x), str(y)])

def screencap(name):
    outpath = os.path.join(ART_DIR, name)
    with open(outpath, "wb") as f:
        subprocess.run([ADB, "-P", PORT, "-s", SERIAL, "exec-out", "screencap", "-p"], stdout=f)

def send_vietnamese(text):
    run(["shell", "ime", "enable", "com.android.adbkeyboard/.AdbIME"])
    run(["shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"])
    b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    run(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])

# Step 1: Dismiss "Viewer history turned on" modal
print("[1] Dismissing sheet...")
tap(540, 1950)
time.sleep(1.5)

# Step 2: Open Edit profile (76, 131)
print("[2] Opening Edit Profile...")
tap(76, 131)
time.sleep(2.0)

# Step 3: Tap username row (500, 850)
print("[3] Tapping Username row...")
tap(500, 850)
time.sleep(2.0)

# Step 4: Clear old username
run(["shell", "input", "tap", "895", "310"])
time.sleep(0.3)
run(["shell", "input", "keycombination", "113", "29"])
time.sleep(0.2)
run(["shell", "input", "keyevent", "67"])
time.sleep(0.5)

# Step 5: Type bachvan.daily26
user_target = "bachvan.daily26"
print(f"[4] Typing {user_target}...")
run(["shell", "input", "text", user_target])
time.sleep(1.5)

# Step 6: Save (990, 120)
print("[5] Tapping Save...")
tap(990, 120)
time.sleep(1.5)

# Step 7: Confirm (723, 1235)
print("[6] Tapping Confirm...")
tap(723, 1235)
time.sleep(2.0)

# Back to profile
run(["shell", "input", "keyevent", "4"])
time.sleep(1.5)

screencap("m4_profile_updated.png")
print("Saved m4_profile_updated.png")
