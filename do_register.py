# -*- coding: utf-8 -*-
import subprocess
import time
import random
import string
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

SERIAL = "9889da304447393259"
ADB_PORT = "5038"
PROXY = "160.250.185.49:14102"

def adb_cmd(args):
    cmd = ["adb", "-P", ADB_PORT, "-s", SERIAL] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

def tap(x, y, delay=0.5):
    adb_cmd(["shell", "input", "tap", str(x), str(y)])
    time.sleep(delay)

def type_text(text, delay=0.5):
    escaped = text.replace(" ", "%s")
    adb_cmd(["shell", "input", "text", escaped])
    time.sleep(delay)

def dump_ui(filename="current_ui.xml"):
    adb_cmd(["shell", "uiautomator", "dump", "/sdcard/dump.xml"])
    subprocess.run(["adb", "-P", ADB_PORT, "-s", SERIAL, "pull", "/sdcard/dump.xml", filename], capture_output=True)
    return filename

def save_to_excel(fullname, username, password, proxy, status, note=""):
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
        
        # Style header
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

    stt = ws.max_row
    row_data = [stt, now_str, SERIAL, fullname, username, password, proxy, status, note]
    ws.append(row_data)
    
    # Border & font cho row mới
    thin = Side(border_style="thin", color="D9D9D9")
    border = Border(top=thin, left=thin, right=thin, bottom=thin)
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=stt + 1, column=col)
        cell.border = border
        cell.alignment = Alignment(horizontal="center" if col in [1, 2, 3, 7, 8] else "left", vertical="center")
        
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    wb.save(excel_path)
    print(f"[✓] Đã lưu vào file Excel: {excel_path}")
    
    # Lưu CSV
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", encoding="utf-8-sig") as f:
        if not file_exists:
            f.write(",".join(headers) + "\n")
        f.write(f'{stt},"{now_str}","{SERIAL}","{fullname}","{username}","{password}","{proxy}","{status}","{note}"\n')
    print(f"[✓] Đã lưu vào file CSV: {csv_path}")

def run():
    print("=== BẮT ĐẦU QUY TRÌNH ĐĂNG KÝ TÀI KHOẢN GOLIKE RANDOM ===")
    
    # 1. Random info
    first_names = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Phan", "Vu", "Dang", "Bui", "Do"]
    middle_names = ["Van", "Minh", "Quoc", "Hoang", "Duc", "Thanh", "Dinh"]
    last_names = ["Nam", "Long", "Tri", "Huy", "Tuan", "Dat", "Khoi", "Phong", "Bao"]
    
    fullname = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"
    
    # Username: e.g. nam_glk7824 hoặc tringuyen9482
    rnd_digits = "".join(random.choices(string.digits, k=5))
    prefix = "".join(random.choices(string.ascii_lowercase, k=4))
    username = f"usr_{prefix}{rnd_digits}"
    
    # Password: upper + lower + numbers + special char
    pwd_digits = "".join(random.choices(string.digits, k=4))
    password = f"Golike@{pwd_digits}A"
    
    print(f"[*] Họ tên: {fullname}")
    print(f"[*] Username: {username}")
    print(f"[*] Password: {password}")
    
    # 2. Nhập các trường
    # Field 1: Họ và tên [97,388][981,493]
    print("[1/5] Điền Họ và tên...")
    tap(539, 440)
    # Clear existing if any
    for _ in range(30):
        adb_cmd(["shell", "input", "keyevent", "67"])
    type_text(fullname)
    time.sleep(0.5)
    
    # Field 2: Tên đăng nhập [97,606][981,711]
    print("[2/5] Điền Tên đăng nhập...")
    tap(539, 658)
    for _ in range(30):
        adb_cmd(["shell", "input", "keyevent", "67"])
    type_text(username)
    time.sleep(0.5)
    
    # Field 3: Mật khẩu [97,824][981,926]
    print("[3/5] Điền Mật khẩu...")
    tap(539, 875)
    for _ in range(30):
        adb_cmd(["shell", "input", "keyevent", "67"])
    type_text(password)
    time.sleep(0.5)
    
    # Field 4: Nhập lại mật khẩu [97,1042][981,1144]
    print("[4/5] Điền Xác nhận mật khẩu...")
    tap(539, 1093)
    for _ in range(30):
        adb_cmd(["shell", "input", "keyevent", "67"])
    type_text(password)
    time.sleep(0.5)
    
    # 3. Kiểm tra checkbox điều khoản
    dump_ui("reg_check_before_submit.xml")
    tree = ET.parse("reg_check_before_submit.xml")
    has_check = False
    for n in tree.iter('node'):
        if n.attrib.get('text') == '\uf00c': # fontawesome checkmark
            has_check = True
            break
            
    if not has_check:
        print("[!] Checkbox chưa tích, tiến hành tích chọn...")
        tap(157, 1606)
        time.sleep(0.5)
    else:
        print("[✓] Checkbox điều khoản đã được tích.")
        
    # 4. Bấm nút Đăng ký [97,1756][981,1887]
    print("[5/5] Bấm nút 'Đăng ký'...")
    tap(539, 1821)
    
    print("[*] Chờ phản hồi từ GoLike...")
    time.sleep(4)
    
    # 5. Chụp ảnh kết quả & dump UI
    result_img = "D:/TOOL TIKTOK/golike_reg_result.png"
    adb_cmd(["shell", "screencap", "-p", "/sdcard/golike_reg_result.png"])
    subprocess.run(["adb", "-P", ADB_PORT, "-s", SERIAL, "pull", "/sdcard/golike_reg_result.png", result_img], capture_output=True)
    
    dump_ui("reg_result_dump.xml")
    result_tree = ET.parse("reg_result_dump.xml")
    
    all_texts = []
    for n in result_tree.iter('node'):
        t = n.attrib.get('text', '').strip()
        d = n.attrib.get('content-desc', '').strip()
        if t:
            all_texts.append(t)
        if d:
            all_texts.append(d)
            
    text_content = " | ".join(all_texts)
    print(f"[*] Text trên màn hình sau đăng ký: {text_content[:200]}...")
    
    status = "Đã đăng ký (Chờ xác nhận)"
    note = "Tự động đăng ký qua tool ADB"
    
    # Kiểm tra xem có thông báo lỗi hay thành công không
    if "thành công" in text_content.lower() or "chúc mừng" in text_content.lower() or "đăng nhập" in text_content.lower():
        status = "Thành công"
        note = "Đăng ký thành công"
        print("[✓] ĐĂNG KÝ THÀNH CÔNG!")
    elif "tồn tại" in text_content.lower():
        status = "Tên đăng nhập đã tồn tại"
        note = "Cần chọn username khác"
        print("[!] Tên đăng nhập đã tồn tại.")
    elif "captcha" in text_content.lower() or "xác thực" in text_content.lower():
        status = "Chờ Captcha"
        note = "Cần xác thực captcha"
        print("[!] Cần xác thực captcha.")
        
    # Lưu vào Excel & CSV
    save_to_excel(fullname, username, password, PROXY, status, note)
    print("\n=== HOÀN TẤT QUY TRÌNH ===")

if __name__ == "__main__":
    run()
