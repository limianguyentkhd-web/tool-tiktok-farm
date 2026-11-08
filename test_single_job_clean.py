import subprocess
import time
import os
import sys
import re
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

DEVICE = 'ce031713dba2c72101'
BASE_DIR = r'C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd'

def adb_shell(cmd):
    res = subprocess.run(['adb', '-s', DEVICE, 'shell', cmd], capture_output=True, text=True, errors='ignore')
    return res.stdout

def tap(x, y):
    adb_shell(f'input tap {x} {y}')

def screenshot(name='screen.png'):
    path = os.path.join(BASE_DIR, name)
    res = subprocess.run(['adb', '-s', DEVICE, 'exec-out', 'screencap', '-p'], capture_output=True)
    with open(path, 'wb') as f:
        f.write(res.stdout)
    return path

def get_ui():
    adb_shell('uiautomator dump /data/local/tmp/ui.xml')
    xml_str = adb_shell('cat /data/local/tmp/ui.xml')
    try:
        return ET.fromstring(xml_str)
    except:
        return None

def find_nodes(root, text_sub='', desc_sub='', cls_sub=''):
    if root is None:
        return []
    res = []
    for n in root.iter():
        txt = n.attrib.get('text', '')
        desc = n.attrib.get('content-desc', '')
        cls = n.attrib.get('class', '')
        if text_sub and text_sub.lower() not in txt.lower():
            continue
        if desc_sub and desc_sub.lower() not in desc.lower():
            continue
        if cls_sub and cls_sub.lower() not in cls.lower():
            continue
        res.append(n)
    return res

def get_center(bounds_str):
    m = re.findall(r'\d+', bounds_str)
    if len(m) == 4:
        return (int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2
    return 540, 1000

def solve_visual_captcha():
    print('  [Captcha] Solving GoLike visual drag captcha...')
    path = screenshot('cap_temp.png')
    arr = np.array(Image.open(path))
    
    # 1. Blue square
    b_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] < 150) & (arr[:, :, 2] > 200)
    by, bx = np.where(b_mask)
    if len(bx) == 0:
        print('  [Captcha] Could not locate blue square!')
        return False
    p0 = (int(np.mean(bx)), int(np.mean(by)))
    
    # 2. Green circle
    g_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] > 150) & (arr[:, :, 2] < 100)
    gy, gx = np.where(g_mask)
    if len(gx) == 0:
        print('  [Captcha] Could not locate green circle!')
        return False
    p2 = (int(np.mean(gx)), int(np.mean(gy)))
    
    # 3. Dashed circle border
    d_mask = (arr[:, :, 0] > 125) & (arr[:, :, 0] < 185) & (arr[:, :, 1] > 145) & (arr[:, :, 1] < 205) & (arr[:, :, 2] > 170) & (arr[:, :, 2] < 225)
    d_mask[:850, :] = False
    d_mask[1450:, :] = False
    d_mask[:, :300] = False
    d_mask[:, 850:] = False
    dy, dx = np.where(d_mask)
    if len(dx) > 0:
        p1 = (int(np.mean(dx)), int(np.mean(dy)))
    else:
        p1 = ((p0[0] + p2[0]) // 2, (p0[1] + p2[1]) // 2)
        
    print(f'  [Captcha] p0={p0} -> p1={p1} -> p2={p2}')
    commands = [f'input motionevent DOWN {p0[0]} {p0[1]}', 'sleep 0.1']
    for i in range(1, 31):
        t = i / 30.0
        x = int((1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0])
        y = int((1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1])
        commands.append(f'input motionevent MOVE {x} {y}')
        commands.append('sleep 0.02')
    commands.append('sleep 0.15')
    commands.append(f'input motionevent UP {p2[0]} {p2[1]}')
    
    local_sh = os.path.join(BASE_DIR, 'cap_curve.sh')
    with open(local_sh, 'w', newline='\n') as f:
        f.write('\n'.join(commands) + '\n')
    subprocess.run(['adb', '-s', DEVICE, 'push', local_sh, '/data/local/tmp/cap_curve.sh'], stdout=subprocess.DEVNULL)
    adb_shell('sh /data/local/tmp/cap_curve.sh')
    time.sleep(3.5)
    return True

def handle_popups():
    root = get_ui()
    if root is None:
        return
    # Check Terms
    terms = find_nodes(root, text_sub='Xác nhận làm việc bằng App')
    if len(terms) > 0:
        print('  [Popup] Accepting terms...')
        tap(85, 1373)
        time.sleep(0.5)
        tap(913, 1560)
        time.sleep(2)
        root = get_ui()
        
    # Check OK
    oks = find_nodes(root, text_sub='OK')
    if len(oks) > 0 and len(find_nodes(root, text_sub='xác minh')) > 0:
        print('  [Popup] Tapping OK on verification alert...')
        tap(539, 1354)
        time.sleep(2)
        root = get_ui()
        
    # Check Captcha
    if len(find_nodes(root, text_sub='Kéo khối vuông')) > 0 or len(find_nodes(root, text_sub='Xác minh nhanh')) > 0:
        solve_visual_captcha()

def run_job():
    print('=== STEP 1: Verify current screen ===')
    root = get_ui()
    
    # If not on Kiếm Thưởng, navigate there
    if len(find_nodes(root, text_sub='Nhận Job ngay')) == 0 and len(find_nodes(root, text_sub='Chi tiết')) == 0:
        print('Navigating to Kiếm Thưởng...')
        # Check if on Home
        if len(find_nodes(root, text_sub='Trang chủ')) > 0:
            tap(324, 2045)
            time.sleep(2.5)
            root = get_ui()
        if len(find_nodes(root, text_sub='Chọn kênh kiếm xu')) > 0:
            tap(279, 1350)
            time.sleep(2.5)
            root = get_ui()

    # If on Kiếm Thưởng, tap Nhận Job ngay
    nhan_btns = find_nodes(root, text_sub='Nhận Job ngay')
    if len(nhan_btns) > 0:
        nx, ny = get_center(nhan_btns[0].attrib.get('bounds'))
        print(f'Tapping "Nhận Job ngay" at ({nx}, {ny})...')
        tap(nx, ny)
        time.sleep(3)
        handle_popups()
        time.sleep(2)
        root = get_ui()

    handle_popups()
    time.sleep(1)
    root = get_ui()

    print('=== STEP 2: Job details ===')
    job_type_nodes = find_nodes(root, text_sub='TĂNG')
    job_title = job_type_nodes[0].attrib.get('text', '') if len(job_type_nodes) > 0 else 'TĂNG TƯƠNG TÁC'
    pts_nodes = find_nodes(root, text_sub='điểm')
    pts_text = pts_nodes[0].attrib.get('text', '') if len(pts_nodes) > 0 else ''
    id_nodes = find_nodes(root, text_sub='Job Id:')
    job_id = id_nodes[0].attrib.get('text', '') if len(id_nodes) > 0 else ''
    print(f'  Job: {job_title} | Reward: {pts_text} | {job_id}')

    print('=== STEP 3: Open TikTok ===')
    tt_nodes = find_nodes(root, text_sub='TikTok') or find_nodes(root, desc_sub='TikTok')
    tt_x, tt_y = (540, 767)
    if len(tt_nodes) > 0:
        tt_x, tt_y = get_center(tt_nodes[0].attrib.get('bounds'))
    print(f'Tapping TikTok at ({tt_x}, {tt_y})...')
    tap(tt_x, tt_y)
    time.sleep(4.5)

    print('=== STEP 4: Perform interaction in TikTok ===')
    tt_root = get_ui()
    follow_nodes = [n for n in find_nodes(tt_root, text_sub='Follow') if n.attrib.get('text', '').strip() == 'Follow']
    if len(follow_nodes) > 0:
        fx, fy = get_center(follow_nodes[0].attrib.get('bounds'))
        print(f'  Tapping Follow at ({fx}, {fy})...')
        tap(fx, fy)
    else:
        print('  Double-tapping center to like...')
        tap(540, 1000)
        time.sleep(0.12)
        tap(540, 1000)

    time.sleep(3) # Anti-spam delay

    print('=== STEP 5: Return to GoLike ===')
    adb_shell('am start -n com.golike/.MainActivity -f 0x20000000')
    time.sleep(2.5)

    print('=== STEP 6: Tap Hoàn thành ===')
    gl_root = get_ui()
    ht_nodes = find_nodes(gl_root, text_sub='Hoàn thành')
    ht_x, ht_y = (540, 908)
    if len(ht_nodes) > 0:
        ht_x, ht_y = get_center(ht_nodes[0].attrib.get('bounds'))
    print(f'Tapping Hoàn thành at exact ({ht_x}, {ht_y})...')
    tap(ht_x, ht_y)
    time.sleep(4)

    sc = screenshot('single_job_verified.png')
    print(f'=== STEP 7: Completed! Screenshot: {sc} ===')
    
    # Inspect final messages
    final_root = get_ui()
    for n in final_root.iter() if final_root is not None else []:
        txt = n.attrib.get('text', '')
        desc = n.attrib.get('content-desc', '')
        if any(k in txt.lower() or k in desc.lower() for k in ['thành công', 'thất bại', 'hoàn thành', 'lỗi', 'job', 'điểm']):
            print(f'  UI notification: {txt} {desc}')

if __name__ == '__main__':
    run_job()
