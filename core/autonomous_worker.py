# -*- coding: utf-8 -*-
"""
Module Luồng Thực Thi Tự Hành (Autonomous Device Worker)
Chạy độc lập cho từng máy: Nuôi nick hoặc Đăng bài, tự phục hồi lỗi và báo cáo Telegram.
"""

import os
import time
import random
import traceback
from typing import Callable, Optional, Dict
from .device_manager import DeviceManager
from .self_healing import SelfHealingEngine
from .ai_vision_agent import VisionAIAgent
from .telegram_notifier import TelegramNotifier
from .video_processor import VideoProcessor
from .account_manager import AccountProfileManager

class AutonomousDeviceWorker:
    def __init__(
        self,
        serial: str,
        account_profile: Dict,
        device_mgr: DeviceManager,
        self_healing: SelfHealingEngine,
        ai_vision: VisionAIAgent,
        telegram_notifier: TelegramNotifier,
        video_proc: VideoProcessor,
        account_mgr: AccountProfileManager,
        log_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.serial = serial
        self.profile = account_profile
        self.dm = device_mgr
        self.sh = self_healing
        self.ai = ai_vision
        self.tg = telegram_notifier
        self.vp = video_proc
        self.am = account_mgr
        self.log_callback = log_callback or (lambda s, m: print(f"[{s}] {m}"))
        self._stop_flag = False

    def log(self, message: str):
        self.log_callback(self.serial, message)

    def stop(self):
        self._stop_flag = True

    def run_warmup(self, duration_minutes: int = 15):
        """Kịch bản nuôi nick: Lướt video dạo như người thật, thả tim, ngắm comment."""
        self.log(f" Bắt đầu nuôi nick ({duration_minutes} phút)...")
        self.am.update_status(self.serial, "Đang nuôi nick")
        
        # Mở khóa màn hình
        self.dm.run_adb(self.serial, ["shell", "input", "keyevent", "224"])
        self.dm.run_adb(self.serial, ["shell", "input", "keyevent", "82"])
        
        # Bật TikTok
        self.dm.force_stop(self.serial, "com.zhiliaoapp.musically")
        time.sleep(1)
        self.dm.run_adb(self.serial, ["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(5)
        
        # Dập tắt popup đầu game
        self.sh.auto_dismiss_popups(self.serial)

        start_time = time.time()
        max_duration = duration_minutes * 60
        w, h = self.dm.get_screen_size(self.serial)

        while time.time() - start_time < max_duration and not self._stop_flag:
            # Xem video từ 6 đến 18 giây
            watch_time = random.uniform(6.0, 18.0)
            time.sleep(watch_time)

            # Tỷ lệ 20% thả tim (Double tap vào giữa màn hình)
            if random.random() < 0.20:
                self.log("❤️ Thả tim video...")
                cx, cy = w // 2, h // 2
                self.dm.tap(self.serial, cx, cy)
                time.sleep(0.1)
                self.dm.tap(self.serial, cx, cy)
                time.sleep(1.0)

            # Tự động dập popup nếu có hiện
            self.sh.auto_dismiss_popups(self.serial)

            # Vuốt sang video tiếp theo (mô phỏng ngón tay người vuốt từ dưới lên)
            sx = random.randint(int(w * 0.4), int(w * 0.6))
            sy = random.randint(int(h * 0.75), int(h * 0.85))
            ey = random.randint(int(h * 0.15), int(h * 0.25))
            self.dm.human_swipe(self.serial, sx, sy, sx, ey)

        self.log(" Hoàn tất ca nuôi nick.")
        self.am.update_status(self.serial, "Sẵn sàng")

    def run_post_cycle(self) -> bool:
        """
        Quy trình tự hành trọn gói:
        1. Kiểm tra kho video riêng của máy. Nếu hết, tự cào từ kênh nguồn của máy đó.
        2. Lách bản quyền bằng FFmpeg.
        3. Đẩy vào máy & Đăng lên TikTok.
        4. Tự phục hồi khi gặp sự cố hoặc gọi Mắt Thần AI.
        5. Báo cáo Telegram.
        """
        self.log("🚀 Bắt đầu quy trình tự hành Đăng Video...")
        self.am.update_status(self.serial, "Đang xử lý video")

        w, h = self.dm.get_screen_size(self.serial)
        folder = self.profile.get("video_folder", "videos")
        source_url = self.profile.get("source_channel_url", "")
        niche = self.profile.get("topic", "Tổng hợp")
        os.makedirs(folder, exist_ok=True)

        # 1. Tìm video sẵn có trong folder
        ready_videos = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.lower().endswith(".mp4") and not f.startswith("raw_")
        ]

        target_video = ""
        video_title = ""

        if ready_videos:
            target_video = ready_videos[0]
            video_title = os.path.splitext(os.path.basename(target_video))[0].replace("_", " ")
            self.log(f"📦 Tìm thấy video sẵn có trong kho: {os.path.basename(target_video)}")
        elif source_url:
            self.log(f"🌐 Kho hết video, đang cào video từ kênh nguồn gán riêng: {source_url}...")
            dl_res = self.vp.download_video(source_url)
            if dl_res:
                raw_path, raw_title = dl_res
                video_title = raw_title or f"Video {niche}"
                out_path = os.path.join(folder, f"reup_{int(time.time())}.mp4")
                self.log("✂️ Đang áp dụng bộ lọc lách bản quyền (Anti-detection)...")
                if self.vp.anti_detect_render(raw_path, out_path, hflip=True):
                    target_video = out_path
                    self.log("✅ Lách bản quyền thành công!")
                else:
                    self.log("❌ Lỗi render FFmpeg.")
                    return False
            else:
                self.log(f"❌ Không tải được video từ link nguồn: {source_url}")
                return False
        else:
            self.log("⚠️ Không có video trong kho và chưa cài đặt link kênh nguồn cho nick này.")
            self.am.update_status(self.serial, "Thiếu video")
            return False

        # 2. Đẩy video sang điện thoại
        self.am.update_status(self.serial, "Đang nạp video vào máy")
        remote_filename = f"vid_{int(time.time())}.mp4"
        remote_path = f"/sdcard/DCIM/Camera/{remote_filename}"
        self.log(f"📲 Đang nạp video sang thư mục Camera: {remote_path}...")
        if not self.dm.push_file(self.serial, target_video, remote_path):
            self.log("❌ Lỗi push file sang điện thoại!")
            return False

        self.dm.trigger_media_scan(self.serial, remote_path)
        time.sleep(2)

        # 3. Đánh thức màn hình và mở TikTok
        self.am.update_status(self.serial, "Đang mở TikTok")
        self.dm.run_adb(self.serial, ["shell", "input", "keyevent", "224"])
        self.dm.run_adb(self.serial, ["shell", "input", "keyevent", "82"])
        self.dm.force_stop(self.serial, "com.zhiliaoapp.musically")
        time.sleep(1.0)
        self.dm.run_adb(self.serial, ["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
        time.sleep(4.5)

        # Dập tắt popup đầu
        self.sh.auto_dismiss_popups(self.serial)

        # 4. Thao tác đăng video (với cơ chế AI cứu hộ khi kẹt)
        try:
            self.log("➕ Bấm nút Tạo video (+)...")
            self.dm.tap(self.serial, int(w * 0.5), int(h * 0.85))
            time.sleep(2.5)
            self._handle_possible_stuck("Vừa bấm dấu cộng tạo video")

            self.log("🖼️ Mở thư viện Album (Upload)...")
            self.dm.tap(self.serial, int(w * 0.15), int(h * 0.82))
            time.sleep(2.0)
            self._handle_possible_stuck("Vừa bấm mở Album")

            self.log("🎞️ Chọn video mới nhất...")
            self.dm.tap(self.serial, int(w * 0.3), int(h * 0.18))
            time.sleep(1.5)

            self.log("➡️ Bấm 'Tiếp' để vào trình chỉnh sửa...")
            self.dm.tap(self.serial, int(w * 0.75), int(h * 0.85))
            time.sleep(3.5)
            self._handle_possible_stuck("Đang ở màn hình chỉnh sửa")

            self.log("➡️ Bấm 'Tiếp' sang màn hình Đăng bài...")
            self.dm.tap(self.serial, int(w * 0.75), int(h * 0.85))
            time.sleep(3.0)
            self._handle_possible_stuck("Đang ở màn hình soạn thảo bài đăng")

            # Nhập Caption
            self.log(f"✍️ Đang nhập tiêu đề: {video_title[:35]}...")
            self.dm.tap(self.serial, int(w * 0.35), int(h * 0.2))
            time.sleep(1.0)

            # Sử dụng adb shell input text hoặc adb keyboard
            clean_cap = video_title.replace('"', '').replace("'", "") + " #" + niche.replace(" ", "")
            self.dm.run_adb(self.serial, ["shell", "input", "text", f'"{clean_cap}"'])
            time.sleep(1.5)
            
            # Đóng bàn phím
            self.dm.run_adb(self.serial, ["shell", "input", "keyevent", "111"])
            time.sleep(1.0)

            # Bấm ĐĂNG
            self.log("🚀 Bấm nút ĐĂNG (POST)...")
            self.dm.tap(self.serial, int(w * 0.75), int(h * 0.83))
            time.sleep(4.0)

            # Xử lý dập tắt các popup mời chia sẻ sau đăng
            self.sh.auto_dismiss_popups(self.serial)
            time.sleep(2.0)

            # Cập nhật thành công vào cơ sở dữ liệu
            self.am.update_post_success(self.serial, video_title, source_url)
            self.log(f"🎉 ĐĂNG THÀNH CÔNG VIDEO: {video_title}!")

            # Báo cáo Telegram
            if self.tg.is_configured():
                screen_cap = os.path.join("logs", f"success_{self.serial}.png")
                if self.dm.take_screenshot(self.serial, screen_cap):
                    caption = (
                        f"✅ <b>[MÁY {self.profile.get('box_name', self.serial)}] ĐĂNG BÀI THÀNH CÔNG!</b>\n"
                        f"👤 Kênh: <code>{self.profile.get('username')}</code>\n"
                        f"🎬 Tiêu đề: {video_title}\n"
                        f"📁 Chủ đề: {niche}\n"
                        f"📊 Tổng video đã đăng: {self.profile.get('total_posts', 1)}"
                    )
                    self.tg.send_photo(screen_cap, caption)

            # Xóa file video đã đăng khỏi máy tính để lần sau lấy video mới
            try:
                os.remove(target_video)
            except Exception:
                pass

            return True

        except Exception as e:
            self.log(f"❌ Lỗi ngoại lệ trong quá trình đăng: {e}")
            self._handle_critical_error(str(e))
            return False

    def _handle_possible_stuck(self, current_step: str):
        """Cơ chế Tầng 1 dập popup, nếu thất bại kích hoạt Tầng 2 AI Vision."""
        if self.sh.auto_dismiss_popups(self.serial):
            time.sleep(1.0)
            return

        # Nếu AI Vision được cấu hình, kiểm tra xem màn hình có đang bị kẹt không
        if self.ai.is_configured():
            shot_path = os.path.join("logs", f"ai_check_{self.serial}.png")
            if self.dm.take_screenshot(self.serial, shot_path):
                w, h = self.dm.get_screen_size(self.serial)
                analysis = self.ai.analyze_screen(shot_path, w, h, current_goal=current_step)
                if analysis.get("is_stuck") and analysis.get("action") == "click":
                    px = analysis.get("pixel_x")
                    py = analysis.get("pixel_y")
                    self.log(f"🤖 [Mắt Thần AI] Phát hiện kẹt: '{analysis.get('issue')}'. Đang tự giải cứu bấm vào ({px}, {py})...")
                    self.dm.tap(self.serial, px, py)
                    time.sleep(1.5)

    def _handle_critical_error(self, err_msg: str):
        """Cơ chế Tầng 3: Chụp ảnh gửi Telegram báo cho người dùng mà không làm sập tool."""
        self.am.update_status(self.serial, "Cần can thiệp", note=err_msg[:50])
        shot_path = os.path.join("logs", f"alert_{self.serial}.png")
        if self.dm.take_screenshot(self.serial, shot_path):
            if self.tg.is_configured():
                alert_text = (
                    f"⚠️ <b>[CẢNH BÁO MÁY {self.profile.get('box_name', self.serial)}] CẦN CAN THIỆP!</b>\n"
                    f"👤 Kênh: <code>{self.profile.get('username')}</code>\n"
                    f"❌ Sự cố: {err_msg}\n"
                    f"ℹ️ Tool đã tạm dừng máy này để bạn xử lý, các máy khác vẫn hoạt động bình thường."
                )
                self.tg.send_photo(shot_path, alert_text)
