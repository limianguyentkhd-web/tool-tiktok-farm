import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')
DEV = '9889da304447393259'

def sh(cmd):
    return subprocess.run(['adb', '-s', DEV, 'shell'] + cmd, capture_output=True, text=True).stdout

def tap(x, y, delay=0.5):
    sh(['input', 'tap', str(x), str(y)])
    time.sleep(delay)

def type_text(x, y, text):
    tap(x, y, 0.3)
    for _ in range(30):
        sh(['input', 'keyevent', '67'])
    sh(['input', 'text', text])
    time.sleep(0.3)

un = "glk_ntbi12803"
pw = "Golike@1026A"

print(f"Logging in as {un}...")
# 1. Username
type_text(540, 740, un)

# 2. Password
type_text(540, 930, pw)

# 3. Dismiss keyboard
sh(['input', 'tap', '780', '2160'])
time.sleep(0.5)

# 4. Tap Đăng nhập at (500, 1560)
print("Tapping Đăng nhập...")
tap(500, 1560, 4.0)

subprocess.run(['cmd', '/c', f'adb -s {DEV} exec-out screencap -p > gl_logged_new.png'])
print("Done login attempt!")
