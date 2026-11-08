import subprocess
import time
import os
import sys
from PIL import Image
import numpy as np

# Force unbuffered UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

DEVICE = 'ce031713dba2c72101'
DIR = r'C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd'

def adb(cmd):
    full_cmd = f'adb -s {DEVICE} {cmd}'
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, errors='ignore')
    return res.stdout.strip()

def screencap(name='current.png'):
    local_path = os.path.join(DIR, name)
    adb('shell screencap -p /sdcard/sc.png')
    adb(f'pull /sdcard/sc.png "{local_path}"')
    return local_path

def solve_captcha(img_path):
    im = Image.open(img_path)
    arr = np.array(im)
    
    # 1. Blue square
    blue_mask = (arr[:, :, 2] > 200) & (arr[:, :, 0] < 80) & (arr[:, :, 1] < 150)
    by, bx = np.where(blue_mask)
    if len(bx) < 50:
        return False
    p_start = (int(bx.mean()), int(by.mean()))
    
    # 2. Green circle
    green_mask = (arr[:, :, 1] > 140) & (arr[:, :, 0] < 80) & (arr[:, :, 2] < 120)
    gy, gx = np.where(green_mask)
    if len(gx) < 50:
        return False
    p_end = (int(gx.mean()), int(gy.mean()))
    
    # 3. Dashed circle
    bg = arr[900, 500, :3].astype(int)
    diff = np.sqrt(np.sum((arr[800:1500, 300:750, :3].astype(int) - bg)**2, axis=2))
    ys, xs = np.where(diff > 25)
    if len(xs) < 50:
        return False
    p_mid = (300 + int((xs.min() + xs.max())/2), 800 + int((ys.min() + ys.max())/2))
    
    print(f'[CAPTCHA] Detected! Start: {p_start}, Mid: {p_mid}, End: {p_end}', flush=True)
    
    points = []
    for t in np.linspace(0, 1, 15):
        points.append((int(p_start[0] + t * (p_mid[0] - p_start[0])), int(p_start[1] + t * (p_mid[1] - p_start[1]))))
    for t in np.linspace(0, 1, 10)[1:]:
        points.append((int(p_mid[0] + t * (p_end[0] - p_mid[0])), int(p_mid[1] + t * (p_end[1] - p_mid[1]))))
        
    lines = ['#!/system/bin/sh']
    lines.append(f'input motionevent DOWN {points[0][0]} {points[0][1]}')
    lines.append('sleep 0.1')
    for pt in points[1:]:
        lines.append(f'input motionevent MOVE {pt[0]} {pt[1]}')
        lines.append('sleep 0.03')
    lines.append('sleep 0.1')
    lines.append(f'input motionevent UP {points[-1][0]} {points[-1][1]}')
    
    sh_path = os.path.join(DIR, 'drag.sh')
    with open(sh_path, 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    
    adb(f'push "{sh_path}" /data/local/tmp/drag.sh')
    adb('shell "chmod +x /data/local/tmp/drag.sh ; sh /data/local/tmp/drag.sh"')
    time.sleep(2.5)
    return True

def is_modal_open(arr):
    return arr[50, 500, 0] < 100

def is_job_details(arr):
    # Only the Job Details screen has the gold coin icon of Hoàn thành (len > 300)
    sub_gold = (arr[800:1250, 380:480, 0] > 220) & (arr[800:1250, 380:480, 1] > 160) & (arr[800:1250, 380:480, 2] < 120)
    return np.sum(sub_gold) > 300

def get_job_buttons(arr):
    # Báo lỗi: red triangle icon in x: 420..480, y: 800..1250
    sub_red = (arr[800:1250, 420:480, 0] > 200) & (arr[800:1250, 420:480, 1] < 80) & (arr[800:1250, 420:480, 2] < 80)
    ry, rx = np.where(sub_red)
    bao_loi_y = 800 + int(ry.mean()) if len(ry) > 5 else 1040

    # Hoàn thành: gold coin icon in x: 380..480, y: 800..1250
    sub_gold = (arr[800:1250, 380:480, 0] > 220) & (arr[800:1250, 380:480, 1] > 160) & (arr[800:1250, 380:480, 2] < 120)
    gy, gx = np.where(sub_gold)
    hoan_thanh_y = 800 + int(gy.mean()) if len(gy) > 5 else 900

    # TikTok button is always above both
    tiktok_y = min(bao_loi_y, hoan_thanh_y) - 135

    return {
        'tiktok': (540, tiktok_y),
        'bao_loi': (540, bao_loi_y),
        'hoan_thanh': (540, hoan_thanh_y)
    }

def is_follow_job(arr):
    icon = arr[250:315, 60:125, :3]
    top_pink = (icon[:20, :, 0] > 180) & (icon[:20, :, 1] < 100)
    bottom_cyan = (icon[-20:, :, 2] > 140) & (icon[-20:, :, 0] < 100)
    return (np.sum(top_pink) > 10) and (np.sum(bottom_cyan) > 10)

def run_farm_cycle():
    img_path = screencap('loop.png')
    im = Image.open(img_path)
    arr = np.array(im)
    
    # 1. Popup Modal
    if is_modal_open(arr):
        checkbox_area = arr[1350:1400, 60:200, :3]
        if (checkbox_area[:, :, 0] < 100).any() and (checkbox_area[:, :, 2] > 180).any():
            print('[POPUP] Found "Xác nhận làm việc bằng App". Accepting...', flush=True)
            adb('shell input tap 150 1370')
            time.sleep(0.5)
            adb('shell input tap 860 1560')
            time.sleep(2.5)
            return 'popup'
            
        if solve_captcha(img_path):
            print('[CAPTCHA] Solved!', flush=True)
            time.sleep(2.5)
            return 'captcha'
            
    # 2. Check if we are on Job Details screen
    if is_job_details(arr):
        buttons = get_job_buttons(arr)
        follow = is_follow_job(arr)
        
        crop = im.crop((50, 240, 800, 320))
        crop.save(os.path.join(DIR, 'current_job_title.png'))
        
        if follow:
            print(f'[JOB] Follow Job detected ({crop.size})! Skipping back to main (tap 30 110)...', flush=True)
            adb('shell input tap 30 110')
            time.sleep(2.0)
            return 'skipped_follow'
        else:
            print(f'[JOB] ★★★ LIKE / TIM JOB FOUND! ★★★', flush=True)
            im.save(os.path.join(DIR, f'like_job_{int(time.time())}.png'))
            print(f'[JOB] Opening TikTok at {buttons["tiktok"]}...', flush=True)
            adb(f'shell input tap {buttons["tiktok"][0]} {buttons["tiktok"][1]}')
            time.sleep(5.0) # wait for video to load fully
            
            print('[TIKTOK] Liking video (double tap center)...', flush=True)
            adb('shell input tap 540 1100')
            time.sleep(0.12)
            adb('shell input tap 540 1100')
            time.sleep(4.0) # real human watch delay
            
            print('[TIKTOK] Returning to GoLike...', flush=True)
            adb('shell am start -n com.golike/.MainActivity')
            time.sleep(2.5)
            
            post_img = screencap('post_like.png')
            post_arr = np.array(Image.open(post_img))
            post_buttons = get_job_buttons(post_arr)
            
            print(f'[GOLIKE] Confirming completion at {post_buttons["hoan_thanh"]}...', flush=True)
            adb(f'shell input tap {post_buttons["hoan_thanh"][0]} {post_buttons["hoan_thanh"][1]}')
            time.sleep(4.0)
            print('[GOLIKE] Successfully completed LIKE Job!', flush=True)
            return 'completed_like'

    # 3. Main screen with 'Nhận Job ngay' button at (518, 1132)
    # Card is cyan on left (x=200), white button in center (x=518), pink on right (x=800)
    is_main = (arr[1132, 518, 0] > 240) and (arr[1132, 800, 0] > 200) and (arr[1132, 200, 2] > 180)
    if is_main:
        print('[MAIN] Tapping "Nhận Job ngay"...', flush=True)
        adb('shell input tap 518 1132')
        time.sleep(3.0)
        return 'nhan_job'

    print('[INFO] Screen not recognized or transition state. Sleeping 2s...', flush=True)
    time.sleep(2.0)
    return 'idle'

if __name__ == '__main__':
    max_cycles = 15
    print(f'Starting GoLike Like Job Farmer for nick _ngminh (@nguyennminhh256) [max {max_cycles} cycles]...\n', flush=True)
    like_count = 0
    skip_count = 0
    for i in range(max_cycles):
        print(f'>>> Cycle {i+1}/{max_cycles}:', flush=True)
        action = run_farm_cycle()
        if action == 'completed_like':
            like_count += 1
            print(f'[STATS] Likes so far: {like_count}, Skips: {skip_count}', flush=True)
            time.sleep(8.0)
        elif action == 'skipped_follow':
            skip_count += 1
            print(f'[STATS] Likes so far: {like_count}, Skips: {skip_count}', flush=True)
            time.sleep(1.5)
        else:
            time.sleep(1.0)
            
    print(f'\nFinished session! Total Likes completed: {like_count}, Follows skipped: {skip_count}', flush=True)
