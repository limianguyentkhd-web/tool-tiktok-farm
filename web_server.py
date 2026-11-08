# -*- coding: utf-8 -*-
"""
Máy Chủ Giao Diện Web (Web Dashboard Server) cho TikTok Farm Studio
Khởi chạy dịch vụ Web UI để quản lý dàn Phone Farm từ mọi trình duyệt máy tính, điện thoại qua LAN/WAN.
"""

import os
import sys
import json
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory

# Đảm bảo đường dẫn gốc nằm trong sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import load_config, save_config
from core.device_manager import DeviceManager
from core.account_manager import AccountProfileManager
from core.self_healing import SelfHealingEngine
from core.ai_vision_agent import VisionAIAgent
from core.telegram_notifier import TelegramNotifier
from core.video_processor import VideoProcessor
from core.autonomous_worker import AutonomousDeviceWorker

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

# Khởi tạo lõi quản lý
config = load_config()
device_mgr = DeviceManager(config.get("adb_path"), config.get("adb_ports"))
account_mgr = AccountProfileManager()
self_healing = SelfHealingEngine(device_mgr)
ai_vision = VisionAIAgent(config.get("gemini_api_key"), config.get("gemini_model"))
telegram = TelegramNotifier(config.get("telegram_bot_token"), config.get("telegram_chat_id"))
video_proc = VideoProcessor()

# Bộ đệm log thời gian thực
logs_buffer = []
workers = {}
running_threads = []

def add_log(tag: str, msg: str):
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "tag": tag, "msg": str(msg)}
    logs_buffer.append(entry)
    if len(logs_buffer) > 200:
        logs_buffer.pop(0)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Lấy danh sách thiết bị kèm thông tin hồ sơ tài khoản."""
    devices = device_mgr.scan_devices()
    result = []
    
    # Nếu chưa cắm máy thật, trả về danh sách hồ sơ từ file để hiển thị đầy đủ
    if not devices:
        for acc in account_mgr.accounts:
            result.append({
                "serial": acc.get("serial", "N/A"),
                "box_name": acc.get("box_name", "Thiết Bị Farm"),
                "username": acc.get("username", "Chưa gán"),
                "topic": acc.get("topic") or acc.get("niche", "Chưa gán"),
                "source_channel_url": acc.get("source_channel_url", ""),
                "video_folder": acc.get("video_folder", "videos"),
                "total_posts": acc.get("total_posts", acc.get("total_posted", 0)),
                "battery": "100%",
                "status": acc.get("status", "Sẵn sàng (Offline)")
            })
        return jsonify(result)

    for dev in devices:
        serial = dev["serial"]
        acc = account_mgr.get_by_serial(serial) or {}
        result.append({
            "serial": serial,
            "box_name": acc.get("box_name", dev["model"]),
            "username": acc.get("username", "Chưa gán"),
            "topic": acc.get("topic") or acc.get("niche", "Chưa gán"),
            "source_channel_url": acc.get("source_channel_url", ""),
            "video_folder": acc.get("video_folder", "videos"),
            "total_posts": acc.get("total_posts", acc.get("total_posted", 0)),
            "battery": dev["battery"],
            "status": acc.get("status", "Sẵn sàng (Online)")
        })
    return jsonify(result)

@app.route("/api/profiles", methods=["GET"])
def get_profiles():
    return jsonify(account_mgr.accounts)

@app.route("/api/profiles/save", methods=["POST"])
def save_profile():
    data = request.json or {}
    serial = data.get("serial")
    if not serial:
        return jsonify({"status": "error", "message": "Thiếu serial thiết bị"}), 400
    
    account_mgr.upsert_account(data)
    add_log("PROFILE", f"Đã lưu hồ sơ mới cho máy {serial}: {data.get('username')}")
    return jsonify({"status": "ok", "message": "Đã lưu hồ sơ thành công"})

@app.route("/api/config", methods=["GET", "POST"])
def handle_config():
    global config
    if request.method == "POST":
        new_cfg = request.json or {}
        config.update(new_cfg)
        save_config(config)
        add_log("SYS", "Đã cập nhật cấu hình hệ thống config.json")
        return jsonify({"status": "ok"})
    return jsonify(config)

@app.route("/api/action/start_all", methods=["POST"])
def start_auto_post_all():
    devices = device_mgr.scan_devices()
    if not devices:
        add_log("WARN", "Không tìm thấy thiết bị kết nối qua ADB! Đang chạy mô phỏng.")
        return jsonify({"status": "warn", "message": "Không có máy thật kết nối, vui lòng kiểm tra cổng ADB"})

    add_log("SYS", f"🚀 Kích hoạt quy trình Đăng Video Tự Hành cho {len(devices)} thiết bị...")
    for dev in devices:
        serial = dev["serial"]
        acc = account_mgr.get_by_serial(serial) or {"serial": serial, "box_name": dev["model"]}
        worker = AutonomousDeviceWorker(
            serial=serial,
            account_profile=acc,
            device_mgr=device_mgr,
            self_healing=self_healing,
            ai_vision=ai_vision,
            telegram_notifier=telegram,
            video_proc=video_proc,
            account_mgr=account_mgr,
            log_callback=lambda s, m: add_log(s[-6:], m)
        )
        workers[serial] = worker
        t = threading.Thread(target=worker.run_post_cycle, daemon=True)
        running_threads.append(t)
        t.start()

    return jsonify({"status": "ok", "message": f"Đã kích hoạt {len(devices)} luồng tự hành."})

@app.route("/api/action/warmup_all", methods=["POST"])
def start_warmup_all():
    devices = device_mgr.scan_devices()
    if not devices:
        return jsonify({"status": "warn", "message": "Không có máy thật kết nối"})

    add_log("WARMUP", f"❤️ Kích hoạt nuôi nick cho {len(devices)} thiết bị...")
    for dev in devices:
        serial = dev["serial"]
        acc = account_mgr.get_by_serial(serial) or {"serial": serial}
        worker = AutonomousDeviceWorker(
            serial=serial,
            account_profile=acc,
            device_mgr=device_mgr,
            self_healing=self_healing,
            ai_vision=ai_vision,
            telegram_notifier=telegram,
            video_proc=video_proc,
            account_mgr=account_mgr,
            log_callback=lambda s, m: add_log(s[-6:], m)
        )
        workers[serial] = worker
        t = threading.Thread(target=lambda: worker.run_warmup(15), daemon=True)
        running_threads.append(t)
        t.start()

    return jsonify({"status": "ok", "message": "Đã bắt đầu chu trình nuôi nick."})

@app.route("/api/action/stop_all", methods=["POST"])
def stop_all():
    for w in workers.values():
        w.stop()
    workers.clear()
    add_log("SYS", "⏹ Đã gửi tín hiệu dừng tới toàn bộ Worker.")
    return jsonify({"status": "ok", "message": "Đã dừng toàn bộ"})

@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(logs_buffer)

@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    logs_buffer.clear()
    return jsonify({"status": "ok"})

@app.route("/api/telegram/test", methods=["POST"])
def test_telegram():
    data = request.json or {}
    token = data.get("bot_token") or config.get("telegram_bot_token")
    chat_id = data.get("chat_id") or config.get("telegram_chat_id")
    test_tg = TelegramNotifier(token, chat_id)
    success = test_tg.send_message("<b>[THÔNG BÁO WEB]</b> TikTok Farm Studio Web UI đã kết nối thành công!")
    if success:
        add_log("TELEGRAM", "Gửi tin nhắn thử nghiệm thành công tới Telegram!")
        return jsonify({"status": "ok", "message": "Gửi tin nhắn Telegram thành công"})
    return jsonify({"status": "error", "message": "Gửi tin nhắn thất bại, hãy kiểm tra lại Bot Token và Chat ID"}), 400

if __name__ == "__main__":
    add_log("SYS", "TikTok Farm Studio Web Server đã khởi động tại cổng 5000.")
    print("=" * 60)
    print("🌐 TIKTOK FARM STUDIO - WEB INTERFACE")
    print("👉 Mở trình duyệt truy cập: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
