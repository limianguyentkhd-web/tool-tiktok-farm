# -*- coding: utf-8 -*-
"""
Giao Diện Chính của Phần Mềm (PyQt6 MainWindow)
Hệ Thống Quản Lý Phone Farm TikTok Tự Hành Chuyên Nghiệp.
"""

import os
import sys
import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QTextEdit, QHeaderView, QGroupBox, QComboBox, QCheckBox,
    QMessageBox, QSplitter, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QIcon

from core.config import load_config, save_config
from core.device_manager import DeviceManager
from core.account_manager import AccountProfileManager
from core.self_healing import SelfHealingEngine
from core.ai_vision_agent import VisionAIAgent
from core.telegram_notifier import TelegramNotifier
from core.video_processor import VideoProcessor
from core.autonomous_worker import AutonomousDeviceWorker

class LogSignalEmitter(QObject):
    log_signal = pyqtSignal(str, str) # serial, message
    status_signal = pyqtSignal(str, str) # serial, status

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TikTok Autonomous Farm Studio - Hệ Thống Farm Tự Hành")
        self.resize(1180, 780)

        # Khởi tạo Lõi
        self.config = load_config()
        self.device_mgr = DeviceManager(self.config.get("adb_path"), self.config.get("adb_ports"))
        self.account_mgr = AccountProfileManager()
        self.self_healing = SelfHealingEngine(self.device_mgr)
        self.ai_vision = VisionAIAgent(self.config.get("gemini_api_key"), self.config.get("gemini_model"))
        self.telegram = TelegramNotifier(self.config.get("telegram_bot_token"), self.config.get("telegram_chat_id"))
        self.video_proc = VideoProcessor()

        # Signal Emitter để giao tiếp luồng an toàn với PyQt6
        self.emitter = LogSignalEmitter()
        self.emitter.log_signal.connect(self.append_log)
        self.emitter.status_signal.connect(self.update_device_status_in_table)

        self.workers = {}
        self.running_threads = []

        self.apply_dark_theme()
        self.init_ui()
        self.scan_devices()

    def apply_dark_theme(self):
        dark_qss = """
        QMainWindow, QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QTabWidget::pane {
            border: 1px solid #313244;
            background: #181825;
            border-radius: 8px;
        }
        QTabBar::tab {
            background: #313244;
            color: #a6adc8;
            padding: 8px 16px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QTabBar::tab:selected {
            background: #89b4fa;
            color: #11111b;
            font-weight: bold;
        }
        QGroupBox {
            border: 1px solid #45475a;
            border-radius: 8px;
            margin-top: 14px;
            padding-top: 14px;
            font-weight: bold;
            color: #89b4fa;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QPushButton {
            background-color: #89b4fa;
            color: #11111b;
            border-radius: 6px;
            padding: 7px 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #b4befe;
        }
        QPushButton:pressed {
            background-color: #74c7ec;
        }
        QPushButton#btn_danger {
            background-color: #f38ba8;
            color: #11111b;
        }
        QPushButton#btn_success {
            background-color: #a6e3a1;
            color: #11111b;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 6px;
            color: #cdd6f4;
        }
        QTableWidget {
            background-color: #181825;
            alternate-background-color: #1e1e2e;
            gridline-color: #313244;
            border: 1px solid #313244;
            border-radius: 6px;
        }
        QHeaderView::section {
            background-color: #313244;
            color: #cdd6f4;
            padding: 6px;
            font-weight: bold;
            border: 1px solid #45475a;
        }
        """
        self.setStyleSheet(dark_qss)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Phân chia giữa Các Tab chức năng và Bảng Log bên dưới
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self.create_dashboard_tab(), "📱 Dàn Máy & Điều Khiển")
        tabs.addTab(self.create_profile_tab(), "👤 Kênh Nguồn & Nick TikTok")
        tabs.addTab(self.create_video_tab(), "🎬 Xử Lý Video & Lách Bản Quyền")
        tabs.addTab(self.create_settings_tab(), "⚙️ Mắt Thần AI & Telegram")
        splitter.addWidget(tabs)

        # Log Console
        log_group = QGroupBox("📋 Nhật Ký Hoạt Động Thời Gian Thực (Autonomous Real-time Logs)")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))

        log_btn_layout = QHBoxLayout()
        btn_clear_log = QPushButton("Xóa Log")
        btn_clear_log.setFixedWidth(90)
        btn_clear_log.clicked.connect(self.log_text.clear)
        log_btn_layout.addStretch()
        log_btn_layout.addWidget(btn_clear_log)

        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_btn_layout)
        splitter.addWidget(log_group)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)

    def create_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Thanh công cụ trên cùng
        toolbar = QHBoxLayout()
        btn_scan = QPushButton("🔍 Quét Thiết Bị (ADB Scan)")
        btn_scan.clicked.connect(self.scan_devices)
        
        btn_auto_all = QPushButton("🚀 Bắt Đầu Chạy Tự Động Toàn Dàn")
        btn_auto_all.setObjectName("btn_success")
        btn_auto_all.clicked.connect(self.start_auto_post_all)

        btn_warmup_all = QPushButton("❤️ Nuôi Nick Lướt Dạo (Warmup)")
        btn_warmup_all.clicked.connect(self.start_warmup_all)

        btn_stop = QPushButton("⏹ Dừng Toàn Bộ")
        btn_stop.setObjectName("btn_danger")
        btn_stop.clicked.connect(self.stop_all)

        toolbar.addWidget(btn_scan)
        toolbar.addWidget(btn_auto_all)
        toolbar.addWidget(btn_warmup_all)
        toolbar.addWidget(btn_stop)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Bảng thiết bị
        self.table_devices = QTableWidget()
        self.table_devices.setColumnCount(8)
        self.table_devices.setHorizontalHeaderLabels([
            "Serial Máy", "Tên Box", "Kênh TikTok", "Chủ Đề (Niche)", 
            "Kênh Nguồn Đã Gán", "Đã Đăng", "Pin", "Trạng Thái"
        ])
        self.table_devices.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_devices.setAlternatingRowColors(True)
        self.table_devices.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table_devices)

        return widget

    def create_profile_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        grp = QGroupBox("Gán Kênh Nguồn & Cấu Hình Độc Lập Cho Từng Máy")
        form = QVBoxLayout(grp)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Chọn Máy / Serial:"))
        self.combo_devices = QComboBox()
        self.combo_devices.currentIndexChanged.connect(self.on_select_device_for_profile)
        row1.addWidget(self.combo_devices)
        form.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Kênh TikTok (Username):"))
        self.txt_username = QLineEdit()
        row2.addWidget(self.txt_username)
        row2.addWidget(QLabel("Chủ Đề (Niche):"))
        self.txt_niche = QLineEdit()
        row2.addWidget(self.txt_niche)
        form.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Link Kênh Nguồn (Douyin / Shorts / Reels):"))
        self.txt_source_url = QLineEdit()
        self.txt_source_url.setPlaceholderText("https://www.youtube.com/@channel hoặc link Douyin/Shorts...")
        row3.addWidget(self.txt_source_url)
        form.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Thư Mục Video Riêng:"))
        self.txt_video_folder = QLineEdit()
        self.txt_video_folder.setText("videos")
        row4.addWidget(self.txt_video_folder)
        form.addLayout(row4)

        btn_save_profile = QPushButton("💾 Lưu Hồ Sơ Máy Này")
        btn_save_profile.setObjectName("btn_success")
        btn_save_profile.clicked.connect(self.save_current_profile)
        form.addWidget(btn_save_profile)

        layout.addWidget(grp)
        layout.addStretch()
        return widget

    def create_video_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        grp = QGroupBox("Phòng Xử Lý Video Reup & Lách Bản Quyền (FFmpeg Engine)")
        v_layout = QVBoxLayout(grp)

        row_dl = QHBoxLayout()
        row_dl.addWidget(QLabel("Tải nhanh video từ link:"))
        self.txt_quick_url = QLineEdit()
        self.txt_quick_url.setPlaceholderText("Dán link Douyin / TikTok / Reels / Shorts vào đây...")
        btn_dl = QPushButton("⬇️ Tải Không Logo")
        btn_dl.clicked.connect(self.quick_download_video)
        row_dl.addWidget(self.txt_quick_url)
        row_dl.addWidget(btn_dl)
        v_layout.addLayout(row_dl)

        grp_filters = QGroupBox("Các Bộ Lọc Chống Thuật Toán ByteDance:")
        f_layout = QVBoxLayout(grp_filters)
        self.chk_flip = QCheckBox("Lật gương hình ảnh (Horizontal Flip)")
        self.chk_flip.setChecked(True)
        self.chk_zoom = QCheckBox("Phóng to 1.04x & Cắt viền lệch tâm (Zoom & Crop)")
        self.chk_zoom.setChecked(True)
        self.chk_speed = QCheckBox("Tăng tốc độ ngẫu nhiên 1.03x - 1.05x (Giữ nguyên âm sắc)")
        self.chk_speed.setChecked(True)
        self.chk_color = QCheckBox("Đổi độ tương phản & độ sáng nhẹ (Color Grading)")
        self.chk_color.setChecked(True)
        self.chk_meta = QCheckBox("Xóa sạch Metadata thiết bị gốc & tạo MD5 Hash mới tinh")
        self.chk_meta.setChecked(True)

        f_layout.addWidget(self.chk_flip)
        f_layout.addWidget(self.chk_zoom)
        f_layout.addWidget(self.chk_speed)
        f_layout.addWidget(self.chk_color)
        f_layout.addWidget(self.chk_meta)
        v_layout.addWidget(grp_filters)

        btn_batch_render = QPushButton("🚀 Bắt Đầu Lách Bản Quyền Toàn Bộ Thư Mục raw_videos/")
        btn_batch_render.setObjectName("btn_success")
        btn_batch_render.clicked.connect(self.batch_render_raw_videos)
        v_layout.addWidget(btn_batch_render)

        layout.addWidget(grp)
        layout.addStretch()
        return widget

    def create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Mắt Thần AI
        grp_ai = QGroupBox("🤖 Tầng 2: Mắt Thần AI Cứu Hộ (Gemini Vision API)")
        ai_layout = QVBoxLayout(grp_ai)
        
        row_key = QHBoxLayout()
        row_key.addWidget(QLabel("Gemini API Key:"))
        self.txt_gemini_key = QLineEdit()
        self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_gemini_key.setText(self.config.get("gemini_api_key", ""))
        row_key.addWidget(self.txt_gemini_key)
        ai_layout.addLayout(row_key)

        row_model = QHBoxLayout()
        row_model.addWidget(QLabel("Mô hình AI Vision:"))
        self.combo_ai_model = QComboBox()
        self.combo_ai_model.addItems(["gemini-2.5-flash", "gemini-1.5-flash"])
        self.combo_ai_model.setCurrentText(self.config.get("gemini_model", "gemini-2.5-flash"))
        row_model.addWidget(self.combo_ai_model)
        ai_layout.addLayout(row_model)
        layout.addWidget(grp_ai)

        # Telegram
        grp_tg = QGroupBox("📢 Tầng 3: Báo Cáo Từ Xa Qua Telegram Bot")
        tg_layout = QVBoxLayout(grp_tg)

        row_tg1 = QHBoxLayout()
        row_tg1.addWidget(QLabel("Telegram Bot Token:"))
        self.txt_tg_token = QLineEdit()
        self.txt_tg_token.setText(self.config.get("telegram_bot_token", ""))
        row_tg1.addWidget(self.txt_tg_token)
        tg_layout.addLayout(row_tg1)

        row_tg2 = QHBoxLayout()
        row_tg2.addWidget(QLabel("Telegram Chat ID:"))
        self.txt_tg_chat = QLineEdit()
        self.txt_tg_chat.setText(self.config.get("telegram_chat_id", ""))
        row_tg2.addWidget(self.txt_tg_chat)

        btn_test_tg = QPushButton("📩 Gửi Thử Tin Nhắn")
        btn_test_tg.clicked.connect(self.test_telegram_connection)
        row_tg2.addWidget(btn_test_tg)
        tg_layout.addLayout(row_tg2)
        layout.addWidget(grp_tg)

        # Nút Lưu Toàn Bộ Cấu Hình
        btn_save_cfg = QPushButton("💾 Lưu Cài Đặt Hệ Thống")
        btn_save_cfg.setObjectName("btn_success")
        btn_save_cfg.clicked.connect(self.save_settings)
        layout.addWidget(btn_save_cfg)

        layout.addStretch()
        return widget

    def scan_devices(self):
        """Quét và làm mới danh sách thiết bị trên bảng."""
        self.append_log("SYS", "🔍 Đang quét thiết bị kết nối qua các cổng ADB...")
        devices = self.device_mgr.scan_devices()
        self.table_devices.setRowCount(len(devices))
        self.combo_devices.clear()

        for row, dev in enumerate(devices):
            serial = dev["serial"]
            self.combo_devices.addItem(f"{dev.get('model')} ({serial})", serial)

            # Lấy thông tin tài khoản đã gán
            acc = self.account_mgr.get_by_serial(serial) or {}

            self.table_devices.setItem(row, 0, QTableWidgetItem(serial))
            self.table_devices.setItem(row, 1, QTableWidgetItem(acc.get("box_name", dev["model"])))
            self.table_devices.setItem(row, 2, QTableWidgetItem(acc.get("username", "Chưa gán")))
            self.table_devices.setItem(row, 3, QTableWidgetItem(acc.get("topic", "Chưa gán")))
            self.table_devices.setItem(row, 4, QTableWidgetItem(acc.get("source_channel_url", "Chưa gán")))
            self.table_devices.setItem(row, 5, QTableWidgetItem(str(acc.get("total_posts", 0))))
            self.table_devices.setItem(row, 6, QTableWidgetItem(dev["battery"]))
            self.table_devices.setItem(row, 7, QTableWidgetItem(acc.get("status", "Sẵn sàng")))

        self.append_log("SYS", f"✅ Đã tìm thấy {len(devices)} thiết bị đang hoạt động.")

    def on_select_device_for_profile(self, index: int):
        serial = self.combo_devices.currentData()
        if not serial:
            return
        acc = self.account_mgr.get_by_serial(serial) or {}
        self.txt_username.setText(acc.get("username", ""))
        self.txt_niche.setText(acc.get("topic", ""))
        self.txt_source_url.setText(acc.get("source_channel_url", ""))
        self.txt_video_folder.setText(acc.get("video_folder", "videos"))

    def save_current_profile(self):
        serial = self.combo_devices.currentData()
        if not serial:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một thiết bị trước!")
            return
        profile = {
            "serial": serial,
            "username": self.txt_username.text().strip(),
            "topic": self.txt_niche.text().strip(),
            "source_channel_url": self.txt_source_url.text().strip(),
            "video_folder": self.txt_video_folder.text().strip() or "videos"
        }
        self.account_mgr.upsert_account(profile)
        self.scan_devices()
        QMessageBox.information(self, "Thành công", f"Đã lưu cấu hình hồ sơ cho máy {serial}!")

    def save_settings(self):
        self.config["gemini_api_key"] = self.txt_gemini_key.text().strip()
        self.config["gemini_model"] = self.combo_ai_model.currentText()
        self.config["telegram_bot_token"] = self.txt_tg_token.text().strip()
        self.config["telegram_chat_id"] = self.txt_tg_chat.text().strip()
        save_config(self.config)

        # Cập nhật đối tượng
        self.ai_vision.set_api_key(self.config["gemini_api_key"])
        self.ai_vision.model = self.config["gemini_model"]
        self.telegram.bot_token = self.config["telegram_bot_token"]
        self.telegram.chat_id = self.config["telegram_chat_id"]

        QMessageBox.information(self, "Cài đặt", "Đã lưu cài đặt Mắt Thần AI & Telegram thành công!")

    def test_telegram_connection(self):
        token = self.txt_tg_token.text().strip()
        chat_id = self.txt_tg_chat.text().strip()
        test_tg = TelegramNotifier(token, chat_id)
        if test_tg.send_message("<b>[THÔNG BÁO TEST]</b> Hệ Thống TikTok Farm Studio đã kết nối Telegram thành công!"):
            QMessageBox.information(self, "Telegram", "Đã gửi tin nhắn test thành công tới Telegram của bạn!")
        else:
            QMessageBox.critical(self, "Telegram", "Không thể gửi tin nhắn! Vui lòng kiểm tra lại Bot Token hoặc Chat ID.")

    def quick_download_video(self):
        url = self.txt_quick_url.text().strip()
        if not url:
            return
        self.append_log("VIDEO", f"⬇️ Đang tải video từ link: {url}...")
        def dl():
            res = self.video_proc.download_video(url)
            if res:
                self.emitter.log_signal.emit("VIDEO", f"✅ Tải thành công: {res[0]}")
            else:
                self.emitter.log_signal.emit("VIDEO", "❌ Tải video thất bại.")
        threading.Thread(target=dl, daemon=True).start()

    def batch_render_raw_videos(self):
        self.append_log("VIDEO", "✂️ Bắt đầu quét và lách bản quyền cho toàn bộ thư mục raw_videos/...")
        def process():
            raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw_videos")
            out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "videos")
            files = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.lower().endswith(".mp4")]
            for f in files:
                out_path = os.path.join(out_dir, f"reup_{os.path.basename(f)}")
                self.emitter.log_signal.emit("VIDEO", f"Đang render: {os.path.basename(f)}...")
                if self.video_proc.anti_detect_render(f, out_path, hflip=self.chk_flip.isChecked()):
                    self.emitter.log_signal.emit("VIDEO", f"✅ Xong: {os.path.basename(out_path)}")
                else:
                    self.emitter.log_signal.emit("VIDEO", f"❌ Lỗi: {os.path.basename(f)}")
        threading.Thread(target=process, daemon=True).start()

    def start_auto_post_all(self):
        devices = self.device_mgr.scan_devices()
        if not devices:
            QMessageBox.warning(self, "Thông báo", "Không có thiết bị nào đang kết nối!")
            return

        self.append_log("SYS", f"🚀 Kích hoạt quy trình Đăng Video Tự Hành cho {len(devices)} thiết bị...")
        for dev in devices:
            serial = dev["serial"]
            acc = self.account_mgr.get_by_serial(serial) or {"serial": serial, "box_name": dev["model"]}
            worker = AutonomousDeviceWorker(
                serial=serial,
                account_profile=acc,
                device_mgr=self.device_mgr,
                self_healing=self.self_healing,
                ai_vision=self.ai_vision,
                telegram_notifier=self.telegram,
                video_proc=self.video_proc,
                account_mgr=self.account_mgr,
                log_callback=lambda s, m: self.emitter.log_signal.emit(s, m)
            )
            self.workers[serial] = worker
            t = threading.Thread(target=worker.run_post_cycle, daemon=True)
            self.running_threads.append(t)
            t.start()

    def start_warmup_all(self):
        devices = self.device_mgr.scan_devices()
        if not devices:
            QMessageBox.warning(self, "Thông báo", "Không có thiết bị nào đang kết nối!")
            return

        self.append_log("SYS", f"❤️ Kích hoạt quy trình Nuôi Nick (Warmup) cho {len(devices)} thiết bị...")
        for dev in devices:
            serial = dev["serial"]
            acc = self.account_mgr.get_by_serial(serial) or {"serial": serial, "box_name": dev["model"]}
            worker = AutonomousDeviceWorker(
                serial=serial,
                account_profile=acc,
                device_mgr=self.device_mgr,
                self_healing=self.self_healing,
                ai_vision=self.ai_vision,
                telegram_notifier=self.telegram,
                video_proc=self.video_proc,
                account_mgr=self.account_mgr,
                log_callback=lambda s, m: self.emitter.log_signal.emit(s, m)
            )
            self.workers[serial] = worker
            t = threading.Thread(target=worker.run_warmup, daemon=True)
            self.running_threads.append(t)
            t.start()

    def stop_all(self):
        self.append_log("SYS", "⏹ Đang dừng toàn bộ luồng hoạt động...")
        for worker in self.workers.values():
            worker.stop()
        self.append_log("SYS", "Đã gửi lệnh dừng tới tất cả thiết bị.")

    def append_log(self, serial: str, message: str):
        color = "#cdd6f4"
        if "✅" in message or "thành công" in message.lower() or "🎉" in message:
            color = "#a6e3a1"
        elif "❌" in message or "lỗi" in message.lower() or "cần can thiệp" in message.lower():
            color = "#f38ba8"
        elif "⚠️" in message or "đang" in message.lower():
            color = "#f9e2af"
        elif "🤖" in message:
            color = "#cba6f7"

        formatted = f"<span style='color: #89b4fa;'>[{serial}]</span> <span style='color: {color};'>{message}</span>"
        self.log_text.append(formatted)

    def update_device_status_in_table(self, serial: str, status: str):
        for row in range(self.table_devices.rowCount()):
            item = self.table_devices.item(row, 0)
            if item and item.text() == serial:
                status_item = self.table_devices.item(row, 7)
                if status_item:
                    status_item.setText(status)
                break
