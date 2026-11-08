import subprocess
import time
import os

adb = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
port = "5038"
serial = "ce011821c45dc4060c"
art_dir = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

def run(cmd_list):
    return subprocess.run([adb, "-P", port, "-s", serial] + cmd_list, capture_output=True, text=True)

def screencap(name):
    outpath = os.path.join(art_dir, name)
    with open(outpath, "wb") as f:
        subprocess.run([adb, "-P", port, "-s", serial, "exec-out", "screencap", "-p"], stdout=f)

# Tap clear button 'x' at (895, 310)
print("Clearing text...")
run(["shell", "input", "tap", "895", "310"])
time.sleep(0.5)

# Also select all and delete just in case
run(["shell", "input", "keycombination", "113", "29"])
time.sleep(0.2)
run(["shell", "input", "keyevent", "67"])
time.sleep(0.5)

# Type new username: thuytrang.daily
new_user = "thuytrang.daily"
print(f"Typing {new_user}...")
run(["shell", "input", "text", new_user])
time.sleep(1.5)

screencap("m5_user_typed.png")
