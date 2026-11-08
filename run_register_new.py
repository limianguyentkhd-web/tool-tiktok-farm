import sys
import os
import subprocess
import time
import random
import string
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DEV = '9889da304447393259'

def sh(cmd):
    return subprocess.run(['adb', '-s', DEV, 'shell'] + cmd, capture_output=True, text=True).stdout

def tap(x, y, delay=0.5):
    sh(['input', 'tap', str(x), str(y)])
    time.sleep(delay)

def clear_and_type(x, y, text):
    tap(x, y, 0.3)
    # select all and delete or backspace 30 times
    for _ in range(30):
        sh(['input', 'keyevent', '67'])
    escaped = text.replace(' ', '%s')
    sh(['input', 'text', escaped])
    time.sleep(0.3)

def save_to_excel(fullname, username, password, status="Thành công"):
    excel_path = r"D:\TOOL TIKTOK\lich_su_tai_khoan_golike.xlsx"
    csv_path = r"D:\TOOL TIKTOK\lich_su_tai_khoan_golike.csv"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    headers = ["STT", "Thời Gian Tạo", "Serial Máy", "Họ Và Tên", "Tên Đăng Nhập", "Mật Khẩu", "Proxy Sử Dụng", "Trạng Thái", "Ghi Chú"]
    
    wb = None
    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
        except Exception:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "TaiKhoan_Golike"
            ws.append(headers)
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "TaiKhoan_Golike"
        ws.append(headers)
    
    stt = ws.max_row
    ws.append([stt, now_str, DEV, fullname, username, password, "Direct", status, "Tự động tạo mới"])
    wb.save(excel_path)
    
    with open(csv_path, "a", encoding="utf-8-sig") as f:
        f.write(f'{stt},"{now_str}","{DEV}","{fullname}","{username}","{password}","Direct","{status}","Tự động tạo mới"\n')
    print(f"[✓] Đã lưu thông tin tài khoản mới vào Excel & CSV!")

# Account info
first_names = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Phan", "Vu", "Dang", "Bui", "Do"]
middle_names = ["Van", "Minh", "Quoc", "Hoang", "Duc", "Thanh", "Dinh"]
last_names = ["Nam", "Long", "Tri", "Huy", "Tuan", "Dat", "Khoi", "Phong", "Bao"]

fullname = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"
rnd_digits = "".join(random.choices(string.digits, k=5))
prefix = "".join(random.choices(string.ascii_lowercase, k=4))
username = f"glk_{prefix}{rnd_digits}"
pwd_digits = "".join(random.choices(string.digits, k=4))
password = f"Golike@{pwd_digits}A"

print(f"=== ĐIỀN THÔNG TIN ĐĂNG KÝ GOLIKE MỚI ===")
print(f"Họ tên: {fullname}")
print(f"Username: {username}")
print(f"Password: {password}")

# 1. Field 1: Họ và tên
clear_and_type(540, 380, fullname)

# 2. Field 2: Tên đăng nhập
clear_and_type(540, 600, username)

# 3. Field 3: Mật khẩu
clear_and_type(540, 810, password)

# 4. Field 4: Nhập lại mật khẩu
clear_and_type(540, 1030, password)

# 5. Hide keyboard
sh(['input', 'tap', '780', '2160'])
time.sleep(0.5)

# 6. Checkbox
print("Tích checkbox điều khoản...")
tap(152, 1575, 0.5)

# 7. Chụp ảnh trước khi bấm Đăng ký
subprocess.run(['cmd', '/c', f'adb -s {DEV} exec-out screencap -p > gl_filled.png'])

# 8. Bấm Đăng ký
print("Bấm nút Đăng ký...")
tap(540, 1785, 4.0)

# 9. Chụp ảnh sau khi bấm Đăng ký
subprocess.run(['cmd', '/c', f'adb -s {DEV} exec-out screencap -p > gl_after_submit.png'])

save_to_excel(fullname, username, password)
print("=== HOÀN TẤT ĐĂNG KÝ ===")
