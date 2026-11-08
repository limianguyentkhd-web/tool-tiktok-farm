import subprocess
import time
import os

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
PORT = "5037"
SERIAL = "ce01182188dbdcee0c"
ART_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

def run(args):
    return subprocess.run([ADB, "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True, errors="replace")

def screencap(name):
    outpath = os.path.join(ART_DIR, name)
    with open(outpath, "wb") as f:
        subprocess.run([ADB, "-P", PORT, "-s", SERIAL, "exec-out", "screencap", "-p"], stdout=f)

print("Stopping Chrome...")
run(["shell", "am", "force-stop", "com.android.chrome"])

print("Stopping and relaunching TikTok...")
run(["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
time.sleep(1.0)
run(["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
time.sleep(4.5)

screencap("m3_relaunch.png")
print("Saved m3_relaunch.png")
