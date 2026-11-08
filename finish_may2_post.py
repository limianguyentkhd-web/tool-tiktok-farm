import subprocess
import time
import os
import base64

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

def send_vietnamese(text):
    run(["shell", "ime", "enable", "com.android.adbkeyboard/.AdbIME"])
    run(["shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"])
    b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    run(["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])

# 1. Tap Next (1) from album
print("[1] Tapping Next (1)...")
tap(740, 1990)
time.sleep(3.5)

# 2. Tap Next from video editor
print("[2] Tapping Next from editor...")
tap(740, 1990)
time.sleep(3.5)

# 3. Enter caption
print("[3] Entering caption...")
tap(350, 150)
time.sleep(1.0)
caption = "Đơn giản mà vẫn cực kỳ cuốn hút 🌿 Mọi người thấy set này thế nào? #outfit #xuhuongtiktok #douyin #viral "
send_vietnamese(caption)
time.sleep(1.5)

# 4. Hide keyboard
run(["shell", "input", "keyevent", "111"])
time.sleep(1.0)

# 5. Tap Post
print("[4] Tapping Post...")
tap(740, 1990)
time.sleep(5.0)

# Dismiss potential dialogs
tap(300, 880)
time.sleep(1.0)
tap(330, 1280)
time.sleep(2.0)

# Tap Profile tab (900, 2070)
tap(900, 2070)
time.sleep(2.0)

screencap("m2_post_done_final.png")
print("Saved m2_post_done_final.png")
