#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOLIKE TIKTOK AUTO BOT
======================
Tự động hóa hoàn toàn kiếm tiền TikTok trên GoLike Android:
- Tự động nhận job (Follow / Like).
- Tự động vượt Captcha kéo khối thông minh (Quadratic Bézier curve).
- Tự động nhận diện nút [Hoàn thành] chống anti-bot đảo vị trí của GoLike.
- Tự động đóng tất cả popups, điều khoản, thông báo.
- Chuyển tab GoLike <-> TikTok mượt mà bằng Single Top intent.
"""

import subprocess
import time
import os
import sys
import re
import argparse
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

DEVICE = 'ce031713dba2c72101'
TEMP_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_PATH = r'C:\Program Files (x86)\xiaowei_android\tools\adb.exe'
if not os.path.exists(ADB_PATH):
    ADB_PATH = 'adb'

def adb_shell(cmd):
    res = subprocess.run([ADB_PATH, '-s', DEVICE, 'shell', cmd], capture_output=True, encoding='utf-8', errors='ignore')
    return res.stdout

def tap(x, y):
    adb_shell(f'input tap {x} {y}')

def screenshot(filename='screen_temp.png'):
    path = os.path.join(TEMP_DIR, filename)
    res = subprocess.run([ADB_PATH, '-s', DEVICE, 'exec-out', 'screencap', '-p'], capture_output=True)
    with open(path, 'wb') as f:
        f.write(res.stdout)
    return path

def get_ui():
    adb_shell('uiautomator dump /data/local/tmp/dump.xml')
    xml_str = adb_shell('cat /data/local/tmp/dump.xml')
    try:
        return ET.fromstring(xml_str)
    except:
        return None

def get_center(bounds_str):
    m = re.findall(r'\d+', bounds_str)
    if len(m) == 4:
        return (int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2
    return 540, 1000

def solve_visual_captcha():
    print('  [Captcha] Phát hiện captcha kéo khối GoLike! Đang tính toán toạ độ và vẽ quỹ đạo Bézier...')
    path = screenshot('cap_temp.png')
    arr = np.array(Image.open(path))
    
    # 1. Khối vuông xanh lam bắt đầu
    b_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] < 150) & (arr[:, :, 2] > 200)
    by, bx = np.where(b_mask)
    if len(bx) == 0:
        return False
    p0 = (int(np.mean(bx)), int(np.mean(by)))
    
    # 2. Vòng tròn xanh lá đích
    g_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] > 150) & (arr[:, :, 2] < 100)
    gy, gx = np.where(g_mask)
    if len(gx) == 0:
        return False
    p2 = (int(np.mean(gx)), int(np.mean(gy)))
    
    # 3. Vòng tròn nét đứt trung gian
    d_mask = (arr[:, :, 0] > 125) & (arr[:, :, 0] < 185) & (arr[:, :, 1] > 145) & (arr[:, :, 1] < 205) & (arr[:, :, 2] > 170) & (arr[:, :, 2] < 225)
    d_mask[:850, :] = False
    d_mask[1450:, :] = False
    d_mask[:, :300] = False
    d_mask[:, 850:] = False
    dy, dx = np.where(d_mask)
    p1 = (int(np.mean(dx)), int(np.mean(dy))) if len(dx) > 0 else ((p0[0] + p2[0]) // 2, (p0[1] + p2[1]) // 2)
    
    commands = [f'input motionevent DOWN {p0[0]} {p0[1]}', 'sleep 0.1']
    for i in range(1, 31):
        t = i / 30.0
        x = int((1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0])
        y = int((1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1])
        commands.append(f'input motionevent MOVE {x} {y}')
        commands.append('sleep 0.02')
    commands.append('sleep 0.15')
    commands.append(f'input motionevent UP {p2[0]} {p2[1]}')
    
    local_sh = os.path.join(TEMP_DIR, 'cap_runner.sh')
    with open(local_sh, 'w', newline='\n') as f:
        f.write('\n'.join(commands) + '\n')
    subprocess.run([ADB_PATH, '-s', DEVICE, 'push', local_sh, '/data/local/tmp/cap_runner.sh'], stdout=subprocess.DEVNULL)
    adb_shell('sh /data/local/tmp/cap_runner.sh')
    time.sleep(3.5)
    print('  [Captcha] Đã vượt Captcha thành công!')
    return True

def handle_popups():
    root = get_ui()
    if root is None:
        return
        
    for n in root.iter():
        txt = n.attrib.get('text', '').strip()
        # Popup điều khoản làm việc bằng App
        if 'Xác nhận làm việc' in txt:
            print('  [Popup] Tự động tích đồng ý điều khoản làm việc...')
            tap(85, 1373)
            time.sleep(0.5)
            tap(913, 1560)
            time.sleep(2)
            root = get_ui()
            break
            
        # Popup thông báo / thành công
        if txt == 'OK':
            print('  [Popup] Đóng modal thông báo (OK)...')
            tap(*get_center(n.attrib.get('bounds')))
            time.sleep(2)
            root = get_ui()
            break

    # Kiểm tra captcha xuất hiện bất chợt
    if root is not None:
        for n in root.iter():
            txt = n.attrib.get('text', '')
            if 'Kéo khối vuông' in txt or 'Xác minh nhanh' in txt:
                solve_visual_captcha()
                time.sleep(2)
                break

def execute_single_job(job_index, total_jobs):
    print(f'\n==================================================')
    print(f'>>> THỰC HIỆN JOB #{job_index}/{total_jobs}')
    print(f'==================================================')
    
    handle_popups()
    
    # 1. Nhận job nếu ở màn danh sách job
    root = get_ui()
    nhan_btn = None
    for n in root.iter() if root is not None else []:
        txt = n.attrib.get('text', '').strip()
        if 'Nhận Job ngay' in txt or 'Nhận Job' in txt:
            nhan_btn = n
            break
            
    if nhan_btn is not None:
        nx, ny = get_center(nhan_btn.attrib.get('bounds'))
        print(f'  [1] Bấm [Nhận Job ngay] tại ({nx}, {ny})...')
        tap(nx, ny)
        time.sleep(3)
        handle_popups()
        time.sleep(2)

    # 2. Chờ màn hình chi tiết Job xuất hiện (tìm nút Hoàn thành)
    tt_btn = None
    ht_btn = None
    job_type = 'TĂNG LƯỢT THEO DÕI'
    reward_pts = ''
    
    for wait_turn in range(6):
        root = get_ui()
        if root is not None:
            for n in root.iter():
                txt = n.attrib.get('text', '').strip()
                cls = n.attrib.get('class', '')
                bounds = n.attrib.get('bounds', '')
                
                # Nút TikTok trong khung việc
                if txt == 'TikTok' and 700 < get_center(bounds)[1] < 1000:
                    tt_btn = n
                # Nút Hoàn thành chống anti-bot tráo đổi vị trí
                if cls == 'android.widget.Button' and txt == 'Hoàn thành':
                    ht_btn = n
                if 'TĂNG' in txt:
                    job_type = txt
                if 'điểm' in txt:
                    reward_pts = txt
                    
        if ht_btn is not None and tt_btn is not None:
            break
        print('  [Chờ] Đang tải chi tiết nhiệm vụ từ máy chủ GoLike...')
        handle_popups()
        time.sleep(2)

    if ht_btn is None or tt_btn is None:
        print('  [Cảnh báo] Chưa load được chi tiết job (có thể hết job hoặc hệ thống đang tìm việc).')
        return False

    tt_x, tt_y = get_center(tt_btn.attrib.get('bounds'))
    ht_x, ht_y = get_center(ht_btn.attrib.get('bounds'))
    
    print(f'  [Thông tin Job] Loại: {job_type} | Thưởng: {reward_pts}')
    print(f'  [Toạ độ động] Nút TikTok: ({tt_x}, {tt_y}) | Nút Hoàn thành: ({ht_x}, {ht_y})')

    # 3. Mở TikTok
    print('  [2] Mở TikTok...')
    tap(tt_x, tt_y)
    time.sleep(4.5)

    # 4. Tương tác TikTok
    print('  [3] Thực hiện tương tác trên TikTok...')
    tt_root = get_ui()
    action_done = False
    if tt_root is not None:
        for n in tt_root.iter():
            txt = n.attrib.get('text', '').strip()
            if txt == 'Follow':
                fx, fy = get_center(n.attrib.get('bounds'))
                print(f'    -> Phát hiện nút Follow tại ({fx}, {fy}), tiến hành Follow!')
                tap(fx, fy)
                action_done = True
                break
                
    if not action_done:
        print('    -> Không tìm thấy Follow (có thể là Job Like), Double Tap vào video để Like...')
        tap(540, 1000)
        time.sleep(0.12)
        tap(540, 1000)

    time.sleep(3.5)

    # 5. Quay lại GoLike
    print('  [4] Chuyển về GoLike (Single Top task)...')
    adb_shell('am start -n com.golike/.MainActivity -f 0x20000000')
    time.sleep(2.5)

    # Quét lại vị trí nút Hoàn thành chống tráo đổi
    gl_root = get_ui()
    if gl_root is not None:
        for n in gl_root.iter():
            if n.attrib.get('class') == 'android.widget.Button' and n.attrib.get('text', '').strip() == 'Hoàn thành':
                ht_x, ht_y = get_center(n.attrib.get('bounds'))
                break

    # 6. Bấm Hoàn thành
    print(f'  [5] Bấm [Hoàn thành] tại toạ độ ({ht_x}, {ht_y})...')
    tap(ht_x, ht_y)
    time.sleep(4)

    # 7. Kiểm tra kết quả
    result_root = get_ui()
    success = False
    for n in result_root.iter() if result_root is not None else []:
        txt = n.attrib.get('text', '')
        if 'Thành công' in txt or 'Báo cáo thành công' in txt:
            success = True
            print(f'  [OK] Báo cáo thành công: {txt}')
            break

    # Đóng modal thành công nếu có
    handle_popups()

    # Cooldown an toàn chống rate limit
    cooldown = 4
    print(f'  Nghỉ {cooldown}s trước job tiếp theo...')
    time.sleep(cooldown)
    return success

def ensure_on_tiktok_jobs():
    """Tự động điều hướng từ bất kỳ màn hình nào về màn hình Kiếm việc TikTok"""
    handle_popups()
    root = get_ui()
    if root is None:
        return
    
    texts = [n.attrib.get('text', '').strip() for n in root.iter()]
    
    # Nếu đã ở màn danh sách job hoặc chi tiết job thì thôi
    if any('Nhận Job ngay' in t for t in texts) or any(t == 'Hoàn thành' for t in texts):
        print('  [Điều hướng] Đang ở sẵn màn hình Danh sách Job TikTok.')
        return

    # Nếu đang ở Trang chủ hoặc tab khác, bấm tab Kiếm xu
    print('  [Điều hướng] Chuyển đến tab Kiếm xu...')
    tap(324, 2011)
    time.sleep(2)
    handle_popups()
    
    # Tìm mục Tiktok trên màn Kiếm xu
    root = get_ui()
    tt_item = None
    for n in root.iter() if root is not None else []:
        txt = n.attrib.get('text', '').strip()
        if txt.lower() == 'tiktok':
            tt_item = n
            break
            
    if tt_item is not None:
        tx, ty = get_center(tt_item.attrib.get('bounds'))
        print(f'  [Điều hướng] Bấm chọn Tiktok tại ({tx}, {ty})...')
        tap(tx, ty)
        time.sleep(2.5)
        handle_popups()
    else:
        # Fallback click vị trí mặc định của Tiktok card
        tap(279, 1350)
        time.sleep(2.5)
        handle_popups()

def run_bot(total_jobs=10):
    print('==================================================')
    print(f'BẮT ĐẦU GOLIKE TIKTOK AUTO BOT ({total_jobs} JOBS)')
    print('==================================================')
    
    # Khóa màn hình xoay dọc
    adb_shell('settings put system accelerometer_rotation 0')
    adb_shell('settings put system user_rotation 0')
    
    # Đảm bảo vào đúng màn hình Kiếm việc TikTok
    ensure_on_tiktok_jobs()
    
    completed = 0
    for i in range(1, total_jobs + 1):
        try:
            ok = execute_single_job(i, total_jobs)
            if ok:
                completed += 1
        except Exception as e:
            print(f'  [Lỗi job #{i}]: {e}')
            time.sleep(3)

    print('\n==================================================')
    print(f'ĐÃ HOÀN THÀNH TẤT CẢ: {completed}/{total_jobs} JOBS THÀNH CÔNG!')
    print('==================================================')
    
    # Quay về Trang chủ xem số dư
    handle_popups()
    tap(108, 2045)
    time.sleep(3)
    screenshot('final_home_balance.png')
    print('Đã chụp ảnh số dư tại final_home_balance.png')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GoLike TikTok Auto Runner')
    parser.add_argument('--jobs', type=int, default=10, help='Số lượng job cần làm')
    args = parser.parse_args()
    run_bot(args.jobs)
