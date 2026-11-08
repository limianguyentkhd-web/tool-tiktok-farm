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

def get_ui_dump():
    adb_shell('uiautomator dump /data/local/tmp/ui.xml')
    xml_str = adb_shell('cat /data/local/tmp/ui.xml')
    try:
        return ET.fromstring(xml_str)
    except:
        return None

def find_nodes(root, text_pattern=None, desc_pattern=None, class_pattern=None):
    if root is None:
        return []
    results = []
    for node in root.iter():
        txt = node.attrib.get('text', '')
        desc = node.attrib.get('content-desc', '')
        cls = node.attrib.get('class', '')
        if text_pattern and not re.search(text_pattern, txt, re.IGNORECASE):
            continue
        if desc_pattern and not re.search(desc_pattern, desc, re.IGNORECASE):
            continue
        if class_pattern and not re.search(class_pattern, cls, re.IGNORECASE):
            continue
        results.append(node)
    return results

def get_center(bounds_str):
    m = re.findall(r'\d+', bounds_str)
    if len(m) == 4:
        return (int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2
    return 540, 1000

def solve_visual_captcha():
    print('  [Captcha] Solving GoLike visual drag captcha...')
    path = screenshot('current_captcha.png')
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
        
    print(f'  [Captcha] Trajectory: p0(Blue)={p0} -> p1(Dashed)={p1} -> p2(Green)={p2}')
    
    commands = [f'input motionevent DOWN {p0[0]} {p0[1]}', 'sleep 0.1']
    for i in range(1, 31):
        t = i / 30.0
        x = int((1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0])
        y = int((1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1])
        commands.append(f'input motionevent MOVE {x} {y}')
        commands.append('sleep 0.02')
    commands.append('sleep 0.15')
    commands.append(f'input motionevent UP {p2[0]} {p2[1]}')
    
    local_sh = os.path.join(BASE_DIR, 'solve_curve.sh')
    with open(local_sh, 'w', newline='\n') as f:
        f.write('\n'.join(commands) + '\n')
    subprocess.run(['adb', '-s', DEVICE, 'push', local_sh, '/data/local/tmp/solve_curve.sh'], stdout=subprocess.DEVNULL)
    adb_shell('sh /data/local/tmp/solve_curve.sh')
    time.sleep(3.5)
    return True

def ensure_portrait():
    adb_shell('settings put system accelerometer_rotation 0')
    adb_shell('settings put system user_rotation 0')

def navigate_to_tiktok_jobs():
    ensure_portrait()
    adb_shell('am start -n com.golike/.MainActivity -f 0x20000000')
    time.sleep(2)
    
    root = get_ui_dump()
    # Check if already on Chi tiết or Kiếm Thưởng
    if find_nodes(root, text_pattern=r'Chi tiết|Nhận Job ngay'):
        return True
        
    # If on Home, tap Kiếm xu tab
    nodes_kx = find_nodes(root, text_pattern=r'^Kiếm xu$')
    if nodes_kx:
        tap(*get_center(nodes_kx[0].attrib.get('bounds')))
        time.sleep(2)
        root = get_ui_dump()
        
    # If on Chọn kênh kiếm xu, tap Tiktok
    nodes_tt = find_nodes(root, text_pattern=r'^Tiktok$')
    if nodes_tt:
        tap(*get_center(nodes_tt[0].attrib.get('bounds')))
        time.sleep(2)
        root = get_ui_dump()
        
    return True

def check_and_handle_popups():
    root = get_ui_dump()
    if root is None:
        return
        
    # 1. Terms
    if find_nodes(root, text_pattern=r'Xác nhận làm việc'):
        print('  [Popup] Accepting terms...')
        tap(85, 1373) # checkbox
        time.sleep(0.5)
        tap(913, 1560) # Đồng ý
        time.sleep(2)
        root = get_ui_dump()
        
    # 2. OK popup
    if find_nodes(root, text_pattern=r'^OK$') and find_nodes(root, text_pattern=r'xác minh'):
        print('  [Popup] Tapping OK on verification notification...')
        tap(539, 1354)
        time.sleep(2)
        root = get_ui_dump()
        
    # 3. Visual captcha
    if find_nodes(root, text_pattern=r'Kéo khối vuông|Xác minh nhanh'):
        solve_visual_captcha()

def perform_single_job():
    navigate_to_tiktok_jobs()
    time.sleep(1)
    
    root = get_ui_dump()
    check_and_handle_popups()
    root = get_ui_dump()
    
    # If on "Kiếm Thưởng" screen with "Nhận Job ngay"
    nhan_btn = find_nodes(root, text_pattern=r'Nhận Job ngay')
    if nhan_btn:
        print('>>> Tapping "Nhận Job ngay"...')
        tap(*get_center(nhan_btn[0].attrib.get('bounds')))
        time.sleep(3)
        check_and_handle_popups()
        time.sleep(2)
        root = get_ui_dump()
        
    # Verify we are on "Chi tiết" job screen
    title_node = find_nodes(root, text_pattern=r'Chi tiết')
    if not title_node and not find_nodes(root, text_pattern=r'TikTok'):
        print('  [Notice] Job not ready yet, checking screen...')
        time.sleep(2)
        root = get_ui_dump()
        
    # Read job information
    job_type_nodes = find_nodes(root, text_pattern=r'TĂNG')
    job_title = job_type_nodes[0].attrib.get('text', '') if job_type_nodes else 'TĂNG TƯƠNG TÁC'
    
    pts_nodes = find_nodes(root, text_pattern=r'điểm')
    pts_text = pts_nodes[0].attrib.get('text', '') if pts_nodes else ''
    
    id_nodes = find_nodes(root, text_pattern=r'Job Id:')
    job_id = id_nodes[0].attrib.get('text', '') if id_nodes else ''
    
    print(f'>>> ACTIVE JOB: {job_title} | Reward: {pts_text} | {job_id}')
    
    # Find TikTok button
    tt_btn = find_nodes(root, text_pattern=r'^TikTok$', class_pattern=r'TextView')
    if not tt_btn:
        tt_btn = find_nodes(root, desc_pattern=r'^TikTok$')
    if not tt_btn:
        print('  ERROR: TikTok button not found on job screen!')
        screenshot('error_no_tt_btn.png')
        return False
        
    tt_x, tt_y = get_center(tt_btn[0].attrib.get('bounds'))
    print(f'>>> Tapping TikTok button at ({tt_x}, {tt_y})...')
    tap(tt_x, tt_y)
    
    # Wait for TikTok to load
    time.sleep(4.5)
    
    # Interacting inside TikTok
    print('>>> In TikTok: Checking interaction...')
    tt_root = get_ui_dump()
    follow_btns = find_nodes(tt_root, text_pattern=r'^Follow$')
    if follow_btns:
        fx, fy = get_center(follow_btns[0].attrib.get('bounds'))
        print(f'  Found Follow button at ({fx}, {fy}), tapping...')
        tap(fx, fy)
    else:
        print('  Follow button not found, double-tapping video center to Like...')
        tap(540, 1000)
        time.sleep(0.12)
        tap(540, 1000)
        
    time.sleep(3) # Safe delay for TikTok action to register
    
    # Switch back to GoLike
    print('>>> Switching back to GoLike...')
    adb_shell('am start -n com.golike/.MainActivity -f 0x20000000')
    time.sleep(2.5)
    
    # On GoLike: Find and tap "Hoàn thành"
    gl_root = get_ui_dump()
    ht_btns = find_nodes(gl_root, text_pattern=r'^Hoàn thành$')
    if not ht_btns:
        print('  [Warning] "Hoàn thành" button not immediately found, re-checking...')
        time.sleep(1.5)
        gl_root = get_ui_dump()
        ht_btns = find_nodes(gl_root, text_pattern=r'^Hoàn thành$')
        
    if ht_btns:
        hx, hy = get_center(ht_btns[0].attrib.get('bounds'))
        print(f'>>> Tapping "Hoàn thành" button at exact bounds ({hx}, {hy})...')
        tap(hx, hy)
        time.sleep(4)
    else:
        print('  ERROR: "Hoàn thành" button not found!')
        screenshot('error_no_ht_btn.png')
        return False
        
    # Check outcome
    after_root = get_ui_dump()
    screenshot('after_job_submit.png')
    
    # Check for success messages or alerts
    success_nodes = find_nodes(after_root, text_pattern=r'thành công|hoàn thành|cộng điểm')
    if success_nodes:
        txt = success_nodes[0].attrib.get('text', 'Job submitted successfully!')
        print(f'>>> RESULT: {txt}')
    else:
        print('>>> RESULT: Job submitted (next job or screen loaded).')
        
    return True

if __name__ == '__main__':
    perform_single_job()
