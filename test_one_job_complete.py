# -*- coding: utf-8 -*-
"""
Tự động giải Captcha và thực hiện 1 Job GoLike trên Máy 1
"""
import sys
import os
import time
import subprocess
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
DEVICE = "9889da304447393259"
PORT = "5037"

def adb_cmd(args, timeout=15):
    cmd = [ADB, "-P", PORT, "-s", DEVICE] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")

def tap(x, y):
    adb_cmd(["shell", "input", "tap", str(x), str(y)])

def screencap(local_path):
    remote = "/sdcard/sc.png"
    adb_cmd(["shell", "screencap", "-p", remote])
    adb_cmd(["pull", remote, local_path])
    return local_path

def dump_ui():
    xml_path = "/sdcard/ui_dump.xml"
    adb_cmd(["shell", "uiautomator", "dump", xml_path])
    res = adb_cmd(["shell", "cat", xml_path])
    if "<hierarchy" in res.stdout:
        return ET.fromstring(res.stdout)
    return None

def solve_captcha_if_present():
    print("[1] Kiểm tra xem có Captcha kéo thả không...")
    img_path = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\cap_current.png"
    screencap(img_path)
    im = Image.open(img_path)
    arr = np.array(im)[:, :, :3]

    # Crop captcha canvas (y=870..1480, x=86..992)
    c_arr = arr[871:1480, 86:992]

    # Blue square
    b_mask = (c_arr[:, :, 2] > 170) & (c_arr[:, :, 0] < 80)
    by, bx = np.where(b_mask)
    if len(bx) < 50:
        print("[-] Không phát hiện Captcha khối vuông.")
        return False

    p0 = (int(np.mean(bx)), int(np.mean(by)))

    # Target circle (Green or Red)
    g_mask = (c_arr[:, :, 1] > 130) & (c_arr[:, :, 0] < 80) & (c_arr[:, :, 2] < 120)
    gy, gx = np.where(g_mask)
    if len(gx) > 20:
        p2 = (int(np.mean(gx)), int(np.mean(gy)))
        target_name = "Green"
    else:
        r_mask = (c_arr[:, :, 0] > 180) & (c_arr[:, :, 1] < 120) & (c_arr[:, :, 2] < 120)
        ry, rx = np.where(r_mask)
        p2 = (int(np.mean(rx)), int(np.mean(ry)))
        target_name = "Red"

    # Dashed circle
    d_mask = (c_arr[:, :, 0] > 100) & (c_arr[:, :, 0] < 190) & (c_arr[:, :, 1] > 120) & (c_arr[:, :, 1] < 200) & (c_arr[:, :, 2] > 150) & (c_arr[:, :, 2] < 230)
    dy, dx = np.where(d_mask)
    valid_dx, valid_dy = [], []
    for x, y in zip(dx, dy):
        d0 = (x - p0[0])**2 + (y - p0[1])**2
        d2 = (x - p2[0])**2 + (y - p2[1])**2
        if d0 > 2500 and d2 > 2500:
            valid_dx.append(x)
            valid_dy.append(y)

    if len(valid_dx) > 10:
        p1 = (int(np.mean(valid_dx)), int(np.mean(valid_dy)))
    else:
        p1 = ((p0[0] + p2[0]) // 2, (p0[1] + p2[1]) // 2)

    gp0 = (86 + p0[0], 871 + p0[1])
    gp1 = (86 + p1[0], 871 + p1[1])
    gp2 = (86 + p2[0], 871 + p2[1])
    print(f"[+] Tìm thấy tọa độ Captcha:")
    print(f"    - Khối vuông xanh (Bắt đầu): {gp0}")
    print(f"    - Vòng nét đứt (Đi xuyên qua): {gp1}")
    print(f"    - Vòng đích {target_name}: {gp2}")

    # Generate Bezier curve drag
    commands = [f"input motionevent DOWN {gp0[0]} {gp0[1]}", "sleep 0.1"]
    steps = 35
    for i in range(1, steps + 1):
        t = i / float(steps)
        x = int((1-t)**2 * gp0[0] + 2*(1-t)*t * gp1[0] + t**2 * gp2[0])
        y = int((1-t)**2 * gp0[1] + 2*(1-t)*t * gp1[1] + t**2 * gp2[1])
        commands.append(f"input motionevent MOVE {x} {y}")
        commands.append("sleep 0.02")
    commands.append("sleep 0.2")
    commands.append(f"input motionevent UP {gp2[0]} {gp2[1]}")

    local_sh = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\drag_solve.sh"
    with open(local_sh, "w", newline="\n") as f:
        f.write("\n".join(commands) + "\n")

    adb_cmd(["push", local_sh, "/data/local/tmp/drag_solve.sh"])
    print("[+] Đang thực hiện vuốt giải Captcha tự động...")
    adb_cmd(["shell", "sh", "/data/local/tmp/drag_solve.sh"])
    time.sleep(3.5)
    print("[✓] Đã giải xong Captcha!")
    return True

def run():
    print("=" * 60)
    print("🚀 BẮT ĐẦU KIỂM TRA LÀM THỬ 1 JOB TRÊN GOLIKE (MÁY 1)")
    print("=" * 60)

    # 1. Giải captcha nếu đang hiện
    solve_captcha_if_present()

    # 2. Kiểm tra xem đã có Job trên màn hình chưa, nếu chưa bấm "Nhận Job ngay"
    time.sleep(1.0)
    root = dump_ui()
    if root is not None:
        has_job = any("TIKTOK" in (n.attrib.get("text", "") or "") and "Kiếm xu" not in (n.attrib.get("text", "") or "") for n in root.iter("node"))
        for n in root.iter("node"):
            t = n.attrib.get("text", "")
            if "Nhận Job ngay" in t:
                print("[2] Bấm nút 'Nhận Job ngay'...")
                tap(507, 1166)
                time.sleep(3.5)
                # Giải captcha nếu hiện sau khi bấm nhận
                solve_captcha_if_present()
                time.sleep(2.0)
                break

    # 3. Chụp màn hình và đọc thông tin Job
    screencap(r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\job_current_state.png")
    root = dump_ui()
    job_type = "UNKNOWN"
    tiktok_btn_center = None
    complete_btn_center = None

    if root is not None:
        for n in root.iter("node"):
            t = n.attrib.get("text", "")
            d = n.attrib.get("content-desc", "")
            b = n.attrib.get("bounds", "")
            
            if "THEO DÕI" in t or "FOLLOW" in t or "tiktok-follow" in d:
                job_type = "FOLLOW"
            elif "THẢ TIM" in t or "LIKE" in t or "tiktok-like" in d:
                job_type = "LIKE"
            elif "Hết Job" in t or "Chưa có công việc" in t:
                print("[!] Thông báo từ GoLike: Hết Job tạm thời hoặc chưa có nhiệm vụ mới.")
                return

            if "TikTok" in t and "Kênh TikTok" not in t and "HƯỚNG DẪN" not in t:
                import re
                m = re.findall(r'\[(\d+),(\d+)\]', b)
                if len(m) == 2:
                    tiktok_btn_center = ((int(m[0][0]) + int(m[1][0])) // 2, (int(m[0][1]) + int(m[1][1])) // 2)

            if "Hoàn thành" in t or "Xác nhận" in t or "Hoan thanh" in t:
                import re
                m = re.findall(r'\[(\d+),(\d+)\]', b)
                if len(m) == 2:
                    complete_btn_center = ((int(m[0][0]) + int(m[1][0])) // 2, (int(m[0][1]) + int(m[1][1])) // 2)

    print(f"[3] Loại nhiệm vụ: {job_type}")
    print(f"    - Nút mở TikTok: {tiktok_btn_center}")
    print(f"    - Nút Hoàn thành: {complete_btn_center}")

    if tiktok_btn_center:
        print(f"[4] Bấm nút mở TikTok tại {tiktok_btn_center}...")
        tap(tiktok_btn_center[0], tiktok_btn_center[1])
        time.sleep(5.0)

        # Thực hiện tương tác trên TikTok
        if job_type == "FOLLOW":
            print("[5] Đang nhấn nút FOLLOW trên TikTok...")
            tap(254, 572)
            time.sleep(2.0)
        else:
            print("[5] Đang thả TIM trên TikTok...")
            tap(540, 1050)
            time.sleep(0.1)
            tap(540, 1050)
            time.sleep(2.0)

        # Quay lại GoLike
        print("[6] Quay lại GoLike...")
        adb_cmd(["shell", "input", "keyevent", "4"])
        time.sleep(1.5)

        # Bấm Hoàn thành
        if complete_btn_center:
            print(f"[7] Bấm 'Hoàn thành' tại {complete_btn_center}...")
            tap(complete_btn_center[0], complete_btn_center[1])
            time.sleep(4.0)

            # Chụp kết quả
            res_png = screencap(r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\job_result.png")
            print("[✓] Đã gửi xác nhận hoàn thành Job lên GoLike! Đã lưu ảnh kết quả.")
    else:
        print("[-] Chưa load được chi tiết Job hoặc cần kiểm tra lại giao diện GoLike.")

if __name__ == "__main__":
    run()
