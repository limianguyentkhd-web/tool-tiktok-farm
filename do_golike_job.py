import sys
import time
import subprocess
import re
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
DEVICE = "9889da304447393259"

def adb(cmd):
    full_cmd = f"adb -s {DEVICE} {cmd}"
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return res.stdout.strip()

def lock_portrait():
    adb("shell settings put system accelerometer_rotation 0")
    adb("shell settings put system user_rotation 0")

def dump_ui():
    adb("shell uiautomator dump /sdcard/cur.xml")
    adb("pull /sdcard/cur.xml cur_tmp.xml")
    try:
        tree = ET.parse("cur_tmp.xml")
        return tree
    except Exception as e:
        print(f"dump_ui error: {e}")
        return None

def find_node(tree, text=None, content_desc=None):
    if tree is None:
        return None
    for n in tree.iter():
        t = n.attrib.get('text', '')
        cd = n.attrib.get('content-desc', '')
        if text and text in t:
            return n
        if content_desc and content_desc in cd:
            return n
    return None

def get_bounds_center(node):
    b = node.attrib.get('bounds')
    # format [x1,y1][x2,y2]
    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', b)
    if m:
        x1, y1, x2, y2 = map(int, m.groups())
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def solve_captcha_if_present():
    adb("shell screencap -p /sdcard/cap_check.png")
    adb("pull /sdcard/cap_check.png cap_check.png")
    im = Image.open("cap_check.png")
    arr = np.array(im)
    
    # Check canvas bounds [86, 871, 992, 1480]
    canvas = arr[871:1480, 86:992]
    # Blue square: arr[:, :, 2] > 170 & arr[:, :, 0] < 80
    b_mask = (canvas[:, :, 2] > 170) & (canvas[:, :, 0] < 80)
    if np.sum(b_mask) < 200:
        return False # No captcha
        
    print("Captcha detected! Solving...")
    by, bx = np.where(b_mask)
    gp0 = (int(np.mean(bx)) + 86, int(np.mean(by)) + 871)
    
    # Target circle (green or red)
    g_mask = (canvas[:, :, 1] > 130) & (canvas[:, :, 0] < 80) & (canvas[:, :, 2] < 120)
    r_mask = (canvas[:, :, 0] > 180) & (canvas[:, :, 1] < 120) & (canvas[:, :, 2] < 120)
    if np.sum(g_mask) > 100:
        gy, gx = np.where(g_mask)
        gp2 = (int(np.mean(gx)) + 86, int(np.mean(gy)) + 871)
    elif np.sum(r_mask) > 100:
        ry, rx = np.where(r_mask)
        gp2 = (int(np.mean(rx)) + 86, int(np.mean(ry)) + 871)
    else:
        print("Cannot find target circle in captcha")
        return False
        
    # Dashed circle
    d_mask = (canvas[:, :, 0] > 100) & (canvas[:, :, 0] < 190) & (canvas[:, :, 1] > 120) & (canvas[:, :, 1] < 200) & (canvas[:, :, 2] > 150) & (canvas[:, :, 2] < 230)
    if np.sum(d_mask) > 50:
        dy, dx = np.where(d_mask)
        gp1 = (int(np.mean(dx)) + 86, int(np.mean(dy)) + 871)
    else:
        gp1 = ((gp0[0] + gp2[0]) // 2, (gp0[1] + gp2[1]) // 2 - 80)
        
    print(f"Captcha points: Start={gp0}, Mid={gp1}, Target={gp2}")
    
    # Generate Bezier path
    steps = 35
    t_vals = np.linspace(0, 1, steps)
    pts = []
    for t in t_vals:
        x = (1 - t)**2 * gp0[0] + 2 * (1 - t) * t * gp1[0] + t**2 * gp2[0]
        y = (1 - t)**2 * gp0[1] + 2 * (1 - t) * t * gp1[1] + t**2 * gp2[1]
        pts.append((int(x), int(y)))
        
    script = ["motionevent DOWN %d %d" % pts[0]]
    for pt in pts[1:]:
        script.append("motionevent MOVE %d %d" % pt)
        script.append("sleep 0.015")
    script.append("motionevent UP %d %d" % pts[-1])
    
    with open("drag_solve.sh", "w", newline="\n") as f:
        f.write("\n".join(script) + "\n")
        
    adb("push drag_solve.sh /data/local/tmp/drag.sh")
    adb("shell chmod 777 /data/local/tmp/drag.sh")
    adb("shell sh /data/local/tmp/drag.sh")
    time.sleep(2)
    return True

def run():
    lock_portrait()
    time.sleep(1)
    
    # Bring GoLike to front
    adb("shell monkey -p com.golike 1")
    time.sleep(2)
    
    lock_portrait()
    
    tree = dump_ui()
    # Check if we are on Kiếm Thưởng TikTok
    btn_job = find_node(tree, text="Nhận Job ngay")
    if btn_job is None:
        print("Looking for Nhận Job button...")
        # Check if policy popup is there
        dong_y = find_node(tree, text="Đồng ý")
        if dong_y is not None:
            c = get_bounds_center(dong_y)
            print(f"Found policy popup, tapping Đồng ý at {c}")
            adb(f"shell input tap {c[0]} {c[1]}")
            time.sleep(2)
            tree = dump_ui()
            btn_job = find_node(tree, text="Nhận Job ngay")
            
    if btn_job is not None:
        c = get_bounds_center(btn_job)
        print(f"Tapping 'Nhận Job ngay' at {c}...")
        adb(f"shell input tap {c[0]} {c[1]}")
        time.sleep(3)
        
        # Check captcha
        solve_captcha_if_present()
        time.sleep(3)
        
    # Check if job loaded
    tree = dump_ui()
    job_type = find_node(tree, text="TĂNG LƯỢT THEO DÕI")
    if job_type is None:
        job_type = find_node(tree, text="THÍCH BÀI VIẾT")
        
    if job_type is not None:
        print(f"JOB LOADED: {job_type.attrib.get('text')}")
        # Look for TikTok button
        tt_btn = find_node(tree, text="TikTok")
        if tt_btn is None:
            tt_btn = find_node(tree, content_desc="TikTok")
            
        if tt_btn is not None:
            c = get_bounds_center(tt_btn)
            print(f"Tapping TikTok button at {c}...")
            adb(f"shell input tap {c[0]} {c[1]}")
            print("Waiting for TikTok to open...")
            time.sleep(5)
            
            # Now we are in TikTok
            tt_tree = dump_ui()
            # Find Follow button
            fl_btn = find_node(tt_tree, text="Follow")
            if fl_btn is None:
                fl_btn = find_node(tt_tree, content_desc="Follow")
                
            if fl_btn is not None:
                fc = get_bounds_center(fl_btn)
                print(f"Found Follow button at {fc}, tapping...")
                adb(f"shell input tap {fc[0]} {fc[1]}")
                time.sleep(2)
            else:
                already_fl = find_node(tt_tree, text="Following")
                if already_fl is not None:
                    print("Already following target!")
                else:
                    print("Follow button not found by text, searching for red Follow button...")
                    # Usually at [657, 545][870, 650] or similar
                    adb("shell input tap 760 600")
                    time.sleep(2)
                    
            # Switch back to GoLike
            print("Returning to GoLike...")
            adb("shell monkey -p com.golike 1")
            time.sleep(2)
            lock_portrait()
            
            # Find Hoàn thành button
            gl_tree = dump_ui()
            ht_btn = find_node(gl_tree, text="Hoàn thành")
            if ht_btn is not None:
                hc = get_bounds_center(ht_btn)
                print(f"Tapping 'Hoàn thành' at {hc}...")
                adb(f"shell input tap {hc[0]} {hc[1]}")
                time.sleep(3)
                
                # Check outcome
                res_tree = dump_ui()
                for n in res_tree.iter():
                    t = n.attrib.get('text', '')
                    if "thành công" in t.lower() or "chờ duyệt" in t.lower() or "điểm" in t.lower():
                        print(f"RESULT: {t}")
                print("Job successfully submitted!")
            else:
                print("Could not find Hoàn thành button!")
    else:
        print("No job screen found. Dumping UI elements:")
        for n in tree.iter():
            t = n.attrib.get('text', '')
            if t:
                print(f" - {t}")

if __name__ == "__main__":
    run()
