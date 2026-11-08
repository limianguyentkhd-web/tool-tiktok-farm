import os
import sys
import subprocess
from yt_dlp import YoutubeDL
from farm_tracker import FarmTracker

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

FFMPEG_PATH = r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
RAW_DIR = r"d:\TOOL TIKTOK\raw_videos"
READY_DIR = r"d:\TOOL TIKTOK\videos"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(READY_DIR, exist_ok=True)

class MediaDownloader:
    def __init__(self):
        self.raw_dir = RAW_DIR
        self.ffmpeg_path = FFMPEG_PATH
        self.tracker = FarmTracker()

    def download_youtube_shorts(self, channel_or_url: str, limit: int = 5, auto_reup: bool = True):
        """
        Tải video YouTube Shorts từ kênh hoặc URL cụ thể.
        Cơ chế tự động rà soát thông minh:
        - Quét toàn bộ danh sách video của kênh.
        - Tự động bỏ qua các video ĐÃ TỪNG TẢI hoặc ĐÃ TỪNG ĐĂNG.
        - Chỉ bóc tách các video mới tinh chưa từng xuất hiện trong hệ thống.
        """
        print(f"\n========================================================")
        print(f"🎬 BẮT ĐẦU RÀ SOÁT & TẢI YOUTUBE SHORTS (Mục tiêu: {limit} video mới)")
        print(f"🔗 Nguồn: {channel_or_url}")
        print(f"========================================================")

        print(f"[*] Đang quét danh mục toàn kênh...")
        try:
            with YoutubeDL({'extract_flat': True, 'quiet': True}) as ydl:
                info = ydl.extract_info(channel_or_url, download=False)
                all_entries = list(info.get('entries', []))
        except Exception as e:
            print(f"[-] Lỗi bóc tách danh mục kênh: {e}")
            all_entries = []

        if not all_entries:
            print("[*] Không lấy được danh sách theo chuẩn kênh, tiến hành tải trực tiếp theo URL...")
            to_download = [channel_or_url]
        else:
            print(f"[*] Kênh có tổng cộng {len(all_entries)} video. Bắt đầu rà soát cơ sở dữ liệu...")
            new_urls = []
            for e in all_entries:
                vid_id = e.get('id', '')
                vid_url = f"https://www.youtube.com/shorts/{vid_id}"
                title = e.get('title', '')
                if self.tracker.is_video_already_handled(vid_id):
                    print(f"  ⏭️ [BỎ QUA] '{title[:45]}...' (ID: {vid_id}) -> Đã từng tải/đăng.")
                else:
                    new_urls.append(vid_url)
                    print(f"  ✨ [MỚI TINH] '{title[:45]}...' (ID: {vid_id})")
                    if len(new_urls) >= limit:
                        break

            if not new_urls:
                print(f"\n[+] 🎉 TOÀN BỘ VIDEO TRÊN KÊNH NÀY ĐÃ ĐƯỢC TẢI/ĐĂNG HẾT! Không có video mới trùng lặp.")
                return []

            to_download = new_urls

        # Định dạng output template
        outtmpl = os.path.join(self.raw_dir, "%(title)s_%(id)s.%(ext)s")

        def ydl_hook(d):
            if d.get('status') == 'finished':
                fn = os.path.basename(d.get('filename', ''))
                info = d.get('info_dict', {})
                url = info.get('webpage_url') or channel_or_url
                chan = info.get('uploader') or info.get('channel') or channel_or_url
                title = info.get('title', '')
                self.tracker.record_download(fn, url, chan, title)

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': outtmpl,
            'quiet': False,
            'no_warnings': True,
            'ffmpeg_location': self.ffmpeg_path,
            'ignoreerrors': True,
            'progress_hooks': [ydl_hook],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(to_download)

        print(f"\n[+] Tải hoàn tất {len(to_download)} video mới vào: {self.raw_dir}")

        if auto_reup:
            print("\n[*] Tự động chuyển sang khâu Lách Bản Quyền Chuẩn Chữ Xuôi (FFmpeg)...")
            from auto_reup_processor import AutoReupProcessor
            p = AutoReupProcessor()
            p.batch_process_folder(self.raw_dir, READY_DIR, hflip=False)
            print("[+] ✅ Toàn bộ video đã được lách xong và sẵn sàng trong thư mục 'videos'!")

    def download_url(self, url: str):
        """
        Tải 1 video bất kỳ từ YouTube, Facebook Reels, TikTok, Douyin...
        """
        print(f"\n========================================================")
        print(f"📥 ĐANG TẢI VIDEO TỪ URL: {url}")
        print(f"========================================================")

        outtmpl = os.path.join(self.raw_dir, "%(title)s_%(id)s.%(ext)s")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': outtmpl,
            'quiet': False,
            'no_warnings': True,
            'ffmpeg_location': self.ffmpeg_path,
            'ignoreerrors': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print(f"\n[+] Tải thành công vào thư mục: {self.raw_dir}")

def show_menu():
    dl = MediaDownloader()
    while True:
        print("\n" + "="*50)
        print("          TOOL TẢI VIDEO REELS / SHORTS         ")
        print("="*50)
        print(" [1] Tải hàng loạt YouTube Shorts từ kênh (VD: @zim_video/shorts)")
        print(" [2] Tải 1 link bất kỳ (YouTube / FB Reels / TikTok)")
        print(" [3] Chạy Auto Lách Bản Quyền cho toàn bộ thư mục raw_videos")
        print(" [0] Quay lại menu chính")
        print("="*50)

        choice = input("👉 Lựa chọn của bạn: ").strip()
        if choice == '1':
            url = input("Nhập link kênh Shorts (Enter để dùng kênh @zim_video/shorts): ").strip()
            if not url:
                url = "https://www.youtube.com/@zim_video/shorts"
            limit_str = input("Số lượng video muốn tải (Mặc định: 5): ").strip()
            limit = int(limit_str) if limit_str.isdigit() else 5
            dl.download_youtube_shorts(url, limit=limit)
        elif choice == '2':
            url = input("Dán link video cần tải (FB Reels, YT Shorts, v.v.): ").strip()
            if url:
                dl.download_url(url)
        elif choice == '3':
            from auto_reup_processor import AutoReupProcessor
            processor = AutoReupProcessor()
            print("\n⚙️ Chọn chế độ lách bản quyền:")
            print(" [1] Video CÓ CHỮ / Phụ đề tiếng Việt -> KHÔNG LẬT GƯƠNG (chữ đọc xuôi tự nhiên 100%)")
            print(" [2] Video KHÔNG có chữ (gái nhảy, phong cảnh, ẩm thực) -> CÓ LẬT GƯƠNG")
            mode = input("👉 Lựa chọn (1 hoặc 2, Mặc định: 1): ").strip()
            hflip = (mode == "2")
            processor.batch_process_folder(RAW_DIR, READY_DIR, hflip=hflip)
        elif choice == '0':
            break
        else:
            print("Lựa chọn không hợp lệ!")

if __name__ == '__main__':
    show_menu()
