import subprocess
import time
import os

adb_path = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
art_dir = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

def adb(port, serial, cmd_list):
    full_cmd = [adb_path, "-P", port, "-s", serial] + cmd_list
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res.stdout

def tap(port, serial, x, y):
    adb(port, serial, ["shell", "input", "tap", str(x), str(y)])

def screencap(port, serial, name):
    outpath = os.path.join(art_dir, name)
    with open(outpath, "wb") as f:
        subprocess.run([adb_path, "-P", port, "-s", serial, "exec-out", "screencap", "-p"], stdout=f)

# Máy 5
port = "5038"
serial = "ce011821c45dc4060c"

# Dismiss dialog: "Don't allow" is at (330, 575)
print("Dismissing contact sync dialog...")
tap(port, serial, 330, 575)
time.sleep(1)

screencap(port, serial, "m5_after_dismiss.png")
print("Saved m5_after_dismiss.png")
