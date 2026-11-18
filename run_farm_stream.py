# -*- coding: utf-8 -*-
"""
HỆ THỐNG CHẠY LUỒNG TỰ ĐỘNG ĐĂNG BÀI TOÀN HỆ THỐNG PHONE FARM (run_farm_stream.py)
---------------------------------------------------------------------------------
Quy trình tối ưu hóa:
1. PHA 1 (TẢI AN TOÀN): Quét kênh nguồn YouTube, tải tối đa 2 luồng (có delay) để tránh YouTube quét bot/rate limit.
2. PHA 2 (RENDER GPU SIÊU TỐC): Đa luồng render lách bản quyền bằng GPU NVIDIA NVENC (cắt đầu đuôi, crop, đổi pitch, xóa metadata).
3. PHA 3 (ĐẨY VÀO MÁY): Đa luồng ADB Push đồng loạt 14 video vào 14 điện thoại + quét MediaStore.
4. PHA 4 (ĐĂNG TRÊN TIKTOK): Tự mở TikTok, chọn video, gõ caption tiếng Việt + hashtag, bấm Đăng (giãn cách nhẹ 10s giữa các máy để bảo vệ Proxy và tự nhiên).
5. PHA 5 (BÁO CÁO): Cập nhật file Excel và lịch sử đăng bài.
"""

import os
import sys
import time
import json
import base64
import random
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Cấu hình đường dẫn
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

# -------------------------------------------------------------
# 1. HÀM QUẢN LÝ SỔ ĐEN CHỐNG TẢI TRÙNG
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# 2. PHA 1: TẢI VIDEO YOUTUBE SHORTS (2 LUỒNG AN TOÀN)
# -------------------------------------------------------------
def get_channel_videos(channel_url: str, limit: int = 5) -> List[Dict]:
    from yt_dlp import YoutubeDL
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'skip_download': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            entries = info.get('entries', [])
            return list(entries)[:limit]
    except Exception as e:
        print(f"[-] Lỗi quét kênh {channel_url}: {e}")
        return []

def download_one_short(channel_url: str, downloaded_ids: set, target_raw_dir: str) -> Optional[Dict]:
    """Quét và tải 1 video mới nhất chưa từng tải từ kênh nguồn."""
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
                
                # Tìm file đã tải
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

# -------------------------------------------------------------
# 3. PHA 2: RENDER GPU NVENC LÁCH BẢN QUYỀN ĐA LUỒNG
# -------------------------------------------------------------
def render_nvenc_reup(input_path: str, output_path: str) -> bool:
    """
    Sử dụng NVIDIA GPU (h264_nvenc) render siêu tốc lách bản quyền:
    - Cắt 0.2s đầu, crop nhẹ 2.5%, chỉnh speed 1.02x
    - Tinh chỉnh eq âm thanh
    - Xóa toàn bộ EXIF/Metadata
    """
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
        if res.returncode == 0 and os.path.exists(output_path):
            return True
        else:
            # Fallback CPU nếu lỗi NVENC
            cmd_cpu = [
                "ffmpeg", "-y", "-ss", "0.2", "-i", input_path,
                "-vf", "crop=in_w*0.97:in_h*0.97,scale=1080:1920",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k", "-map_metadata", "-1",
                output_path
            ]
            r2 = subprocess.run(cmd_cpu, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return r2.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"[-] Lỗi render: {e}")
        return False

# -------------------------------------------------------------
# 4. PHA 3: ĐẨY VIDEO VÀO ĐIỆN THOẠI (ADB PUSH PARALLEL)
# -------------------------------------------------------------
def push_video_to_phone(serial: str, local_video: str) -> Optional[str]:
    remote_name = f"reup_{int(time.time())}_{os.path.basename(local_video)}"
    remote_path = f"/sdcard/DCIM/Camera/{remote_name}"
    cmd = ["adb", "-s", serial, "push", local_video, remote_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        # Scan file vào MediaStore
        subprocess.run(["adb", "-s", serial, "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"], capture_output=True)
        return remote_path
    return None

# -------------------------------------------------------------
# 5. PHA 4: ĐĂNG TIKTOK TỰ ĐỘNG BẰNG ADB
# -------------------------------------------------------------
def post_tiktok_on_device(serial: str, caption: str) -> bool:
    def adb_sh(args):
        return subprocess.run(["adb", "-s", serial, "shell"] + args, capture_output=True, text=True)
    
    def tap(x, y, delay=1.5):
        adb_sh(["input", "tap", str(x), str(y)])
        time.sleep(delay)
        
    print(f"[{serial}] 📱 Đang mở TikTok và chuẩn bị đăng bài...")
    # Bật AdbIME
    adb_sh(["ime", "enable", "com.android.adbkeyboard/.AdbIME"])
    adb_sh(["ime", "set", "com.android.adbkeyboard/.AdbIME"])
    
    # Khởi động TikTok sạch
    adb_sh(["am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.0)
    adb_sh(["am", "start", "-n", "com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity"])
    time.sleep(5.0)
    
    # Bấm nút [+]
    print(f"[{serial}] 1. Bấm nút [+] (540, 2150)...")
    tap(540, 2150, delay=3.5)
    
    # Bấm Album (Tải lên) ở góc dưới phải
    print(f"[{serial}] 2. Bấm Tải lên / Album...")
    tap(930, 2000, delay=3.0)
    
    # Chọn tab Videos
    tap(340, 240, delay=1.5)
    
    # Chọn video đầu tiên
    print(f"[{serial}] 3. Chọn video mới nhất...")
    tap(180, 400, delay=2.5)
    
    # Bấm Tiếp (Next)
    print(f"[{serial}] 4. Bấm Tiếp...")
    tap(880, 2150, delay=3.5)
    
    # Nhập caption tiếng Việt qua AdbIME Base64
    print(f"[{serial}] 5. Nhập Caption: {caption[:30]}...")
    tap(350, 450, delay=1.5) # Focus ô mô tả
    b64_msg = base64.b64encode(caption.encode('utf-8')).decode('ascii')
    adb_sh(["am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64_msg])
    time.sleep(2.0)
    
    # Ẩn bàn phím
    adb_sh(["input", "keyevent", "111"]) # Escape/Back để ẩn phím
    time.sleep(1.5)
    
    # Bấm ĐĂNG (Post)
    print(f"[{serial}] 🚀 6. Bấm ĐĂNG (Post)...")
    tap(880, 2150, delay=5.0)
    print(f"[{serial}] ✅ Hoàn tất thao tác đăng!")
    return True

# -------------------------------------------------------------
# MASTER PIPELINE ORCHESTRATOR
# -------------------------------------------------------------
def run_master_farm_stream(selected_devices: Optional[List[str]] = None):
    print("="*70)
    print("🚀 BẮT ĐẦU CHẠY LUỒNG TỰ ĐỘNG ĐĂNG BÀI TOÀN BỘ DÀN PHONE FARM")
    print(f"⏰ Thời gian khởi động: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # 1. Đọc danh sách máy từ tai_khoan_farm.json
    with open(FARM_JSON_FILE, "r", encoding="utf-8") as f:
        devices = json.load(f)

    # Lọc máy có kênh nguồn và đang live
    active_devices = [
        d for d in devices
        if d.get("source_channel_url") and "Tam hoan" not in d.get("status", "")
    ]
    if selected_devices:
        active_devices = [d for d in active_devices if d.get("serial") in selected_devices]

    print(f"[*] Tổng số máy sẵn sàng chạy luồng: {len(active_devices)} máy.\n")

    downloaded_ids = load_downloaded_ids()
    download_tasks = []

    # ---------------------------------------------------------
    # PHA 1: TẢI VIDEO AN TOÀN (2 LUỒNG ĐỂ TRÁNH BOT CHECK YOUTUBE)
    # ---------------------------------------------------------
    print("="*70)
    print("📥 PHA 1: TẢI VIDEO NGUỒN (CHẠY 2 LUỒNG AN TOÀN TRÁNH BỊ YOUTUBE QUÉT)")
    print("="*70)

    def download_job(dev):
        serial = dev["serial"]
        box_name = dev["box_name"]
        src = dev["source_channel_url"]
        target_dir = os.path.join(RAW_DIR, serial)
        os.makedirs(target_dir, exist_ok=True)
        
        print(f"[{box_name}] Đang quét kênh: {src}")
        time.sleep(random.uniform(1.0, 2.5)) # Giãn cách an toàn
        info = download_one_short(src, downloaded_ids, target_dir)
        return {"device": dev, "video_info": info}

    downloaded_results = []
    # Dùng 2 workers để không bị YouTube phát hiện cào dồn dập
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(download_job, dev): dev for dev in active_devices}
        for future in as_completed(futures):
            try:
                res = future.result()
                if res.get("video_info"):
                    downloaded_results.append(res)
                    print(f"[{res['device']['box_name']}] ✅ Tải thành công video: {res['video_info']['title'][:35]}...")
                else:
                    print(f"[{res['device']['box_name']}] ⚠️ Không tìm thấy video mới hoặc đã tải hết.")
            except Exception as e:
                print(f"[-] Lỗi trong luồng tải: {e}")

    print(f"\n[*] Đã tải xong: {len(downloaded_results)} / {len(active_devices)} video mới.\n")
    if not downloaded_results:
        print("[-] Không có video mới để xử lý. Kết thúc luồng.")
        return

    # ---------------------------------------------------------
    # PHA 2: RENDER GPU NVENC ĐA LUỒNG (LÁCH BẢN QUYỀN TỰ ĐỘNG)
    # ---------------------------------------------------------
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
            print(f"[{dev['box_name']}] ⚡ GPU Render hoàn tất trong {dur}s: {os.path.basename(out_file)}")
            return {"device": dev, "video_info": vid, "processed_file": out_file}
        else:
            print(f"[{dev['box_name']}] ❌ Render thất bại: {vid['file_path']}")
            return None

    # Render 4 luồng GPU song song cực nhanh
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(render_job, item) for item in downloaded_results]
        for f in as_completed(futures):
            res = f.result()
            if res:
                render_results.append(res)

    print(f"\n[*] Đã render thành công: {len(render_results)} video bằng GPU NVENC.\n")

    # ---------------------------------------------------------
    # PHA 3: ĐẨY VIDEO VÀO ĐIỆN THOẠI CÙNG LÚC (PARALLEL PUSH)
    # ---------------------------------------------------------
    print("="*70)
    print("📤 PHA 3: ĐẨY VIDEO ĐỒNG LOẠT VÀO 14 ĐIỆN THOẠI (PARALLEL ADB PUSH)")
    print("="*70)

    pushed_results = []
    def push_job(item):
        serial = item["device"]["serial"]
        box = item["device"]["box_name"]
        local_file = item["processed_file"]
        remote = push_video_to_phone(serial, local_file)
        if remote:
            print(f"[{box}] 📲 Đã đẩy video vào máy ({remote})")
            item["remote_path"] = remote
            return item
        else:
            print(f"[{box}] ❌ Lỗi đẩy video vào máy")
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(push_job, item) for item in render_results]
        for f in as_completed(futures):
            res = f.result()
            if res:
                pushed_results.append(res)

    print(f"\n[*] Đã nạp video vào thư viện của {len(pushed_results)} máy thành công.\n")

    # ---------------------------------------------------------
    # PHA 4: ĐĂNG BÀI ĐA LUỒNG CÓ GIÃN CÁCH (BẢO VỆ PROXY & TỰ NHIÊN)
    # ---------------------------------------------------------
    print("="*70)
    print("🎬 PHA 4: ĐĂNG TIKTOK TỰ ĐỘNG ĐỒNG LOẠT TRÊN CÁC ĐIỆN THOẠI")
    print("="*70)

    posted_success = []
    for item in pushed_results:
        dev = item["device"]
        vid = item["video_info"]
        serial = dev["serial"]
        box = dev["box_name"]
        topic = dev.get("topic", "Tong Hop")
        
        # Sinh caption tiếng Việt + Hashtag theo Niche
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
            print(f"[{box}] ❌ Lỗi khi đăng: {e}")
            
        # Giãn cách 8-12 giây giữa các máy để bảo vệ proxy và tự nhiên
        print(f"[*] Nghỉ 10s trước khi sang máy tiếp theo...\n")
        time.sleep(10.0)

    # ---------------------------------------------------------
    # PHA 5: TỔNG KẾT VÀ BÁO CÁO
    # ---------------------------------------------------------
    print("="*70)
    print(f"🎉 TỔNG KẾT LUỒNG FARM: ĐĂNG THÀNH CÔNG {len(posted_success)} / {len(active_devices)} MÁY!")
    print("="*70)
    for p in posted_success:
        print(f" ✅ {p['box']}: {p['title']}")
        
    # Ghi lịch sử CSV
    with open(HISTORY_CSV, "a", encoding="utf-8") as f:
        for p in posted_success:
            f.write(f"{p['time']},{p['box']},{p['serial']},{p['title']},SUCCESS\n")

if __name__ == "__main__":
    run_master_farm_stream()
