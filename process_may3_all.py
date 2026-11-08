import subprocess
import time
import os
import base64
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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

def send_vietnamese(text):
    run(["shell", "ime", "enable", "com.android.adbkeyboard/.AdbIME"])
    run(["shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"])
    b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    run(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])

# Step 1: Dismiss "Don't allow" dialog
print("[1] Dismissing sync dialog...")
tap(330, 1275)
time.sleep(1.5)

# Step 2: Tap Profile tab (900, 2070)
print("[2] Opening Profile tab...")
tap(900, 2070)
time.sleep(2.0)

# Dismiss viewer history sheet if present
tap(540, 1950)
time.sleep(1.0)

# Step 3: Open Edit profile (76, 131)
print("[3] Opening Edit Profile...")
tap(76, 131)
time.sleep(2.0)

# Step 4: Tap Username row (500, 850)
print("[4] Tapping Username row...")
tap(500, 850)
time.sleep(2.0)

# Clear old username
run(["shell", "input", "tap", "895", "310"])
time.sleep(0.3)
run(["shell", "input", "keycombination", "113", "29"])
time.sleep(0.2)
run(["shell", "input", "keyevent", "67"])
time.sleep(0.5)

# Type new username: minhtuan.vibes26
user_target = "minhtuan.vibes26"
print(f"[5] Typing {user_target}...")
run(["shell", "input", "text", user_target])
time.sleep(1.5)

# Tap Save (990, 120)
print("[6] Tapping Save...")
tap(990, 120)
time.sleep(1.5)

# Tap Confirm (723, 1235)
print("[7] Tapping Confirm...")
tap(723, 1235)
time.sleep(2.0)

# Back to Profile
run(["shell", "input", "keyevent", "4"])
time.sleep(1.5)

screencap("m3_profile_after_user.png")
print("Profile updated! Now posting video...")

# Step 5: Post Video
# Tap red Upload button in middle (540, 1242) or + button (540, 2030)
tap(540, 1242)
time.sleep(2.5)

# Tap Videos tab (268, 248)
tap(268, 248)
time.sleep(2.0)

# Select first video circle (290, 380)
tap(290, 380)
time.sleep(1.0)

# Tap Next from album (740, 1990)
tap(740, 1990)
time.sleep(3.5)

# Tap Next from editor (740, 1990)
tap(740, 1990)
time.sleep(3.5)

# Enter caption
tap(350, 150)
time.sleep(1.0)
caption = "Một chút năng lượng tích cực cho ngày mới nè các bác ơi 💕 #ootdfashion #trending #viral #fyp "
send_vietnamese(caption)
time.sleep(1.5)

# Hide keyboard
run(["shell", "input", "keyevent", "111"])
time.sleep(1.0)

# Tap Post (740, 1990)
tap(740, 1990)
time.sleep(5.0)

# Dismiss popups
tap(300, 880)
time.sleep(1.0)
tap(330, 1280)
time.sleep(2.0)

# Tap Profile tab
tap(900, 2070)
time.sleep(2.0)

screencap("m3_posted_verified.png")
print("Saved m3_posted_verified.png!")
