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
    print('    [Captcha] GoLike visual drag puzzle detected! Solving dynamically...')
    path = screenshot('cap_auto.png')
    arr = np.array(Image.open(path))
    
    # Blue square
    b_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] < 150) & (arr[:, :, 2] > 200)
    by, bx = np.where(b_mask)
    if len(bx) == 0:
        return False
    p0 = (int(np.mean(bx)), int(np.mean(by)))
    
    # Green circle
    g_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] > 150) & (arr[:, :, 2] < 100)
    gy, gx = np.where(g_mask)
    if len(gx) == 0:
        return False
    p2 = (int(np.mean(gx)), int(np.mean(gy)))
    
    # Dashed circle border
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
    
    local_sh = os.path.join(BASE_DIR, 'cap_auto.sh')
    with open(local_sh, 'w', newline='\n') as f:
        f.write('\n'.join(commands) + '\n')
    subprocess.run(['adb', '-s', DEVICE, 'push', local_sh, '/data/local/tmp/cap_auto.sh'], stdout=subprocess.DEVNULL)
    adb_shell('sh /data/local/tmp/cap_auto.sh')
    time.sleep(3.5)
    return True

def handle_popups():
    root = get_ui()
    if root is None:
        return
        
    for n in root.iter():
        txt = n.attrib.get('text', '').strip()
        # Terms popup
        if 'Xác nhận làm việc' in txt:
            print('    [Popup] Accepting app terms...')
            tap(85, 1373)
            time.sleep(0.5)
            tap(913, 1560)
            time.sleep(2)
            root = get_ui()
            break
            
        # Success popup or general OK popup
        if txt == 'OK':
            print('    [Popup] Tapping OK...')
            tap(*get_center(n.attrib.get('bounds')))
            time.sleep(2)
            root = get_ui()
            break

    # Check for visual captcha
    if root is not None:
        for n in root.iter():
            txt = n.attrib.get('text', '')
            if 'Kéo khối vuông' in txt or 'Xác minh nhanh' in txt:
                solve_visual_captcha()
                time.sleep(2)
                break

def execute_job(job_index):
    print(f'\n========================================')
    print(f'>>> STARTING JOB #{job_index}/10')
    print(f'========================================')
    
    # 1. Handle any remaining popups (like the previous success popup)
    handle_popups()
    
    # 2. Check if we need to tap "Nhận Job ngay"
    root = get_ui()
    nhan_btn = None
    for n in root.iter() if root is not None else []:
        if 'Nhận Job ngay' in n.attrib.get('text', ''):
            nhan_btn = n
            break
            
    if nhan_btn is not None:
        nx, ny = get_center(nhan_btn.attrib.get('bounds'))
        print(f'  [1] Tapping "Nhận Job ngay" at ({nx}, {ny})...')
        tap(nx, ny)
        time.sleep(2.5)
        handle_popups()
        time.sleep(2)
        root = get_ui()

    # 3. Locate buttons on Job Details screen
    tt_btn = None
    ht_btn = None
    job_type = 'TĂNG LƯỢT THEO DÕI'
    reward_pts = ''
    
    for n in root.iter() if root is not None else []:
        txt = n.attrib.get('text', '').strip()
        desc = n.attrib.get('content-desc', '').strip()
        cls = n.attrib.get('class', '')
        
        if 'TikTok' in desc or (cls == 'android.widget.TextView' and txt == 'TikTok'):
            if tt_btn is None:
                tt_btn = n
        if cls == 'android.widget.Button' and txt == 'Hoàn thành':
            ht_btn = n
        if 'TĂNG' in txt:
            job_type = txt
        if 'điểm' in txt:
            reward_pts = txt

    if tt_btn is None or ht_btn is None:
        print('  [Warning] Waiting an extra 2s for job screen...')
        time.sleep(2)
        root = get_ui()
        for n in root.iter() if root is not None else []:
            txt = n.attrib.get('text', '').strip()
            desc = n.attrib.get('content-desc', '').strip()
            cls = n.attrib.get('class', '')
            if 'TikTok' in desc or (cls == 'android.widget.TextView' and txt == 'TikTok'):
                if tt_btn is None:
                    tt_btn = n
            if cls == 'android.widget.Button' and txt == 'Hoàn thành':
                ht_btn = n

    tt_x, tt_y = get_center(tt_btn.attrib.get('bounds')) if tt_btn is not None else (540, 891)
    ht_x, ht_y = get_center(ht_btn.attrib.get('bounds')) if ht_btn is not None else (540, 1171)
    
    print(f'  [Job Info] Type: {job_type} | Reward: {reward_pts}')
    print(f'  [Dynamic Bounds] TikTok: ({tt_x}, {tt_y}) | Hoàn thành: ({ht_x}, {ht_y})')

    # 4. Open TikTok
    print('  [2] Opening TikTok...')
    tap(tt_x, tt_y)
    time.sleep(4.5)

    # 5. Interact on TikTok
    print('  [3] Performing action on TikTok...')
    tt_root = get_ui()
    followed = False
    if tt_root is not None:
        for n in tt_root.iter():
            txt = n.attrib.get('text', '').strip()
            if txt == 'Follow':
                fx, fy = get_node_center = get_center(n.attrib.get('bounds'))
                print(f'    Found Follow button at ({fx}, {fy}), tapping!')
                tap(fx, fy)
                followed = True
                break
                
    if not followed:
        print('    Follow button not found, double-tapping video center to Like...')
        tap(540, 1000)
        time.sleep(0.12)
        tap(540, 1000)

    # Anti-spam delay so account is not flagged
    time.sleep(3.5)

    # 6. Switch back to GoLike
    print('  [4] Returning to GoLike...')
    adb_shell('am start -n com.golike/.MainActivity -f 0x20000000')
    time.sleep(2.5)

    # Re-verify dynamic bounds of Hoàn thành button
    gl_root = get_ui()
    if gl_root is not None:
        for n in gl_root.iter():
            if n.attrib.get('class') == 'android.widget.Button' and n.attrib.get('text', '').strip() == 'Hoàn thành':
                ht_x, ht_y = get_center(n.attrib.get('bounds'))
                break

    # 7. Tap Hoàn thành
    print(f'  [5] Tapping "Hoàn thành" at verified ({ht_x}, {ht_y})...')
    tap(ht_x, ht_y)
    time.sleep(4)

    # 8. Check result
    result_root = get_ui()
    success = False
    for n in result_root.iter() if result_root is not None else []:
        txt = n.attrib.get('text', '')
        if 'Thành công' in txt or 'Báo cáo thành công' in txt:
            success = True
            print(f'  >>> SUCCESS: {txt}')
            break

    screenshot(f'job_{job_index}_done.png')
    
    # Anti-ban cooldown between jobs
    cooldown = 4
    print(f'  Waiting {cooldown}s cooldown before next job...')
    time.sleep(cooldown)
    return success

def main():
    print('Starting 10 GoLike Jobs Test Loop for @nguyennminhh256...')
    adb_shell('settings put system accelerometer_rotation 0')
    adb_shell('settings put system user_rotation 0')

    completed = 0
    # First job was already done above, let's complete the remaining jobs up to 10
    for i in range(1, 11):
        try:
            ok = execute_job(i)
            if ok:
                completed += 1
        except Exception as e:
            print(f'Error during job #{i}: {e}')
            time.sleep(3)

    print(f'\n========================================')
    print(f'All 10 jobs completed! Success count: {completed}/10')
    print(f'========================================')

    # Check final Home balance
    print('Checking final balance on Trang chủ...')
    handle_popups()
    tap(108, 2045) # Home tab
    time.sleep(3)
    screenshot('final_balance.png')

if __name__ == '__main__':
    main()
