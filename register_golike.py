# -*- coding: utf-8 -*-
import subprocess
import time
import random
import string
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime

SERIAL = "9889da304447393259"
ADB_PORT = "5038"

def adb_cmd(args):
    cmd = ["adb", "-P", ADB_PORT, "-s", SERIAL] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

def tap(x, y):
    adb_cmd(["shell", "input", "tap", str(x), str(y)])
    time.sleep(0.5)

def input_text(text):
    # Dùng broadcast ADB keyboard hoặc input text
    # Với ASCII, input text thay khoảng trắng bằng %s
    escaped = text.replace(" ", "%s")
    adb_cmd(["shell", "input", "text", escaped])
    time.sleep(0.5)

def generate_random_account():
    first_names = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Phan", "Vu", "Dang", "Bui", "Do"]
    middle_names = ["Van", "Minh", "Quoc", "Hoang", "Duc", "Thanh", "Dinh"]
    last_names = ["Nam", "Long", "Tri", "Huy", "Tuan", "Dat", "Khoi", "Phong", "Bao"]
    
    fullname = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"
    
    # Username: lowercase alphanumeric 8-12 chars
    rnd_suffix = "".join(random.choices(string.digits, k=5))
    prefix = "".join(random.choices(string.ascii_lowercase, k=5))
    username = f"glk_{prefix}{rnd_suffix}"
    
    # Password: upper + lower + digit + special
    pwd_suffix = "".join(random.choices(string.digits, k=4))
    password = f"Golike@{pwd_suffix}#"
    
    return fullname, username, password

def save_to_excel(fullname, username, password, proxy, status):
    excel_path = r"D:\TOOL TIKTOK\lich_su_tai_khoan_golike.xlsx"
    csv_path = r"D:\TOOL TIKTOK\lich_su_tai_khoan_golike.csv"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    headers = ["STT", "Thời Gian Tạo", "Serial Máy", "Họ Và Tên", "Tên Đăng Nhập", "Mật Khẩu", "Proxy Sử Dụng", "Trạng Thái", "Ghi Chú"]
    row_data = [now_str, SERIAL, fullname, username, password, proxy, status, "Tự động đăng ký qua Tool ADB"]
    
    # 1. Ghi Excel
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
        
        # Style header
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            
    stt = ws.max_row  # vì đã có header nên max_row hiện tại là số thứ tự dòng mới
    ws.append([stt] + row_data)
    
    # Tự động căn chỉnh độ rộng cột
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    wb.save(excel_path)
    print(f"[✓] Đã lưu vào Excel: {excel_path}")
    
    # 2. Ghi CSV backup
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", encoding="utf-8-sig") as f:
        if not file_exists:
            f.write(",".join(headers) + "\n")
        f.write(f'{stt},"{now_str}","{SERIAL}","{fullname}","{username}","{password}","{proxy}","{status}","Tự động đăng ký qua Tool ADB"\n')
    print(f"[✓] Đã lưu vào CSV: {csv_path}")

if __name__ == "__main__":
    fn, un, pw = generate_random_account()
    print(f"Họ tên: {fn}")
    print(f"Username: {un}")
    print(f"Password: {pw}")
