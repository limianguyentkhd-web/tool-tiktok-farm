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

# Step 1: Tap Upload button at (540, 1242)
print("[1] Tapping Upload button...")
tap(540, 1242)
time.sleep(2.5)

# Step 2: Tap Videos tab (268, 248)
print("[2] Tapping Videos tab...")
tap(268, 248)
time.sleep(2.0)

# Step 3: Select first video circle (290, 380) or let's tap (290, 380)
print("[3] Selecting first video...")
tap(290, 380)
time.sleep(1.0)

# Step 4: Tap Next (740, 1990)
print("[4] Tapping Next from album...")
tap(740, 1990)
time.sleep(3.5)

# Step 5: Tap Next from editor (740, 1990)
print("[5] Tapping Next from editor...")
tap(740, 1990)
time.sleep(3.5)

# Step 6: Enter caption
print("[6] Entering caption...")
tap(350, 150)
time.sleep(1.0)
caption = "Set đồ basic nhưng lên dáng cực kỳ tôn da nha 🌸 #reviewthoitrang #xuhuong #ootdvietnam #douyin "
send_vietnamese(caption)
time.sleep(1.5)

# Step 7: Hide keyboard
run(["shell", "input", "keyevent", "111"])
time.sleep(1.0)

# Step 8: Tap Post
print("[7] Tapping Post...")
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

screencap("m4_posted_verified.png")
print("Saved m4_posted_verified.png")
