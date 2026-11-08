"""
Mô-đun Xử lý Video Reup & Lách Bản Quyền Tự Động cho TikTok (Auto Anti-Detection Video Processor)
Chức năng:
1. Tải video không logo (watermark) từ Douyin, TikTok, Facebook Reels, YouTube Shorts bằng yt-dlp.
2. Tự động lách thuật toán Content ID / Deep Learning của ByteDance:
   - Cắt đầu đuôi ngẫu nhiên (Trim)
   - Lật gương (Horizontal Flip)
   - Phóng to & cắt viền (Zoom & Crop)
   - Tăng tốc độ tự nhiên (Speed 1.03x - 1.06x)
   - Chỉnh màu, độ sáng, độ tương phản (Color Grading)
   - Xóa toàn bộ Metadata, tạo Hash MD5 mới tinh
3. Xuất video sang thư mục 'videos/' sẵn sàng nạp vào dàn Phone Farm 17 máy.
"""

import os
import random
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

import imageio_ffmpeg
from yt_dlp import YoutubeDL

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "videos")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


class AutoReupProcessor:
    def __init__(self):
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    def get_video_duration(self, video_path: str) -> float:
        """Lấy độ dài thời gian của video bằng FFmpeg."""
        try:
            cmd = [self.ffmpeg_path, "-i", video_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
            for line in res.stderr.split("\n"):
                if "Duration:" in line:
                    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", line)
                    if match:
                        h, m, s = match.groups()
                        return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception as e:
            print(f"[-] Lỗi đọc thời lượng video: {e}")
        return 0.0

    def process_video(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        hflip: bool = False,
        speed_range: Tuple[float, float] = (1.03, 1.06),
        zoom_range: Tuple[float, float] = (1.03, 1.05),
        trim_head_range: Tuple[float, float] = (0.5, 1.0),
        trim_tail_range: Tuple[float, float] = (0.8, 1.5),
    ) -> bool:
        """
        Xử lý lách bản quyền cho 1 video với các tham số biến thiên ngẫu nhiên (Jitter).
        """
        if not os.path.isfile(input_path):
            print(f"[-] Không tìm thấy file: {input_path}")
            return False

        duration = self.get_video_duration(input_path)
        if duration <= 3.0:
            print(f"[-] Video quá ngắn ({duration:.1f}s), không thể cắt tỉa an toàn!")
            return False

        if not output_path:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            clean_name = re.sub(r"[^\w\-]", "_", base_name)
            output_path = os.path.join(OUTPUT_DIR, f"reup_{int(time.time())}_{clean_name}.mp4")

        # 1. Tính toán cắt đầu / đuôi ngẫu nhiên
        trim_head = round(random.uniform(*trim_head_range), 2)
        trim_tail = round(random.uniform(*trim_tail_range), 2)
        target_duration = max(2.0, duration - trim_head - trim_tail)

        # 2. Tính toán tốc độ & zoom ngẫu nhiên
        speed = round(random.uniform(*speed_range), 3)
        pts = round(1.0 / speed, 4)
        zoom = round(random.uniform(*zoom_range), 3)

        # 3. Tính toán màu sắc ngẫu nhiên nhẹ (không làm đổi mắt thường)
        contrast = round(random.uniform(1.02, 1.05), 3)
        brightness = round(random.uniform(-0.01, 0.02), 3)
        saturation = round(random.uniform(1.02, 1.06), 3)

        # 4. Xây dựng chuỗi bộ lọc hình ảnh (Video Filters)
        v_filters = []
        if hflip:
            v_filters.append("hflip")
        # Phóng to và crop để xóa tọa độ pixel gốc
        v_filters.append(f"scale={zoom}*iw:{zoom}*ih,crop=iw/{zoom}:ih/{zoom}")
        # Chỉnh màu
        v_filters.append(f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation}")
        # Tăng tốc độ hình ảnh
        v_filters.append(f"setpts={pts}*PTS")

        vf_str = ",".join(v_filters)
        af_str = f"atempo={speed}"

        print(f"[*] Đang xử lý lách bản quyền: {os.path.basename(input_path)}")
        print(f"    -> Cắt đầu: {trim_head}s | Cắt đuôi: {trim_tail}s | Tốc độ: {speed}x | Zoom: {zoom}x | Lật gương: {hflip}")

        cmd = [
            self.ffmpeg_path, "-y",
            "-ss", str(trim_head),
            "-i", input_path,
            "-t", str(target_duration),
            "-vf", vf_str,
            "-af", af_str,
            "-map_metadata", "-1",  # Xóa sạch thông tin thiết bị/tác giả gốc
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            output_path
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
        if res.returncode == 0 and os.path.isfile(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"[+] ✅ Xử lý thành công! File xuất ra ({size_mb:.2f} MB): {output_path}")
            return True
        else:
            print(f"[-] ❌ Lỗi xử lý FFmpeg: {res.stderr[-300:].strip()}")
            return False

    def batch_process_folder(self, raw_folder: str = RAW_DIR, output_folder: str = OUTPUT_DIR, hflip: bool = False) -> List[str]:
        """Xử lý hàng loạt toàn bộ video trong thư mục raw_videos."""
        files = [
            os.path.join(raw_folder, f)
            for f in os.listdir(raw_folder)
            if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm"))
        ]

        if not files:
            print(f"[-] Không có video nào trong: {raw_folder}")
            print(f"👉 Vui lòng copy video cần lách vào thư mục: {raw_folder}")
            return []

        print(f"\n========================================================")
        print(f"🚀 BẮT ĐẦU XỬ LÝ LÁCH BẢN QUYỀN HÀNG LOẠT ({len(files)} FILE)")
        print(f"⚙️  Chế độ Lật Gương (hflip): {'BẬT' if hflip else 'TẮT (Giữ nguyên chiều chữ chuẩn)'}")
        print(f"========================================================")

        success_files = []
        for idx, f in enumerate(files, 1):
            print(f"\n[{idx}/{len(files)}] ----------------------------------------")
            base = os.path.splitext(os.path.basename(f))[0]
            clean_base = re.sub(r"[^\w\-]", "_", base)
            out_file = os.path.join(output_folder, f"ready_{idx}_{clean_base}.mp4")

            ok = self.process_video(f, out_file, hflip=hflip)
            if ok:
                success_files.append(out_file)

        print(f"\n========================================================")
        print(f"🎉 HOÀN TẤT! Đã biến đổi {len(success_files)}/{len(files)} video mới tinh.")
        print(f"📂 Thư mục chứa video sẵn sàng đăng: {output_folder}")
        print(f"========================================================\n")
        return success_files

    def download_douyin_video(self, url: str, output_dir: str = RAW_DIR) -> Optional[str]:
        """Tải video Douyin không logo Full HD bằng API giải mã A_Bogus / X-Bogus."""
        import requests
        print(f"[*] Đang bóc tách link Douyin: {url}...")
        try:
            # Rút trích video ID nếu có trong link
            match = re.search(r"vid=(\d+)|video/(\d+)", url)
            clean_url = f"https://www.douyin.com/video/{match.group(1) or match.group(2)}" if match else url

            s = requests.Session()
            # 1. Lấy auth demo
            r_demo = s.get("https://demo.douyin.wtf/api/v1/auth/demo", timeout=10).json()
            if r_demo.get("success") and r_demo.get("data"):
                u = r_demo["data"]["username"]
                p = r_demo["data"]["password"]
                s.post("https://demo.douyin.wtf/api/v1/auth/login", json={"username": u, "password": p}, timeout=10)

            # 2. Gửi tác vụ bóc tách
            r_parse = s.post("https://demo.douyin.wtf/api/v1/parse", json={"url": clean_url}, timeout=15).json()
            if not r_parse.get("success") or not r_parse.get("data"):
                raise ValueError("Không tạo được tác vụ parse Douyin")

            task_id = r_parse["data"]["task_id"]

            # 3. Chờ lấy link stream gốc
            for _ in range(12):
                time.sleep(1.5)
                r_task = s.get(f"https://demo.douyin.wtf/api/v1/tasks/{task_id}", timeout=10).json()
                if r_task.get("data", {}).get("state") == "done":
                    t_data = r_task["data"]["data"]
                    desc = t_data.get("title") or t_data.get("description") or "douyin_video"
                    clean_title = re.sub(r"[^\w\-]", "_", desc)[:40]

                    media = t_data.get("media", {})
                    v_url = None
                    if media.get("video") and media["video"].get("url"):
                        v_url = media["video"]["url"]
                    elif media.get("streams"):
                        for st in media["streams"]:
                            if not st.get("watermark") and st.get("url"):
                                v_url = st["url"]
                                break

                    if v_url:
                        out_path = os.path.join(output_dir, f"douyin_{int(time.time())}_{clean_title}.mp4")
                        print(f"[*] Đang tải video không logo về: {out_path}...")
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                            "Referer": "https://www.douyin.com/"
                        }
                        dl_res = requests.get(v_url, headers=headers, stream=True, timeout=30)
                        with open(out_path, "wb") as f:
                            for chunk in dl_res.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    f.write(chunk)
                        size_mb = os.path.getsize(out_path) / (1024 * 1024)
                        print(f"[+] ✅ Tải video Douyin thành công! Dung lượng: {size_mb:.2f} MB")
                        return out_path
                    break
        except Exception as e:
            print(f"[-] Lỗi qua Douyin API ({e}), chuyển sang phương thức dự phòng...")
        return None

    def download_douyin_channel(self, channel_url: str, max_videos: int = 20, output_dir: str = RAW_DIR) -> List[str]:
        """Quét và tải hàng loạt toàn bộ video của 1 kênh Douyin KHÔNG CẦN ĐĂNG NHẬP."""
        import requests
        print(f"\n========================================================")
        print(f"🔍 ĐANG QUÉT TOÀN BỘ VIDEO TỪ KÊNH DOUYIN...")
        print(f"🔗 Link kênh: {channel_url}")
        print(f"========================================================")

        # Trích xuất sec_user_id
        m = re.search(r"user/([a-zA-Z0-9_\-]+)", channel_url)
        if not m:
            print("[-] Không tìm thấy User ID trong link kênh!")
            return []
        sec_user_id = m.group(1)

        downloaded_files = []
        try:
            s = requests.Session()
            r_demo = s.get("https://demo.douyin.wtf/api/v1/auth/demo", timeout=10).json()
            if r_demo.get("success") and r_demo.get("data"):
                u = r_demo["data"]["username"]
                p = r_demo["data"]["password"]
                s.post("https://demo.douyin.wtf/api/v1/auth/login", json={"username": u, "password": p}, timeout=10)

            cursor = 0
            has_more = True
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/"
            }
            cookie_file = os.path.join(BASE_DIR, "douyin_cookie.txt")
            if os.path.isfile(cookie_file):
                with open(cookie_file, "r", encoding="utf-8") as cf:
                    headers["Cookie"] = cf.read().strip()
                print("[*] Đã gắn Cookie đăng nhập vào phiên tải.")

            while has_more and len(downloaded_files) < max_videos:
                params = {"sec_user_id": sec_user_id, "count": 15, "cursor": cursor}
                r = s.get("https://demo.douyin.wtf/api/v1/douyin/user/posts", params=params, timeout=15).json()
                if not r.get("success") or not r.get("data"):
                    break
                task_id = r["data"]["task_id"]

                # Chờ kết quả quét
                t_data = None
                for _ in range(12):
                    time.sleep(1.5)
                    r_task = s.get(f"https://demo.douyin.wtf/api/v1/tasks/{task_id}", timeout=10).json()
                    if r_task.get("data", {}).get("state") == "done":
                        t_data = r_task["data"]["data"]
                        break

                if not t_data:
                    break

                items = t_data.get("items", [])
                print(f"[*] Quét thấy {len(items)} video trong đợt này...")

                for idx, item in enumerate(items, 1):
                    if len(downloaded_files) >= max_videos:
                        break
                    desc = item.get("title") or item.get("description") or "douyin"
                    clean_title = re.sub(r"[^\w\-]", "_", desc)[:35]
                    v_url = item.get("media", {}).get("video", {}).get("url")
                    if not v_url and item.get("media", {}).get("streams"):
                        for st in item["media"]["streams"]:
                            if not st.get("watermark") and st.get("url"):
                                v_url = st["url"]
                                break

                    if v_url:
                        out_path = os.path.join(output_dir, f"douyin_{len(downloaded_files)+1}_{clean_title}.mp4")
                        print(f"[{len(downloaded_files)+1}/{max_videos}] Đang tải: {clean_title}...")
                        dl_res = requests.get(v_url, headers=headers, stream=True, timeout=30)
                        with open(out_path, "wb") as f:
                            for chunk in dl_res.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    f.write(chunk)
                        downloaded_files.append(out_path)

                has_more = t_data.get("has_more", False)
                cursor = t_data.get("cursor", 0)

            print(f"\n[+] 🎉 HOÀN TẤT! Đã quét và tải {len(downloaded_files)} video không logo về: {output_dir}")
            return downloaded_files

        except Exception as e:
            print(f"[-] Lỗi khi quét kênh Douyin: {e}")
            return downloaded_files

    def download_url(self, url: str, output_dir: str = RAW_DIR) -> Optional[str]:
        """Tải video không logo (No Watermark) từ Douyin, TikTok, Reels, Shorts."""
        print(f"\n[*] Đang tải video không logo từ: {url}...")
        
        # Nếu là link Douyin, dùng bộ bóc tách chuyên dụng
        if "douyin.com" in url:
            res = self.download_douyin_video(url, output_dir)
            if res:
                return res

        ydl_opts = {
            "outtmpl": os.path.join(output_dir, "%(title).50s_%(id)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "ffmpeg_location": self.ffmpeg_path,
            "quiet": False,
            "no_warnings": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base, ext = os.path.splitext(filename)
                if not os.path.isfile(filename) and os.path.isfile(base + ".mp4"):
                    filename = base + ".mp4"

                print(f"[+] ✅ Tải thành công: {filename}")
                return filename
        except Exception as e:
            print(f"[-] ❌ Lỗi khi tải video từ link: {e}")
            return None


def main():
    processor = AutoReupProcessor()

    while True:
        raw_count = len([f for f in os.listdir(RAW_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm"))])
        ready_count = len([f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm"))])

        print("=================================================================")
        print("🎬 CÔNG CỤ XỬ LÝ VIDEO REUP & LÁCH BẢN QUYỀN TIKTOK TỰ ĐỘNG")
        print(f"📁 Video thô trong 'raw_videos/' : {raw_count} file")
        print(f"📁 Video đã lách trong 'videos/' : {ready_count} file (Sẵn sàng đăng)")
        print("=================================================================")
        print("[1] ⚡ Lách bản quyền TOÀN BỘ video trong 'raw_videos/'")
        print("[2] 📥 Tải 1 video không logo từ Link (TikTok / Douyin / Reels / Shorts)")
        print("[3] 📥 Tải hàng loạt video từ danh sách link (File .txt)")
        print("[4] 🎯 Tự động tải từ link VÀ Lách bản quyền luôn")
        print("[5] 📺 Quét & Tải hàng loạt video từ Kênh Douyin")
        print("[6] 📱 Quét mã QR đăng nhập Douyin (Lưu Cookie để mở khóa tải toàn bộ kênh)")
        print("[0] Thoát")
        print("=================================================================")

        choice = input("👉 Nhập lựa chọn (0-6): ").strip()

        if choice == "1":
            print("\n⚙️ Chọn chế độ lách bản quyền:")
            print(" [1] Video CÓ CHỮ / Phụ đề tiếng Việt -> KHÔNG LẬT GƯƠNG (đảm bảo chữ đọc xuôi 100%)")
            print(" [2] Video KHÔNG có chữ (gái nhảy, phong cảnh, ẩm thực) -> CÓ LẬT GƯƠNG")
            mode = input("👉 Lựa chọn (1 hoặc 2, Mặc định: 1): ").strip()
            hflip = (mode == "2")
            processor.batch_process_folder(hflip=hflip)

        elif choice == "2":
            url = input("👉 Dán link video (TikTok/Douyin/Reels/Shorts): ").strip()
            if url:
                processor.download_url(url)

        elif choice == "3":
            txt_path = input("👉 Nhập đường dẫn file text chứa link (Enter để dùng 'links.txt'): ").strip(' "\'')
            if not txt_path:
                txt_path = os.path.join(BASE_DIR, "links.txt")
            if os.path.isfile(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                print(f"[*] Tìm thấy {len(urls)} link trong file: {txt_path}")
                for u in urls:
                    processor.download_url(u)
            else:
                print(f"[-] Không tìm thấy file: {txt_path}")

        elif choice == "4":
            url = input("👉 Dán link video cần tải & lách luôn: ").strip()
            if url:
                downloaded = processor.download_url(url)
                if downloaded:
                    print("[*] Đang tự động chuyển sang khâu lách bản quyền...")
                    processor.process_video(downloaded)

        elif choice == "5":
            url = input("👉 Dán link kênh Douyin (vd: https://www.douyin.com/user/...): ").strip()
            if url:
                limit_input = input("Nhập số lượng video muốn tải (mặc định: 15): ").strip()
                max_v = int(limit_input) if limit_input.isdigit() else 15
                processor.download_douyin_channel(url, max_videos=max_v)

        elif choice == "6":
            os.system(f'python "{os.path.join(os.path.dirname(__file__), "douyin_login_helper.py")}"')

        elif choice == "0":
            break


if __name__ == "__main__":
    main()
