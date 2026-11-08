import subprocess
import time
import os

adb = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
port = "5038"
serial = "ce011821c45dc4060c"
art_dir = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

def tap(x, y):
    subprocess.run([adb, "-P", port, "-s", serial, "shell", "input", "tap", str(x), str(y)])

def screencap(name):
    outpath = os.path.join(art_dir, name)
    with open(outpath, "wb") as f:
        subprocess.run([adb, "-P", port, "-s", serial, "exec-out", "screencap", "-p"], stdout=f)

# Step 1: Tap edit profile pencil icon at top left (70, 60)
print("Tapping pencil icon...")
tap(70, 60)
time.sleep(2)
screencap("m5_edit_screen.png")
