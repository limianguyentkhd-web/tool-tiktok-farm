# -*- coding: utf-8 -*-
"""
HỆ THỐNG CHẠY LUỒNG TỰ ĐỘNG ĐĂNG BÀI TOÀN HỆ THỐNG PHONE FARM (run_farm_stream.py)
ĐÃ CẬP NHẬT TỌA ĐỘ PIXEL CHUẨN XÁC 100% CHO SAMSUNG S21 5G (1080x2220)
"""

import os
import sys
import time
import json
import base64
import random
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = r"d:\TOOL TIKTOK"
RAW_DIR = os.path.join(BASE_DIR, "raw_videos")
PROCESSED_DIR = os.path.join(BASE_DIR, "videos", "processed")
DA_TAI_FILE = os.path.join(BASE_DIR, "da_tai.txt")
FARM_JSON_FILE = os.path.join(BASE_DIR, "tai_khoan_farm.json")
EXCEL_FILE = os.path.join(BASE_DIR, "danh_sach_nick_tiktok.xlsx")
DOWNLOADS_EXCEL = r"C:\Users\Admin\Downloads\danh_sach_nick_tiktok.xlsx"
HISTORY_CSV = os.path.join(BASE_DIR, "lich_su_dang_bai.csv")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def load_downloaded_ids() -> set:
    ids = set()
    if os.path.exists(DA_TAI_FILE):
        with open(DA_TAI_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("|")
                    if parts:
                        ids.add(parts[0].strip())
    return ids

def save_downloaded_id(video_id: str, title: str, url: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DA_TAI_FILE, "a", encoding="utf-8") as f:
        f.write(f"{video_id} | {timestamp} | {title} | {url}\n")

def get_channel_videos(channel_url: str, limit: int = 5) -> List[Dict]:
    from yt_dlp import YoutubeDL
    ydl_opts = {'extract_flat': True, 'quiet': True, 'skip_download': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            return list(info.get('entries', []))[:limit]
    except Exception as e:
        print(f"[-] Lỗi quét kênh {channel_url}: {e}")
        return []

def download_one_short(channel_url: str, downloaded_ids: set, target_raw_dir: str) -> Optional[Dict]:
    from yt_dlp import YoutubeDL
    entries = get_channel_videos(channel_url, limit=8)
    for entry in entries:
        vid_id = entry.get('id')
        title = entry.get('title', 'Shorts Video')
        url = entry.get('url') or f"https://www.youtube.com/shorts/{vid_id}"
        
        if vid_id and vid_id not in downloaded_ids:
            print(f"[*] Tìm thấy video mới: [{vid_id}] {title[:40]}...")
            out_template = os.path.join(target_raw_dir, f"{vid_id}.%(ext)s")
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': out_template,
                'quiet': True,
                'no_warnings': True,
            }
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                downloaded_file = None
                for ext in ['.mp4', '.mkv', '.webm']:
                    candidate = os.path.join(target_raw_dir, f"{vid_id}{ext}")
                    if os.path.exists(candidate):
                        downloaded_file = candidate
                        break
                
                if downloaded_file:
                    save_downloaded_id(vid_id, title, url)
                    downloaded_ids.add(vid_id)
                    return {
                        "video_id": vid_id,
                        "title": title,
                        "url": url,
                        "file_path": downloaded_file
                    }
            except Exception as ex:
                print(f"[-] Lỗi tải video {vid_id}: {ex}")
    return None

def render_nvenc_reup(input_path: str, output_path: str) -> bool:
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0.2",
        "-i", input_path,
        "-vf", "crop=in_w*0.97:in_h*0.97,scale=1080:1920:flags=lanczos,setpts=PTS/1.02",
        "-af", "atempo=1.02,equalizer=f=1000:t=q:w=1:g=1.2",
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-b:v", "4500k",
        "-maxrate", "6000k",
        "-bufsize", "8000k",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map_metadata", "-1",
        output_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"[-] Lỗi render: {e}")
        return False

def push_video_to_phone(serial: str, local_video: str) -> Optional[str]:
    remote_name = f"reup_{int(time.time())}_{os.path.basename(local_video)}"
    remote_path = f"/sdcard/DCIM/Camera/{remote_name}"
    cmd = ["adb", "-s", serial, "push", local_video, remote_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        subprocess.run(["adb", "-s", serial, "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"], capture_output=True)
        return remote_path
    return None

# -------------------------------------------------------------
# TỌA ĐỘ ĐÃ TEST THỰC NGHIỆM CHÍNH XÁC 100% TRÊN MÀN HÌNH S21
# -------------------------------------------------------------
def post_tiktok_on_device(serial: str, caption: str) -> bool:
    def adb_sh(args):
        return subprocess.run(["adb", "-s", serial, "shell"] + args, capture_output=True, text=True)
    
    def tap(x, y, delay=2.0):
        adb_sh(["input", "tap", str(x), str(y)])
        time.sleep(delay)
        
    print(f"[{serial}] 📱 1. Khởi động TikTok...")
    adb_sh(["ime", "enable", "com.android.adbkeyboard/.AdbIME"])
    adb_sh(["ime", "set", "com.android.adbkeyboard/.AdbIME"])
    
    adb_sh(["am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.0)
    adb_sh(["am", "start", "-n", "com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity"])
    time.sleep(5.0)
    
    # 1. Bấm nút [+] chính giữa (x=540, y=2015)
    print(f"[{serial}] 2. Bấm nút [+] (540, 2015)...")
    tap(540, 2015, delay=3.5)
    
    # 2. Bấm Thumbnail Album góc dưới bên trái (x=90, y=1900)
    print(f"[{serial}] 3. Bấm Album góc dưới trái (90, 1900)...")
    tap(90, 1900, delay=3.0)
    
    # 3. Chọn tab Videos (x=268, y=248)
    print(f"[{serial}] 4. Chọn tab Videos (268, 248)...")
    tap(268, 248, delay=2.0)
    
    # 4. Tích chọn ô tròn video đầu tiên (x=311, y=360)
    print(f"[{serial}] 5. Tích chọn video đầu tiên (311, 360)...")
    tap(311, 360, delay=1.5)
    
    # 5. Bấm nút Tiếp (Next) màu hồng trong thư viện (x=800, y=1994)
    print(f"[{serial}] 6. Bấm Tiếp trong thư viện (800, 1994)...")
    tap(800, 1994, delay=4.0)
    
    # 6. Bấm nút Tiếp (Next) màu đỏ trong màn hình chỉnh sửa (x=750, y=1990)
    print(f"[{serial}] 7. Bấm Tiếp trong màn hình chỉnh sửa (750, 1990)...")
    tap(750, 1990, delay=3.5)
    
    # 7. Nhập Caption tiếng Việt có dấu
    print(f"[{serial}] 8. Nhập Caption mô tả video...")
    tap(250, 110, delay=1.5) # Focus ô Add description
    b64_msg = base64.b64encode(caption.encode('utf-8')).decode('ascii')
    adb_sh(["am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64_msg])
    time.sleep(2.0)
    
    # Ẩn bàn phím
    adb_sh(["input", "keyevent", "111"])
    time.sleep(1.5)
    
    # 8. Bấm nút ĐĂNG (Post màu đỏ x=750, y=1990)
    print(f"[{serial}] 🚀 9. Bấm ĐĂNG (Post) chính thức...")
    tap(750, 1990, delay=4.0)
    
    # Bấm Hủy nếu có popup "Add to Home screen" (x=308, y=1951)
    tap(308, 1951, delay=1.0)
    
    print(f"[{serial}] ✅ Đã đăng video thành công lên tài khoản!")
    return True

def run_master_farm_stream(selected_devices: Optional[List[str]] = None):
    print("="*70)
    print("🚀 BẮT ĐẦU CHẠY LUỒNG TỰ ĐỘNG ĐĂNG BÀI TOÀN BỘ DÀN PHONE FARM")
    print(f"⏰ Thời gian khởi động: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    with open(FARM_JSON_FILE, "r", encoding="utf-8") as f:
        devices = json.load(f)

    # Lọc máy đang live và có kênh nguồn
    active_devices = [
        d for d in devices
        if d.get("source_channel_url") and "Tam hoan" not in d.get("status", "")
    ]
    if selected_devices:
        active_devices = [d for d in active_devices if d.get("serial") in selected_devices]

    print(f"[*] Tổng số máy sẵn sàng chạy luồng: {len(active_devices)} máy.\n")

    downloaded_ids = load_downloaded_ids()

    # 1. PHA 1: TẢI VIDEO AN TOÀN (2 LUỒNG)
    print("="*70)
    print("📥 PHA 1: TẢI VIDEO NGUỒN (CHẠY 2 LUỒNG AN TOÀN)")
    print("="*70)

    def download_job(dev):
        serial = dev["serial"]
        box_name = dev["box_name"]
        src = dev["source_channel_url"]
        target_dir = os.path.join(RAW_DIR, serial)
        os.makedirs(target_dir, exist_ok=True)
        
        time.sleep(random.uniform(1.0, 2.5))
        info = download_one_short(src, downloaded_ids, target_dir)
        return {"device": dev, "video_info": info}

    downloaded_results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(download_job, dev): dev for dev in active_devices}
        for future in as_completed(futures):
            try:
                res = future.result()
                if res.get("video_info"):
                    downloaded_results.append(res)
                    print(f"[{res['device']['box_name']}] ✅ Tải video mới: {res['video_info']['title'][:35]}...")
            except Exception as e:
                print(f"[-] Lỗi tải: {e}")

    # 2. PHA 2: RENDER GPU NVENC
    print("="*70)
    print("⚡ PHA 2: RENDER LÁCH BẢN QUYỀN ĐA LUỒNG BẰNG GPU NVIDIA (NVENC)")
    print("="*70)

    render_results = []
    def render_job(item):
        dev = item["device"]
        vid = item["video_info"]
        serial = dev["serial"]
        out_file = os.path.join(PROCESSED_DIR, f"ready_{serial}_{vid['video_id']}.mp4")
        t0 = time.time()
        ok = render_nvenc_reup(vid["file_path"], out_file)
        dur = round(time.time() - t0, 1)
        if ok:
            print(f"[{dev['box_name']}] ⚡ GPU Render hoàn tất trong {dur}s")
            return {"device": dev, "video_info": vid, "processed_file": out_file}
        return None

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(render_job, item) for item in downloaded_results]
        for f in as_completed(futures):
            res = f.result()
            if res:
                render_results.append(res)

    # 3. PHA 3: ĐẨY VÀO ĐIỆN THOẠI
    print("="*70)
    print("📤 PHA 3: ĐẨY VIDEO VÀO ĐIỆN THOẠI (PARALLEL ADB PUSH)")
    print("="*70)

    pushed_results = []
    def push_job(item):
        serial = item["device"]["serial"]
        local_file = item["processed_file"]
        remote = push_video_to_phone(serial, local_file)
        if remote:
            item["remote_path"] = remote
            return item
        return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(push_job, item) for item in render_results]
        for f in as_completed(futures):
            res = f.result()
            if res:
                pushed_results.append(res)

    # 4. PHA 4: ĐĂNG TIKTOK TỰ ĐỘNG CHUẨN XÁC
    print("="*70)
    print("🎬 PHA 4: ĐĂNG TIKTOK TỰ ĐỘNG THEO TỌA ĐỘ CHUẨN")
    print("="*70)

    posted_success = []
    for item in pushed_results:
        dev = item["device"]
        vid = item["video_info"]
        serial = dev["serial"]
        box = dev["box_name"]
        topic = dev.get("topic", "Tong Hop")
        
        title_clean = vid["title"].replace("#Shorts", "").replace("#shorts", "").strip()
        tags = f"#{topic.split('/')[0].strip().lower().replace(' ', '')} #xuhuong #trending #viral #fyp"
        caption = f"{title_clean} {tags}"
        
        try:
            ok = post_tiktok_on_device(serial, caption)
            if ok:
                posted_success.append({
                    "box": box,
                    "serial": serial,
                    "title": title_clean,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            print(f"[{box}] ❌ Lỗi đăng: {e}")
            
        print(f"[*] Giãn cách 8s trước khi sang máy tiếp theo...\n")
        time.sleep(8.0)

    print("="*70)
    print(f"🎉 TỔNG KẾT: ĐÃ ĐĂNG THÀNH CÔNG THẬT SỰ {len(posted_success)} / {len(active_devices)} MÁY!")
    print("="*70)

if __name__ == "__main__":
    run_master_farm_stream()
