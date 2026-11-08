"""
Module tự động hóa đẩy video từ máy tính sang Phone Farm và đăng bài lên TikTok (TikTok Video Uploader)
Tích hợp đấu nối API Key AI (Gemini / OpenAI / DeepSeek) để tự động tạo Caption cuốn hút & Hashtag chuẩn SEO.
"""

import base64
import os
import random
import subprocess
import sys
import time
from typing import List, Optional

from device_manager import DeviceManager
from caption_generator import AICaptionGenerator, configure_interactive

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class TikTokVideoUploader:
    def __init__(self, port: str = "5037"):
        self.port = port
        self.ai_generator = AICaptionGenerator()

    def _adb_cmd(self, serial: str, args: List[str]) -> subprocess.CompletedProcess:
        cmd = ["adb"]
        if self.port != "5037":
            cmd.extend(["-P", self.port])
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

    def push_video_to_device(self, serial: str, local_video_path: str, remote_filename: Optional[str] = None) -> str:
        """
        Đẩy video từ máy tính vào thư mục ảnh/video của điện thoại và cập nhật thư viện media.
        """
        if not os.path.isfile(local_video_path):
            raise FileNotFoundError(f"Không tìm thấy file video: {local_video_path}")

        if not remote_filename:
            base = os.path.basename(local_video_path)
            remote_filename = f"vid_{int(time.time())}_{base}"

        remote_path = f"/sdcard/DCIM/Camera/{remote_filename}"
        print(f"[{serial}] 🚀 Đang đẩy video sang thiết bị: {remote_path}...")
        res = self._adb_cmd(serial, ["push", local_video_path, remote_path])
        if res.returncode != 0:
            print(f"[{serial}] ❌ Lỗi push video: {res.stderr.strip()}")
            return ""

        # Kích hoạt MediaScanner để Android MediaStore lập chỉ mục ngay
        self._adb_cmd(serial, ["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"])
        self._adb_cmd(serial, ["shell", "content", "call", "--uri", "content://media/external/file", "--method", "scan_file", "--arg", remote_path])
        print(f"[{serial}] ✅ Đã nạp video và cập nhật MediaScanner thành công.")
        return remote_path

    def setup_keyboard(self, serial: str) -> None:
        """Kích hoạt và đặt ADBKeyboard làm bàn phím mặc định để gõ tiếng Việt."""
        ime = "com.android.adbkeyboard/.AdbIME"
        self._adb_cmd(serial, ["shell", "ime", "enable", ime])
        self._adb_cmd(serial, ["shell", "ime", "set", ime])

    def input_vietnamese_text(self, serial: str, text: str) -> None:
        """Gõ tiếng Việt có dấu và emoji vào ô đang focus qua ADBKeyboard."""
        b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        self._adb_cmd(serial, ["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])

    def upload_video(
        self,
        serial: str,
        local_video_path: str,
        caption: str = "auto",
        dismiss_popups: bool = True
    ) -> bool:
        """
        Quy trình trọn gói:
        1. Xử lý caption (nếu chọn 'auto' hoặc 'ai' -> tự động gọi API Key sinh caption)
        2. Đẩy video từ máy tính vào máy
        3. Bật TikTok
        4. Chọn video đầu tiên từ Album
        5. Chuyển qua màn hình chỉnh sửa & Tiếp tục
        6. Nhập caption tiếng Việt có dấu
        7. Bấm Đăng (Post)
        """
        # Nếu caption là 'ai' hoặc 'auto', gọi AI sinh caption theo tên video
        final_caption = caption
        if not caption or caption.lower() in ["ai", "auto"]:
            base_name = os.path.splitext(os.path.basename(local_video_path))[0]
            clean_topic = base_name.replace("_", " ").replace("-", " ")
            print(f"[{serial}] 🤖 Đang gọi AI API tạo Caption cho chủ đề: '{clean_topic}'...")
            final_caption = self.ai_generator.generate_caption(clean_topic)

        print(f"\n========================================================")
        print(f"🎬 BẮT ĐẦU ĐĂNG VIDEO TRÊN THIẾT BỊ [{serial}]")
        print(f"📝 Caption: {final_caption}")
        print(f"========================================================")

        # 1. Cài đặt bàn phím gõ tiếng Việt
        self.setup_keyboard(serial)

        # 2. Đẩy video vào máy
        remote_path = self.push_video_to_device(serial, local_video_path)
        if not remote_path:
            return False

        time.sleep(1.5)

        # Đánh thức màn hình và mở khóa
        self._adb_cmd(serial, ["shell", "input", "keyevent", "224"])
        self._adb_cmd(serial, ["shell", "input", "keyevent", "82"])

        # 3. Làm mới và khởi chạy TikTok từ đầu
        print(f"[{serial}] 📱 Đang khởi chạy TikTok...")
        self._adb_cmd(serial, ["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(4.0)

        # 4. Nhấn nút '+' (Create) ở thanh điều hướng dưới đáy màn hình
        print(f"[{serial}] ➕ Bấm nút Tạo video (+)...")
        self._adb_cmd(serial, ["shell", "input", "tap", "540", "2030"])
        time.sleep(2.5)

        # 5. Nhấn nút Upload / Tải lên (Album) góc dưới bên trái của Camera
        print(f"[{serial}] 🖼️  Mở thư viện Album (Upload)...")
        self._adb_cmd(serial, ["shell", "input", "tap", "90", "1920"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "input", "tap", "417", "563"])
        time.sleep(2.5)

        # 6. Chọn video mới nhất (chọn hình tròn tick số 1 ở góc trên bên phải thumbnail đầu tiên)
        print(f"[{serial}] 🎞️  Chọn video mới nạp...")
        self._adb_cmd(serial, ["shell", "input", "tap", "300", "320"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "input", "tap", "180", "500"])
        time.sleep(1.5)

        # 7. Nhấn nút Tiếp (Next / Next (1)) ở góc dưới bên phải
        print(f"[{serial}] ➡️  Bấm 'Tiếp' để tải video vào trình chỉnh sửa...")
        self._adb_cmd(serial, ["shell", "input", "tap", "740", "1990"])
        time.sleep(3.5)

        # 8. Màn hình chỉnh sửa video: Nhấn nút Tiếp (Next) sang màn hình Đăng
        print(f"[{serial}] ➡️  Bấm 'Tiếp' sang màn hình Đăng bài...")
        self._adb_cmd(serial, ["shell", "input", "tap", "740", "1990"])
        time.sleep(1.5)
        self._adb_cmd(serial, ["shell", "input", "tap", "996", "136"])
        time.sleep(3.0)

        # 9. Nhập tiêu đề / mô tả (Caption) với cơ chế Rà Soát Chống Mất Chữ
        print(f"[{serial}] ✍️  Đang nhập tiêu đề vào TikTok...")
        # Chạm đúng tâm điểm ô mô tả
        self._adb_cmd(serial, ["shell", "input", "tap", "350", "400"])
        time.sleep(1.2)
        # Gõ tiếng Việt qua ADBKeyboard
        self.input_vietnamese_text(serial, final_caption + " ")
        time.sleep(1.5)

        # Rà soát xem chữ đã vào ô chưa (Chống tình trạng hụt con trỏ)
        self._adb_cmd(serial, ["shell", "uiautomator", "dump", "/data/local/tmp/cap_check.xml"])
        cap_dump = self._adb_cmd(serial, ["shell", "cat", "/data/local/tmp/cap_check.xml"]).stdout
        if "Add description..." in cap_dump:
            print(f"[{serial}] ⚠️ Chưa nhận con trỏ, đang ép nhận qua nút Hashtags...")
            self._adb_cmd(serial, ["shell", "input", "tap", "160", "690"]) # Bấm nút # Hashtags để ép focus
            time.sleep(1.0)
            self.input_vietnamese_text(serial, final_caption + " ")
            time.sleep(1.5)

        # Đóng bàn phím an toàn (dùng ESC để không bị Back thoát màn hình)
        self._adb_cmd(serial, ["shell", "input", "keyevent", "111"])
        time.sleep(1.0)

        # 10. Bấm nút ĐĂNG (POST)
        print(f"[{serial}] 🚀 Đang bấm nút ĐĂNG (POST)...")
        self._adb_cmd(serial, ["shell", "input", "tap", "740", "1930"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "input", "tap", "799", "1999"])
        time.sleep(4.0)

        # 11. Xử lý các popup sau đăng (nếu có)
        if dismiss_popups:
            # Bấm Hủy nếu hiện hỏi thêm phím tắt ra màn hình chính
            self._adb_cmd(serial, ["shell", "input", "tap", "308", "1950"])
            time.sleep(1.0)
            # Bấm Don't allow nếu hiện quyền bạn bè / danh bạ
            self._adb_cmd(serial, ["shell", "input", "tap", "355", "1360"])
            time.sleep(1.0)

        print(f"[{serial}] 🎉 ĐÃ HOÀN TẤT ĐĂNG VIDEO THÀNH CÔNG!")
        return True

    def batch_upload(
        self,
        video_dir_or_file: str,
        devices: Optional[List[str]] = None,
        caption: str = "ai",
        stagger_delay: int = 5
    ) -> None:
        """
        Đăng video hàng loạt lên nhiều thiết bị:
        - Nếu truyền file video đơn: đăng video đó lên tất cả máy.
        - Nếu truyền thư mục chứa nhiều video: tự động phân chia lần lượt mỗi máy 1 video khác nhau.
        - Caption hỗ trợ 'ai' để mỗi video có 1 caption độc nhất không trùng lặp.
        """
        if not devices:
            dm = DeviceManager([self.port])
            devices = dm.refresh_devices()

        if not devices:
            print("[-] Không tìm thấy thiết bị nào đang kết nối!")
            return

        videos = []
        if os.path.isfile(video_dir_or_file):
            videos = [video_dir_or_file]
        elif os.path.isdir(video_dir_or_file):
            for f in os.listdir(video_dir_or_file):
                if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
                    videos.append(os.path.join(video_dir_or_file, f))

        if not videos:
            print(f"[-] Không tìm thấy video hợp lệ trong: {video_dir_or_file}")
            return

        print(f"\n[*] Bắt đầu tiến trình đăng video trên {len(devices)} thiết bị...")
        print(f"[*] Danh sách video ({len(videos)} file): {[os.path.basename(v) for v in videos]}")

        for i, serial in enumerate(devices):
            vid = videos[i % len(videos)]
            try:
                self.upload_video(serial, vid, caption=caption)
            except Exception as e:
                print(f"[{serial}] ❌ Lỗi khi đăng: {e}")

            if i < len(devices) - 1:
                jitter = random.randint(stagger_delay, stagger_delay + 4)
                print(f"[*] Nghỉ {jitter}s trước khi đăng trên máy tiếp theo để chống spam...")
                time.sleep(jitter)


def main():
    dm = DeviceManager()
    devices = dm.refresh_devices()
    port = dm.active_port

    uploader = TikTokVideoUploader(port=port)

    while True:
        cfg = uploader.ai_generator.config
        key_status = "ĐÃ ĐẤU API (" + cfg.get("provider", "gemini").upper() + ")" if cfg.get("api_key") else "CHƯA CẤU HÌNH API"

        print("\n======================================================")
        print("🎬 TRÌNH ĐĂNG VIDEO TỰ ĐỘNG HÓA TIKTOK TỪ MÁY TÍNH")
        print(f"[*] Đang nhận diện {len(devices)} máy (Cổng ADB: {port})")
        print(f"[*] Trạng thái AI Caption: {key_status}")
        print("======================================================")
        print("[1] Đăng 1 video lên 1 máy chỉ định")
        print("[2] Đăng 1 video lên TOÀN BỘ máy kết nối")
        print("[3] Chia đều thư mục video (mỗi máy 1 video khác nhau)")
        print("[4] 🔑 Đấu nối API Key AI (Gemini / OpenAI / DeepSeek)")
        print("[0] Thoát")
        print("======================================================")

        choice = input("👉 Nhập lựa chọn (0-4): ").strip()

        if choice == "1":
            for idx, d in enumerate(devices, 1):
                print(f"  {idx}. {d}")
            idx_choice = input(f"Chọn máy (1-{len(devices)}): ").strip()
            if not idx_choice.isdigit() or not (1 <= int(idx_choice) <= len(devices)):
                print("[-] Lựa chọn không hợp lệ!")
                continue
            target_serial = devices[int(idx_choice) - 1]

            v_path = input("Nhập đường dẫn file video (.mp4) hoặc kéo thả file vào đây: ").strip(' "\'')
            if not os.path.isfile(v_path):
                print("[-] File video không tồn tại!")
                continue

            cap = input("Nhập caption (gõ 'ai' để AI tự viết, hoặc Enter lấy mặc định): ").strip()
            if not cap:
                cap = "ai"

            uploader.upload_video(target_serial, v_path, caption=cap)

        elif choice == "2":
            v_path = input("Nhập đường dẫn file video (.mp4) hoặc kéo thả file vào đây: ").strip(' "\'')
            if not os.path.isfile(v_path):
                print("[-] File video không tồn tại!")
                continue

            cap = input("Nhập caption (gõ 'ai' để AI tự viết, hoặc Enter lấy mặc định): ").strip()
            if not cap:
                cap = "ai"

            uploader.batch_upload(v_path, devices=devices, caption=cap)

        elif choice == "3":
            folder = input("Nhập đường dẫn thư mục chứa video: ").strip(' "\'')
            if not os.path.isdir(folder):
                print("[-] Thư mục không tồn tại!")
                continue

            cap = input("Nhập caption (gõ 'ai' để mỗi video có 1 caption AI độc nhất): ").strip()
            if not cap:
                cap = "ai"

            uploader.batch_upload(folder, devices=devices, caption=cap)

        elif choice == "4":
            configure_interactive()
            uploader.ai_generator = AICaptionGenerator()

        elif choice == "0":
            break


if __name__ == "__main__":
    main()
