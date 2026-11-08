import sys
import os
import subprocess
import time
import random
import string
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

DEV = '9889da304447393259'

def sh(cmd):
    return subprocess.run(['adb', '-s', DEV, 'shell'] + cmd, capture_output=True, text=True).stdout

def tap(x, y, delay=0.5):
    sh(['input', 'tap', str(x), str(y)])
    time.sleep(delay)

def type_text(text, delay=0.5):
    # clear field first
    for _ in range(25):
        sh(['input', 'keyevent', '67'])
    escaped = text.replace(' ', '%s')
    sh(['input', 'text', escaped])
    time.sleep(delay)

# Generate account
first_names = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Phan", "Vu", "Dang", "Bui", "Do"]
middle_names = ["Van", "Minh", "Quoc", "Hoang", "Duc", "Thanh", "Dinh"]
last_names = ["Nam", "Long", "Tri", "Huy", "Tuan", "Dat", "Khoi", "Phong", "Bao"]

fullname = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"
rnd_digits = "".join(random.choices(string.digits, k=5))
prefix = "".join(random.choices(string.ascii_lowercase, k=4))
username = f"glk_{prefix}{rnd_digits}"
pwd_digits = "".join(random.choices(string.digits, k=4))
password = f"Golike@{pwd_digits}A"

print(f"=== TẠO TÀI KHOẢN MỚI ===")
print(f"Họ và tên: {fullname}")
print(f"Tên đăng nhập: {username}")
print(f"Mật khẩu: {password}")

# Field 1: Họ và tên at (540, 397)
print("1. Điền Họ và tên...")
tap(540, 397)
type_text(fullname)

# Field 2: Tên đăng nhập at (540, 495)
print("2. Điền Tên đăng nhập...")
tap(540, 495)
type_text(username)

# Field 3: Mật khẩu at (540, 594)
print("3. Điền Mật khẩu...")
tap(540, 594)
type_text(password)

# Field 4: Nhập lại mật khẩu at (540, 692)
print("4. Điền Nhập lại mật khẩu...")
tap(540, 692)
type_text(password)

# Hide keyboard: tap neutral area (50, 500)
sh(['input', 'tap', '50', '500'])
time.sleep(1)

# Checkbox at (152, 925)
print("5. Tích đồng ý điều khoản...")
tap(152, 925)
time.sleep(1)

# Chụp ảnh trước khi submit
subprocess.run(['cmd', '/c', f'adb -s {DEV} exec-out screencap -p > gl_before_reg.png'])

# Cuộn xuống nhẹ để thấy nút Đăng ký nếu cần
sh(['input', 'swipe', '540', '1400', '540', '1000', '200'])
time.sleep(1)

subprocess.run(['cmd', '/c', f'adb -s {DEV} exec-out screencap -p > gl_before_submit.png'])
