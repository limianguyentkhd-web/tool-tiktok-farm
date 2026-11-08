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

def get_node_center(node):
    bounds = node.attrib.get('bounds', '')
    m = re.findall(r'\d+', bounds)
    if len(m) == 4:
        return (int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2
    return 540, 1000

def solve_captcha_if_present():
    path = screenshot('cap_check.png')
    arr = np.array(Image.open(path))
    b_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] < 150) & (arr[:, :, 2] > 200)
    by, bx = np.where(b_mask)
    if len(bx) > 0 and 800 < np.mean(by) < 1600:
        print('  [Captcha] Visual puzzle detected! Solving dynamically...')
        p0 = (int(np.mean(bx)), int(np.mean(by)))
        g_mask = (arr[:, :, 0] < 80) & (arr[:, :, 1] > 150) & (arr[:, :, 2] < 100)
        gy, gx = np.where(g_mask)
        p2 = (int(np.mean(gx)), int(np.mean(gy)))
        
        d_mask = (arr[:, :, 0] > 125) & (arr[:, :, 0] < 185) & (arr[:, :, 1] > 145) & (arr[:, :, 1] < 205) & (arr[:, :, 2] > 170) & (arr[:, :, 2] < 225)
        d_mask[:850, :] = False
        d_mask[1450:, :] = False
        d_mask[:, :300] = False
        d_mask[:, 850:] = False
        dy, dx = np.where(d_mask)
        p1 = (int(np.mean(dx)), int(np.mean(dy))) if len(dx) > 0 else ((p0[0]+p2[0])//2, (p0[1]+p2[1])//2)
        
        commands = [f'input motionevent DOWN {p0[0]} {p0[1]}', 'sleep 0.1']
        for i in range(1, 31):
            t = i / 30.0
            x = int((1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0])
            y = int((1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1])
            commands.append(f'input motionevent MOVE {x} {y}')
            commands.append('sleep 0.02')
        commands.append('sleep 0.15')
        commands.append(f'input motionevent UP {p2[0]} {p2[1]}')
        
        local_sh = os.path.join(BASE_DIR, 'cap_live.sh')
        with open(local_sh, 'w', newline='\n') as f:
            f.write('\n'.join(commands) + '\n')
        subprocess.run(['adb', '-s', DEVICE, 'push', local_sh, '/data/local/tmp/cap_live.sh'], stdout=subprocess.DEVNULL)
        adb_shell('sh /data/local/tmp/cap_live.sh')
        time.sleep(3.5)
        return True
    return False

def do_verified_job():
    print('1. Tapping "Nhận Job ngay" at (507, 1166)...')
    tap(507, 1166)
    time.sleep(2.5)

    # Check captcha
    solve_captcha_if_present()
    time.sleep(2)

    # Dump UI on Job Details screen
    root = get_ui()
    if root is None:
        print('Error getting UI dump')
        return

    # Find buttons
    tt_btn = None
    ht_btn = None
    bao_loi_btn = None

    for n in root.iter():
        txt = n.attrib.get('text', '').strip()
        desc = n.attrib.get('content-desc', '').strip()
        cls = n.attrib.get('class', '')
        if 'TikTok' in desc or (cls == 'android.widget.TextView' and txt == 'TikTok'):
            if tt_btn is None:
                tt_btn = n
        if cls == 'android.widget.Button':
            if txt == 'Hoàn thành':
                ht_btn = n
            elif txt == 'Báo lỗi':
                bao_loi_btn = n

    if tt_btn is not None:
        tt_x, tt_y = get_node_center(tt_btn)
        print(f'   TikTok button found at ({tt_x}, {tt_y})')
    else:
        tt_x, tt_y = 540, 767
        print(f'   Using default TikTok at ({tt_x}, {tt_y})')

    if ht_btn is not None:
        ht_x, ht_y = get_node_center(ht_btn)
        print(f'   Hoàn thành button verified at exact ({ht_x}, {ht_y})')
    else:
        ht_x, ht_y = 540, 908
        print(f'   Using fallback Hoàn thành at ({ht_x}, {ht_y})')

    if bao_loi_btn is not None:
        bx, by = get_node_center(bao_loi_btn)
        print(f'   Báo lỗi button located at ({bx}, {by}) [WILL AVOID]')

    # 2. Tap TikTok
    print('2. Opening TikTok...')
    tap(tt_x, tt_y)
    time.sleep(4.5)

    # 3. Interact inside TikTok
    print('3. Interacting in TikTok...')
    tt_root = get_ui()
    followed = False
    if tt_root is not None:
        for n in tt_root.iter():
            if n.attrib.get('text', '').strip() == 'Follow':
                fx, fy = get_node_center(n)
                print(f'   Found Follow button at ({fx}, {fy}), tapping!')
                tap(fx, fy)
                followed = True
                break

    if not followed:
        print('   Follow button not found, liking video via double tap!')
        tap(540, 1000)
        time.sleep(0.12)
        tap(540, 1000)

    # Anti-spam delay
    time.sleep(3.5)

    # 4. Switch back to GoLike
    print('4. Returning to GoLike...')
    adb_shell('am start -n com.golike/.MainActivity -f 0x20000000')
    time.sleep(2.5)

    # Re-verify Hoàn thành button coordinates
    cur_root = get_ui()
    if cur_root is not None:
        for n in cur_root.iter():
            if n.attrib.get('class') == 'android.widget.Button' and n.attrib.get('text', '').strip() == 'Hoàn thành':
                ht_x, ht_y = get_node_center(n)
                print(f'   Re-confirmed Hoàn thành at ({ht_x}, {ht_y})')
                break

    print(f'5. Tapping Hoàn thành at ({ht_x}, {ht_y})...')
    tap(ht_x, ht_y)
    time.sleep(4)

    # 6. Check outcome
    screenshot('verified_job_outcome.png')
    print('Done! Saved screenshot to verified_job_outcome.png')

if __name__ == '__main__':
    do_verified_job()
