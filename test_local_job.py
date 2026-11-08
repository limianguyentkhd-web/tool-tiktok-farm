import sys
import time
import subprocess
import re
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

DEV = "ce031713dba2c72101"
PORT = "5037"

def adb(*args):
    cmd = ["adb", "-P", PORT, "-s", DEV] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return res.stdout.strip()

def tap(x, y):
    adb("shell", "input", "tap", str(x), str(y))

def dump_ui():
    out = adb("exec-out", "uiautomator", "dump", "/dev/tty")
    if "<?xml" in out:
        out = out[out.find("<?xml"):]
        if "</hierarchy>" in out:
            out = out[:out.find("</hierarchy>") + 12]
        try:
            return ET.fromstring(out)
        except Exception as e:
            pass
    return None

def find_nodes(root, text_pattern=None, desc_pattern=None, class_pattern=None):
    res = []
    if root is None:
        return res
    for node in root.iter('node'):
        txt = node.attrib.get('text', '')
        desc = node.attrib.get('content-desc', '')
        cls = node.attrib.get('class', '')
        bounds = node.attrib.get('bounds', '')
        
        if text_pattern and not re.search(text_pattern, txt, re.IGNORECASE):
            continue
        if desc_pattern and not re.search(desc_pattern, desc, re.IGNORECASE):
            continue
        if class_pattern and not re.search(class_pattern, cls, re.IGNORECASE):
            continue
            
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            res.append({
                'text': txt,
                'desc': desc,
                'class': cls,
                'bounds': (x1, y1, x2, y2),
                'center': ((x1+x2)//2, (y1+y2)//2)
            })
    return res

def solve_captcha_if_needed():
    root = dump_ui()
    captcha_node = find_nodes(root, text_pattern=r'Xác minh nhanh|Kéo khối vuông')
    if not captcha_node:
        return True
    print("[Captcha] Quick verification detected! Solving via computer vision...")
    # Take screenshot
    adb("shell", "screencap", "-p", "/sdcard/cap_local.png")
    subprocess.run(["adb", "-P", PORT, "-s", DEV, "pull", "/sdcard/cap_local.png", "d:/TOOL TIKTOK/cap_local.png"], capture_output=True)
    
    try:
        img = Image.open("d:/TOOL TIKTOK/cap_local.png")
        arr = np.array(img)
        h, w, _ = arr.shape
        
        # Blue square: R < 70, G < 150, B > 200
        blue_mask = (arr[:, :, 0] < 70) & (arr[:, :, 1] < 150) & (arr[:, :, 2] > 200)
        bys, bxs = np.where(blue_mask)
        p0 = (int(np.mean(bxs)), int(np.mean(bys)))
        
        # Green circle: R < 70, G > 140, B < 100
        green_mask = (arr[:, :, 0] < 70) & (arr[:, :, 1] > 140) & (arr[:, :, 2] < 100)
        gys, gxs = np.where(green_mask)
        p2 = (int(np.mean(gxs)), int(np.mean(gys)))
        
        # Dashed circle center
        grey_mask = (np.abs(arr[:, :, 0].astype(int) - arr[:, :, 1].astype(int)) < 15) & \
                    (np.abs(arr[:, :, 1].astype(int) - arr[:, :, 2].astype(int)) < 15) & \
                    (arr[:, :, 0] > 140) & (arr[:, :, 0] < 190) & \
                    (np.arange(h)[:, None] > 1050) & (np.arange(h)[:, None] < 1400) & \
                    (np.arange(w)[None, :] > 350) & (np.arange(w)[None, :] < 650)
        dys, dxs = np.where(grey_mask)
        p1 = (int(np.mean(dxs)), int(np.mean(dys)))
        
        print(f"[Captcha] Points: Start={p0}, Via={p1}, Target={p2}")
        
        # Generate bezier curve
        points = []
        steps = 25
        for i in range(steps + 1):
            t = i / steps
            x = int((1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0])
            y = int((1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1])
            points.append((x, y))
            
        cmds = [f'input motionevent DOWN {points[0][0]} {points[0][1]}', 'sleep 0.1']
        for pt in points[1:-1]:
            cmds.append(f'input motionevent MOVE {pt[0]} {pt[1]}')
            cmds.append('sleep 0.02')
        cmds.append(f'input motionevent MOVE {points[-1][0]} {points[-1][1]}')
        cmds.append('sleep 0.1')
        cmds.append(f'input motionevent UP {points[-1][0]} {points[-1][1]}')
        
        adb("shell", "; ".join(cmds))
        time.sleep(2)
        print("[Captcha] Solved!")
        return True
    except Exception as e:
        print("[Captcha] Error solving:", e)
        return False

def do_one_job():
    print("--- [1] Tap 'Nhận Job ngay' ---")
    root = dump_ui()
    btn = find_nodes(root, text_pattern=r'Nhận Job ngay')
    if btn:
        tap(btn[0]['center'][0], btn[0]['center'][1])
        time.sleep(2.5)
        
    # Check modal confirmation
    root = dump_ui()
    agree = find_nodes(root, text_pattern=r'^Đồng ý$')
    if agree:
        print("Dismissing disclaimer popup...")
        tap(85, 1374)
        time.sleep(0.3)
        tap(agree[0]['center'][0], agree[0]['center'][1])
        time.sleep(2)
        
    solve_captcha_if_needed()
    
    # Check job screen
    root = dump_ui()
    job_type_nodes = find_nodes(root, text_pattern=r'TĂNG LƯỢT|TĂNG LIKE|TĂNG BÌNH LUẬN|Job Id')
    job_desc = "Unknown"
    for n in job_type_nodes:
        print("  Job info:", n['text'])
        if 'TĂNG' in n['text']:
            job_desc = n['text']
            
    tt_btn = find_nodes(root, desc_pattern=r'^TikTok$')
    if not tt_btn:
        tt_btn = find_nodes(root, text_pattern=r'^TikTok$')
        
    if not tt_btn:
        print("Could not find TikTok button! Current nodes:")
        for n in find_nodes(root):
            if n['text']:
                print("   txt:", n['text'])
        return False
        
    print(f"--- [2] Tap 'TikTok' button -> Switching to TikTok app for '{job_desc}' ---")
    tap(tt_btn[0]['center'][0], tt_btn[0]['center'][1])
    time.sleep(4.0)
    
    # We are now in TikTok!
    if 'THEO DÕI' in job_desc.upper():
        print("Executing FOLLOW action in TikTok...")
        tt_root = dump_ui()
        follow = find_nodes(tt_root, text_pattern=r'^Follow$')
        if follow:
            print("Tapping Follow at", follow[0]['center'])
            tap(follow[0]['center'][0], follow[0]['center'][1])
        else:
            # Check if button with text Follow
            f_btns = find_nodes(tt_root, desc_pattern=r'Follow')
            if f_btns:
                print("Tapping Follow desc at", f_btns[0]['center'])
                tap(f_btns[0]['center'][0], f_btns[0]['center'][1])
            else:
                print("Fallback tap Follow coordinate (254, 572)")
                tap(254, 572)
    else:
        # LIKE job: double tap center screen or like button
        print("Executing LIKE action in TikTok...")
        tap(540, 1100)
        time.sleep(0.1)
        tap(540, 1100)
        
    time.sleep(2.5) # Anti-spam delay
    
    print("--- [3] Returning to GoLike ---")
    adb("shell", "input", "keyevent", "4") # Back key
    time.sleep(1.5)
    
    # Check if back on GoLike, if not, bring to front
    root = dump_ui()
    complete_btn = find_nodes(root, text_pattern=r'Hoàn thành')
    if not complete_btn:
        adb("shell", "am", "start", "-n", "com.golike/.MainActivity")
        time.sleep(1.5)
        root = dump_ui()
        complete_btn = find_nodes(root, text_pattern=r'Hoàn thành')
        
    if complete_btn:
        print("Tapping 'Hoàn thành' at", complete_btn[0]['center'])
        tap(complete_btn[0]['center'][0], complete_btn[0]['center'][1])
        time.sleep(3.5)
    else:
        print("Could not find 'Hoàn thành' button!")
        return False
        
    # Check result
    result_root = dump_ui()
    for n in find_nodes(result_root):
        txt = n['text']
        if any(w in txt.lower() for w in ['thành công', 'lỗi', 'điểm', 'nhận được', 'hoàn thành', 'chúc mừng', 'hết thời gian']):
            print("  [Result]:", txt)
            
    return True

if __name__ == '__main__':
    do_one_job()
