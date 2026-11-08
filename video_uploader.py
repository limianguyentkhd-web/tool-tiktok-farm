"""
Module tự động hóa đẩy video từ máy tính sang Phone Farm và đăng bài lên TikTok (TikTok Video Uploader)
Tích hợp đấu nối API Key AI (Gemini / OpenAI / DeepSeek) để tự động tạo Caption cuốn hút & Hashtag chuẩn SEO.
Phân loại thông minh: Kênh Nuôi (Warmup) vs Kênh Bán Hàng (Affiliate Shop Showcase) & Tự động dọn rác PC.
"""

import base64
import json
import os
import random
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional

from device_manager import DeviceManager
from caption_generator import AICaptionGenerator, configure_interactive

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNEL_TOPICS_PATH = os.path.join(BASE_DIR, "channel_topics.json")
VIDEOS_REGISTRY_PATH = os.path.join(BASE_DIR, "videos_registry.json")


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

    def load_channel_config(self, serial: str) -> Dict:
        """Đọc cấu hình kênh (channel_type, attach_product, product_name) theo serial."""
        if os.path.isfile(CHANNEL_TOPICS_PATH):
            try:
                with open(CHANNEL_TOPICS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(serial, {})
            except Exception as e:
                print(f"[-] Lỗi đọc channel_topics.json: {e}")
        return {}

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

    def attach_tiktok_shop_product(self, serial: str, product_name: str = "") -> bool:
        """
        Kịch bản ADB tự động thêm sản phẩm vào video TikTok (Showcase / Affiliate):
        1. Nhấn nút 'Thêm liên kết' (Add link)
        2. Chọn 'Sản phẩm' (Product)
        3. Chọn sản phẩm chỉ định hoặc sản phẩm đầu tiên trong Showcase
        4. Xác nhận Thêm -> Quay về màn hình Đăng
        """
        print(f"[{serial}] 🛍️ Bắt đầu quy trình gắn sản phẩm TikTok Shop: '{product_name or 'Sản phẩm nổi bật'}'...")

        # 1. Bấm nút 'Thêm liên kết' (Add link)
        # Quét UI tìm text Add link hoặc Thêm liên kết
        self._adb_cmd(serial, ["shell", "uiautomator", "dump", "/data/local/tmp/ui_link.xml"])
        xml_data = self._adb_cmd(serial, ["shell", "cat", "/data/local/tmp/ui_link.xml"]).stdout

        clicked_link = False
        match_link = re.search(r'text="(?:Add link|Thêm liên kết)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_data)
        if match_link:
            x1, y1, x2, y2 = map(int, match_link.groups())
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            self._adb_cmd(serial, ["shell", "input", "tap", str(cx), str(cy)])
            clicked_link = True
        else:
            # Fallback tọa độ hàng Add link
            self._adb_cmd(serial, ["shell", "input", "tap", "540", "930"])
            clicked_link = True

        time.sleep(2.0)

        # 2. Chọn 'Sản phẩm' (Product)
        self._adb_cmd(serial, ["shell", "uiautomator", "dump", "/data/local/tmp/ui_prod.xml"])
        xml_prod = self._adb_cmd(serial, ["shell", "cat", "/data/local/tmp/ui_prod.xml"]).stdout
        match_prod = re.search(r'text="(?:Product|Sản phẩm)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_prod)
        if match_prod:
            x1, y1, x2, y2 = map(int, match_prod.groups())
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            self._adb_cmd(serial, ["shell", "input", "tap", str(cx), str(cy)])
        else:
            # Fallback tọa độ chọn Product trong sheet
            self._adb_cmd(serial, ["shell", "input", "tap", "350", "1550"])

        time.sleep(3.0)

        # 3. Chọn sản phẩm trong Showcase (nút Thêm / Add đầu tiên)
        self._adb_cmd(serial, ["shell", "uiautomator", "dump", "/data/local/tmp/ui_showcase.xml"])
        xml_sc = self._adb_cmd(serial, ["shell", "cat", "/data/local/tmp/ui_showcase.xml"]).stdout
        match_add = re.search(r'text="(?:Add|Thêm)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_sc)
        if match_add:
            x1, y1, x2, y2 = map(int, match_add.groups())
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            self._adb_cmd(serial, ["shell", "input", "tap", str(cx), str(cy)])
        else:
            # Fallback nút Thêm ở item 1
            self._adb_cmd(serial, ["shell", "input", "tap", "940", "750"])

        time.sleep(2.0)

        # 4. Xác nhận tên sản phẩm và hoàn tất gắn liên kết
        self._adb_cmd(serial, ["shell", "input", "tap", "540", "2000"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "input", "tap", "740", "1990"])
        time.sleep(2.0)

        print(f"[{serial}] ✅ Đã gắn liên kết sản phẩm giỏ hàng thành công!")
        return True

    def mark_video_as_posted_and_clean(self, local_video_path: str) -> None:
        """Cập nhật trạng thái 'posted' trong registry và tự động xóa file thành phẩm trên PC."""
        filename = os.path.basename(local_video_path)
        if os.path.isfile(VIDEOS_REGISTRY_PATH):
            try:
                with open(VIDEOS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                    registry = json.load(f)
                updated = False
                for item in registry:
                    if item.get("file_name") == filename or item.get("file_path") == local_video_path:
                        item["status"] = "posted"
                        updated = True
                if updated:
                    with open(VIDEOS_REGISTRY_PATH, "w", encoding="utf-8") as f:
                        json.dump(registry, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        # Xóa file thành phẩm trên PC để dọn rác
        if os.path.isfile(local_video_path):
            try:
                os.remove(local_video_path)
                print(f"[🗑️] [Auto-Clean] Đã tự động xóa file thành phẩm trên PC sau khi đăng: {filename}")
            except Exception as e:
                print(f"[!] Không thể xóa file thành phẩm {filename}: {e}")

    def upload_video(
        self,
        serial: str,
        local_video_path: str,
        caption: str = "auto",
        dismiss_popups: bool = True
    ) -> bool:
        """
        Quy trình trọn gói đăng video:
        1. Kiểm tra cấu hình kênh: Warmup (kênh nuôi) vs Affiliate (kênh bán hàng)
        2. Sinh Caption AI
        3. Đẩy video qua ADB vào điện thoại
        4. Chọn video từ Album TikTok
        5. Nhập Caption tiếng Việt chuẩn
        6. Nếu attach_product=True: Tự động gắn liên kết sản phẩm giỏ hàng
        7. Bấm Đăng (Post)
        8. Tự động xóa file thành phẩm trên PC giải phóng ổ cứng
        """
        # Đọc cấu hình phân loại kênh
        ch_cfg = self.load_channel_config(serial)
        channel_type = ch_cfg.get("channel_type", "warmup")
        attach_product = ch_cfg.get("attach_product", False)
        product_name = ch_cfg.get("product_name", "")

        # Xử lý caption AI
        final_caption = caption
        if not caption or caption.lower() in ["ai", "auto"]:
            base_name = os.path.splitext(os.path.basename(local_video_path))[0]
            clean_topic = base_name.replace("_", " ").replace("-", " ")
            print(f"[{serial}] 🤖 Đang gọi AI API tạo Caption cho chủ đề: '{clean_topic}'...")
            final_caption = self.ai_generator.generate_caption(clean_topic)

        print(f"\n========================================================")
        print(f"🎬 BẮT ĐẦU ĐĂNG VIDEO TRÊN THIẾT BỊ [{serial}]")
        print(f"🏷️  Loại kênh: {channel_type.upper()} | Gắn giỏ hàng: {'CÓ (' + product_name + ')' if attach_product else 'KHÔNG (Kênh nuôi view tự nhiên)'}")
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

        # 3. Làm mới và khởi chạy TikTok
        print(f"[{serial}] 📱 Đang khởi chạy TikTok...")
        self._adb_cmd(serial, ["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(4.0)

        # 4. Nhấn nút '+' (Create)
        print(f"[{serial}] ➕ Bấm nút Tạo video (+)...")
        self._adb_cmd(serial, ["shell", "input", "tap", "540", "2030"])
        time.sleep(2.5)

        # 5. Nhấn nút Upload / Tải lên (Album)
        print(f"[{serial}] 🖼️  Mở thư viện Album (Upload)...")
        self._adb_cmd(serial, ["shell", "input", "tap", "90", "1920"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "input", "tap", "417", "563"])
        time.sleep(2.5)

        # 6. Chọn video mới nhất
        print(f"[{serial}] 🎞️  Chọn video mới nạp...")
        self._adb_cmd(serial, ["shell", "input", "tap", "300", "320"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "input", "tap", "180", "500"])
        time.sleep(1.5)

        # 7. Nhấn nút Tiếp (Next)
        print(f"[{serial}] ➡️  Bấm 'Tiếp' để tải video vào trình chỉnh sửa...")
        self._adb_cmd(serial, ["shell", "input", "tap", "740", "1990"])
        time.sleep(3.5)

        # 8. Màn hình chỉnh sửa: Nhấn Tiếp sang màn hình Đăng bài
        print(f"[{serial}] ➡️  Bấm 'Tiếp' sang màn hình Đăng bài...")
        self._adb_cmd(serial, ["shell", "input", "tap", "740", "1990"])
        time.sleep(1.5)
        self._adb_cmd(serial, ["shell", "input", "tap", "996", "136"])
        time.sleep(3.0)

        # 9. Nhập tiêu đề / mô tả (Caption)
        print(f"[{serial}] ✍️  Đang nhập tiêu đề vào TikTok...")
        self._adb_cmd(serial, ["shell", "input", "tap", "350", "400"])
        time.sleep(1.2)
        self.input_vietnamese_text(serial, final_caption + " ")
        time.sleep(1.5)

        # Rà soát chống mất chữ
        self._adb_cmd(serial, ["shell", "uiautomator", "dump", "/data/local/tmp/cap_check.xml"])
        cap_dump = self._adb_cmd(serial, ["shell", "cat", "/data/local/tmp/cap_check.xml"]).stdout
        if "Add description..." in cap_dump:
            print(f"[{serial}] ⚠️ Chưa nhận con trỏ, đang ép nhận qua nút Hashtags...")
            self._adb_cmd(serial, ["shell", "input", "tap", "160", "690"])
            time.sleep(1.0)
            self.input_vietnamese_text(serial, final_caption + " ")
            time.sleep(1.5)

        # Đóng bàn phím an toàn
        self._adb_cmd(serial, ["shell", "input", "keyevent", "111"])
        time.sleep(1.0)

        # 10. PHÂN LOẠI: NẾU LÀ KÊNH AFFILIATE -> THỰC HIỆN GẮN GIỎ HÀNG SẢN PHẨM
        if attach_product:
            try:
                self.attach_tiktok_shop_product(serial, product_name=product_name)
            except Exception as e:
                print(f"[{serial}] ⚠️ Không thể gắn sản phẩm TikTok Shop ({e}), tiếp tục đăng bài...")
        else:
            print(f"[{serial}] 🌿 Kênh Nuôi Nick (Warmup): Bỏ qua gắn sản phẩm để video phân phối tự nhiên.")

        # 11. Bấm nút ĐĂNG (POST)
        print(f"[{serial}] 🚀 Đang bấm nút ĐĂNG (POST)...")
        self._adb_cmd(serial, ["shell", "input", "tap", "740", "1930"])
        time.sleep(1.0)
        self._adb_cmd(serial, ["shell", "input", "tap", "799", "1999"])
        time.sleep(4.0)

        # 12. Xử lý popup sau đăng
        if dismiss_popups:
            self._adb_cmd(serial, ["shell", "input", "tap", "308", "1950"])
            time.sleep(1.0)
            self._adb_cmd(serial, ["shell", "input", "tap", "355", "1360"])
            time.sleep(1.0)

        print(f"[{serial}] 🎉 ĐÃ HOÀN TẤT ĐĂNG VIDEO THÀNH CÔNG!")

        # 13. TỰ ĐỘNG DỌN RÁC: XÓA FILE THÀNH PHẨM TRÊN PC
        self.mark_video_as_posted_and_clean(local_video_path)

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
        - Phân chia lần lượt mỗi máy 1 video khác nhau.
        - Tự động áp dụng phân loại kênh (warmup / affiliate).
        - Tự động xóa file thành phẩm trên PC sau khi hoàn tất.
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
        print("🎬 TRÌNH ĐĂNG VIDEO TỰ ĐỘNG HÓA TIKTOK FARM 2026")
        print(f"[*] Đang nhận diện {len(devices)} máy (Cổng ADB: {port})")
        print(f"[*] Trạng thái AI Caption: {key_status}")
        print("======================================================")
        print("[1] Đăng 1 video lên 1 máy chỉ định (Tự nhận diện Kênh Nuôi vs Bán Hàng)")
        print("[2] Đăng 1 video lên TOÀN BỘ máy kết nối")
        print("[3] Chia đều thư mục 'ready_to_post' (mỗi máy 1 video, tự dọn rác PC)")
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
            folder = input("Nhập đường dẫn thư mục chứa video (Enter để dùng 'videos/ready_to_post'): ").strip(' "\'')
            if not folder:
                folder = os.path.join(BASE_DIR, "videos", "ready_to_post")
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
