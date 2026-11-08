import sys
import subprocess
import time

sys.stdout.reconfigure(encoding='utf-8')

SERIAL = "9889da304447393259"
PORT = "5039"

def run_adb(args):
    return subprocess.run(["adb", "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True)

def tap(x, y):
    run_adb(["shell", "input", "tap", str(x), str(y)])
    time.sleep(1)

print("Bấm Back để reset form...")
tap(70, 130)
time.sleep(1.5)

print("Bấm Next để vào lại form mã...")
tap(540, 1904)
time.sleep(2)

print("Nhập mã OTP 948162...")
for d in "948162":
    run_adb(["shell", "input", "keyevent", f"KEYCODE_{d}"])
    time.sleep(0.3)

time.sleep(3)
subprocess.run(f"adb -P {PORT} -s {SERIAL} exec-out screencap -p > cur_screen.png", shell=True)
subprocess.run(f'copy cur_screen.png "C:\\Users\\Admin\\.gemini\\antigravity\\brain\\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\\cur_screen.png"', shell=True)
print("Xong!")
