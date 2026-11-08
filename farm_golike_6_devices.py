import subprocess
import time
import sys
import os
import random
import re
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

# 6 FARM DEVICES (STRICTLY EXCLUDING MAY MAU ce031713dba2c72101)
DEVICES = [
    {"name": "May 1", "serial": "9889da304447393259", "port": "5037"},
    {"name": "May 2", "serial": "988a17344c564b5657", "port": "5037"},
    {"name": "May 3", "serial": "ce01182188dbdcee0c", "port": "5037"},
    {"name": "May 4", "serial": "ce011821c38b263b05", "port": "5037"},
    {"name": "May 5", "serial": "ce011821c45dc4060c", "port": "5038"},
    {"name": "May 6", "serial": "ce031713ed1e10540d", "port": "5037"},
]

TEMP_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

def adb(dev, cmd, timeout=15):
    full_cmd = f"adb -P {dev['port']} -s {dev['serial']} {cmd}"
    try:
        res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, errors='ignore', timeout=timeout)
        return res.stdout.strip()
    except Exception:
        return ""

def lock_portrait(dev):
    adb(dev, "shell settings put system accelerometer_rotation 0")
    adb(dev, "shell settings put system user_rotation 0")

def dump_ui(dev):
    dev_name = dev['name'].replace(" ", "_")
    xml_remote = f"/sdcard/dump_{dev_name}.xml"
    xml_local = os.path.join(TEMP_DIR, f"ui_{dev_name}.xml")
    adb(dev, f"shell uiautomator dump {xml_remote}", timeout=10)
    adb(dev, f"pull {xml_remote} \"{xml_local}\"", timeout=10)
    try:
        return ET.parse(xml_local)
    except Exception:
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

def get_center(node):
    b = node.attrib.get('bounds')
    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', b)
    if m:
        x1, y1, x2, y2 = map(int, m.groups())
        return (x1 + x2) // 2, (y1 + y2) // 2
    return 540, 1000

def solve_captcha(dev):
    dev_name = dev['name'].replace(" ", "_")
    img_remote = f"/sdcard/cap_{dev_name}.png"
    img_local = os.path.join(TEMP_DIR, f"cap_{dev_name}.png")
    adb(dev, f"shell screencap -p {img_remote}", timeout=8)
    adb(dev, f"pull {img_remote} \"{img_local}\"", timeout=8)
    if not os.path.exists(img_local):
        return False
    try:
        im = Image.open(img_local)
        arr = np.array(im)
        if arr.shape[0] < 1500 or arr.shape[1] < 1000:
            return False
            
        canvas = arr[871:1480, 86:992]
        b_mask = (canvas[:, :, 2] > 170) & (canvas[:, :, 0] < 80)
        if np.sum(b_mask) < 200:
            return False
            
        print(f"[{dev['name']}] Phát hiện Captcha GoLike! Đang giải bằng đường cong Bézier...")
        by, bx = np.where(b_mask)
        gp0 = (int(np.mean(bx)) + 86, int(np.mean(by)) + 871)
        
        g_mask = (canvas[:, :, 1] > 130) & (canvas[:, :, 0] < 80) & (canvas[:, :, 2] < 120)
        r_mask = (canvas[:, :, 0] > 180) & (canvas[:, :, 1] < 120) & (canvas[:, :, 2] < 120)
        if np.sum(g_mask) > 100:
            gy, gx = np.where(g_mask)
            gp2 = (int(np.mean(gx)) + 86, int(np.mean(gy)) + 871)
        elif np.sum(r_mask) > 100:
            ry, rx = np.where(r_mask)
            gp2 = (int(np.mean(rx)) + 86, int(np.mean(ry)) + 871)
        else:
            return False
            
        d_mask = (canvas[:, :, 0] > 100) & (canvas[:, :, 0] < 190) & (canvas[:, :, 1] > 120) & (canvas[:, :, 1] < 200) & (canvas[:, :, 2] > 150) & (canvas[:, :, 2] < 230)
        if np.sum(d_mask) > 50:
            dy, dx = np.where(d_mask)
            gp1 = (int(np.mean(dx)) + 86, int(np.mean(dy)) + 871)
        else:
            gp1 = ((gp0[0] + gp2[0]) // 2, (gp0[1] + gp2[1]) // 2 - 80)
            
        steps = 35
        t_vals = np.linspace(0, 1, steps)
        script = ["motionevent DOWN %d %d" % gp0]
        for t in t_vals[1:]:
            x = (1 - t)**2 * gp0[0] + 2 * (1 - t) * t * gp1[0] + t**2 * gp2[0]
            y = (1 - t)**2 * gp0[1] + 2 * (1 - t) * t * gp1[1] + t**2 * gp2[1]
            script.append(f"motionevent MOVE {int(x)} {int(y)}")
            script.append("sleep 0.015")
        script.append("motionevent UP %d %d" % gp2)
        
        sh_local = os.path.join(TEMP_DIR, f"drag_{dev_name}.sh")
        with open(sh_local, "w", newline="\n") as f:
            f.write("\n".join(script) + "\n")
            
        sh_remote = f"/data/local/tmp/drag_{dev_name}.sh"
        adb(dev, f"push \"{sh_local}\" {sh_remote}")
        adb(dev, f"shell chmod 777 {sh_remote}")
        adb(dev, f"shell sh {sh_remote}")
        time.sleep(2.5)
        print(f"[{dev['name']}] Giải Captcha thành công!")
        return True
    except Exception as e:
        print(f"[{dev['name']}] Lỗi giải Captcha: {e}")
        return False

def do_feed_warmup(dev, duration_minutes=15):
    """Chế độ ĐI NUÔI: Mở TikTok lướt For You ngẫu nhiên để phục hồi trust score."""
    print(f"[{dev['name']}] >>> BẮT ĐẦU CHẾ ĐỘ ĐI NUÔI TIKTOK TRONG {duration_minutes} PHÚT <<<")
    lock_portrait(dev)
    adb(dev, "shell am force-stop com.zhiliaoapp.musically")
    time.sleep(1)
    adb(dev, "shell monkey -p com.zhiliaoapp.musically 1")
    time.sleep(5)
    
    end_time = time.time() + duration_minutes * 60
    video_count = 0
    while time.time() < end_time:
        video_count += 1
        
        # Tự động phát hiện và đóng các popup/chính sách (Got it, Agree, Not now,...)
        try:
            tree = dump_ui(dev)
            if tree is not None:
                for text_btn in ["Got it", "Agree", "Đồng ý", "Not now", "Lúc khác", "Hủy", "Cancel"]:
                    btn = find_node(tree, text=text_btn)
                    if btn is not None:
                        bc = get_center(btn)
                        print(f"[{dev['name']}] Tự động đóng popup '{text_btn}' tại {bc}...")
                        adb(dev, f"shell input tap {bc[0]} {bc[1]}")
                        time.sleep(1.5)
                        break
                        
                # Nếu lỡ kẹt webview chính sách hoặc Live player, bấm Back
                if find_node(tree, text="Virtual Items") is not None or find_node(tree, text="Policy") is not None:
                    print(f"[{dev['name']}] Phát hiện kẹt webview chính sách -> Bấm Back...")
                    adb(dev, "shell input keyevent KEYCODE_BACK")
                    time.sleep(1)
        except Exception:
            pass

        # Random xem từ 8 đến 22 giây
        watch_sec = random.randint(8, 22)
        print(f"[{dev['name']}] Nuôi TikTok - Video #{video_count}: Xem {watch_sec}s...")
        time.sleep(watch_sec)
        
        # 35% xác suất thả tim
        if random.random() < 0.35:
            cx, cy = random.randint(500, 580), random.randint(900, 1100)
            adb(dev, f"shell input tap {cx} {cy}")
            time.sleep(0.12)
            adb(dev, f"shell input tap {cx} {cy}")
            print(f"[{dev['name']}] Đã thả tim video #{video_count}")
            
        # Vuốt sang video tiếp theo
        adb(dev, "shell input swipe 540 1600 540 400 350")
        time.sleep(1.5)
        
    print(f"[{dev['name']}] Hoàn thành phiên đi nuôi ({video_count} videos). Quay lại làm job!")

def execute_single_job(dev):
    lock_portrait(dev)
    adb(dev, "shell monkey -p com.golike 1")
    time.sleep(2)
    lock_portrait(dev)
    
    tree = dump_ui(dev)
    
    # Check if not on TikTok job page
    if find_node(tree, text="Nhận Job ngay") is None and find_node(tree, text="TĂNG LƯỢT THEO DÕI") is None:
        adb(dev, "shell input tap 324 2011")
        time.sleep(1.5)
        adb(dev, "shell input tap 279 1350")
        time.sleep(2)
        tree = dump_ui(dev)
        
    # Check policy popup
    dong_y = find_node(tree, text="Đồng ý")
    if dong_y is not None:
        c = get_center(dong_y)
        adb(dev, f"shell input tap {c[0]} {c[1]}")
        time.sleep(2)
        tree = dump_ui(dev)
        
    btn_job = find_node(tree, text="Nhận Job ngay")
    if btn_job is not None:
        c = get_center(btn_job)
        print(f"[{dev['name']}] Bấm 'Nhận Job ngay'...")
        adb(dev, f"shell input tap {c[0]} {c[1]}")
        time.sleep(3)
        solve_captcha(dev)
        time.sleep(2.5)
        tree = dump_ui(dev)
        
    # Detect job
    job_type = find_node(tree, text="TĂNG LƯỢT THEO DÕI")
    if job_type is None:
        job_type = find_node(tree, text="THÍCH BÀI VIẾT")
        
    if job_type is not None:
        j_title = job_type.attrib.get('text')
        print(f"[{dev['name']}] ĐÃ NHẬN JOB: {j_title}!")
        
        tt_btn = find_node(tree, text="TikTok")
        if tt_btn is None:
            tt_btn = find_node(tree, content_desc="TikTok")
            
        tap_y = 891
        if tt_btn is not None:
            tap_y = get_center(tt_btn)[1]
            
        adb(dev, f"shell input tap 540 {tap_y}")
        print(f"[{dev['name']}] Đang mở TikTok...")
        time.sleep(4.5)
        
        # Follow on TikTok
        tt_tree = dump_ui(dev)
        fl_btn = find_node(tt_tree, text="Follow")
        if fl_btn is None:
            fl_btn = find_node(tt_tree, content_desc="Follow")
            
        if fl_btn is not None:
            fc = get_center(fl_btn)
            adb(dev, f"shell input tap {fc[0]} {fc[1]}")
            print(f"[{dev['name']}] Đã nhấn Follow tại {fc}!")
        else:
            adb(dev, "shell input tap 760 600")
            print(f"[{dev['name']}] Đã tương tác Follow!")
            
        time.sleep(2)
        
        # Return to GoLike
        adb(dev, "shell monkey -p com.golike 1")
        time.sleep(2)
        lock_portrait(dev)
        
        gl_tree = dump_ui(dev)
        ht_btn = find_node(gl_tree, text="Hoàn thành")
        ht_y = 1031
        if ht_btn is not None:
            ht_y = get_center(ht_btn)[1]
            
        print(f"[{dev['name']}] Bấm nút 'Hoàn thành'...")
        adb(dev, f"shell input tap 540 {ht_y}")
        time.sleep(3)
        print(f"[{dev['name']}] >> JOB HOÀN THÀNH VÀ GỬI DUYỆT THÀNH CÔNG! <<")
        return "SUCCESS"
    else:
        texts = [n.attrib.get('text', '') for n in tree.iter() if n.attrib.get('text')]
        err_msg = ""
        for t in texts:
            if any(k in t.lower() for k in ["hết job", "chưa có công việc", "giới hạn", "thử lại sau", "tạm khóa", "block"]):
                err_msg = t
                break
                
        if err_msg:
            print(f"[{dev['name']}] [CẢNH BÁO / BLOCK]: {err_msg}")
            return "BLOCKED"
        else:
            print(f"[{dev['name']}] Chưa lấy được job mới (đang thử lại hoặc giãn cách)...")
            return "NO_JOB"

def worker_loop(dev):
    print(f"[{dev['name']}] Worker khởi chạy!")
    fail_count = 0
    while True:
        try:
            status = execute_single_job(dev)
            if status == "SUCCESS":
                fail_count = 0
                wait = random.randint(8, 15)
                print(f"[{dev['name']}] Nghỉ giãn cách {wait}s trước job tiếp theo...")
                time.sleep(wait)
            elif status == "BLOCKED":
                print(f"[{dev['name']}] Phát hiện chặn / hết job -> BẬT CHẾ ĐỘ ĐI NUÔI 20 PHÚT!")
                do_feed_warmup(dev, duration_minutes=20)
                fail_count = 0
            else: # NO_JOB
                fail_count += 1
                if fail_count >= 3:
                    print(f"[{dev['name']}] Không có job sau 3 lần thử -> CHUYỂN ĐI NUÔI 15 PHÚT!")
                    do_feed_warmup(dev, duration_minutes=15)
                    fail_count = 0
                else:
                    time.sleep(10)
        except Exception as e:
            print(f"[{dev['name']}] Ngoại lệ vòng lặp: {e}")
            time.sleep(10)

def main():
    print("==================================================================")
    print("🚀 KHỞI ĐỘNG HỆ THỐNG FULL JOB GOLIKE TRỌN VẸN 6 MÁY FARM ĐỘC LẬP")
    print(f"[*] Số máy tham gia: {len(DEVICES)} máy (May 1 -> May 6)")
    print("[*] Cơ chế tự động: Nhận Job -> Giải Captcha Bézier -> Follow -> Nhận tiền")
    print("[*] Cơ chế an toàn: Phát hiện Block / Hết Job -> Tự động chuyển ĐI NUÔI lướt feed")
    print("==================================================================")
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(worker_loop, dev) for dev in DEVICES]
        for f in futures:
            f.result()

if __name__ == "__main__":
    main()
