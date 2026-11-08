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

# =========================================================================
# MATRIXFLOW SMART VIDEO ENGINE & APPROVAL DASHBOARD ENDPOINTS
# =========================================================================
READY_TO_POST_DIR = os.path.join(BASE_DIR, "videos", "ready_to_post")
VIDEOS_REGISTRY_PATH = os.path.join(BASE_DIR, "videos_registry.json")
os.makedirs(READY_TO_POST_DIR, exist_ok=True)

def load_video_registry():
    if os.path.exists(VIDEOS_REGISTRY_PATH):
        try:
            with open(VIDEOS_REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_video_registry(videos):
    try:
        with open(VIDEOS_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[-] Lỗi lưu registry video: {e}")

@app.route("/api/videos", methods=["GET"])
def get_videos():
    """Lấy danh sách video sẵn sàng đăng, đồng bộ cùng thư mục ready_to_post/."""
    registry = load_video_registry()
    reg_map = {v.get("file_name"): v for v in registry if isinstance(v, dict)}
    
    # Quét thư mục vật lý nếu có file chưa nằm trong registry
    if os.path.exists(READY_TO_POST_DIR):
        disk_files = [f for f in os.listdir(READY_TO_POST_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
        updated = False
        for f in disk_files:
            if f not in reg_map:
                fpath = os.path.join(READY_TO_POST_DIR, f)
                size_mb = round(os.path.getsize(fpath) / (1024 * 1024), 2)
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(fpath)))
                item = {
                    "id": f"vid_{int(os.path.getmtime(fpath))}",
                    "title": os.path.splitext(f)[0].replace("_", " "),
                    "file_name": f,
                    "file_path": fpath,
                    "preview_url": f"/api/videos/preview/{f}",
                    "render_time": mtime,
                    "duration": 0,
                    "size_mb": size_mb,
                    "voice_used": "N/A",
                    "has_text_overlay": False,
                    "md5_hash": "",
                    "status": "pending_review"
                }
                registry.append(item)
                reg_map[f] = item
                updated = True
        if updated:
            save_video_registry(registry)
            
    return jsonify(registry)

@app.route("/api/videos", methods=["POST"])
def register_rendered_video():
    """Webhook nhận thông báo từ auto_reup_processor.py sau khi render xong."""
    data = request.json or {}
    if not data.get("file_name"):
        return jsonify({"status": "error", "message": "Thiếu file_name"}), 400

    registry = load_video_registry()
    existing_idx = next((i for i, v in enumerate(registry) if v.get("file_name") == data.get("file_name")), None)
    if existing_idx is not None:
        registry[existing_idx].update(data)
    else:
        registry.insert(0, data)
        
    save_video_registry(registry)
    title = data.get("title", data.get("file_name"))
    size = data.get("size_mb", 0)
    add_log("VIDEO", f"🎬 Video mới render xong sẵn sàng duyệt: '{title}' ({size} MB)")
    return jsonify({"status": "ok", "message": "Đã lưu thông tin video thành công"})

@app.route("/api/videos/preview/<path:filename>", methods=["GET"])
def preview_video(filename):
    """Stream xem trước video cho trình duyệt máy tính & điện thoại."""
    target_path = os.path.join(READY_TO_POST_DIR, filename)
    if os.path.isfile(target_path):
        return send_from_directory(READY_TO_POST_DIR, filename, mimetype="video/mp4")
    target_fallback = os.path.join(BASE_DIR, "videos", filename)
    if os.path.isfile(target_fallback):
        return send_from_directory(os.path.join(BASE_DIR, "videos"), filename, mimetype="video/mp4")
    return jsonify({"status": "error", "message": "Không tìm thấy file video"}), 404

@app.route("/api/videos/<video_id>/approve", methods=["POST"])
def approve_video(video_id):
    """Người dùng duyệt video trên điện thoại để sẵn sàng đẩy vào Phone Farm."""
    registry = load_video_registry()
    found = False
    for v in registry:
        if v.get("id") == video_id or v.get("file_name") == video_id:
            v["status"] = "approved"
            found = True
            add_log("APPROVAL", f"✅ Người dùng đã DUYỆT video: '{v.get('title')}'. Sẵn sàng đẩy qua ADB vào Box Phone!")
            break
    if found:
        save_video_registry(registry)
        return jsonify({"status": "ok", "message": "Đã phê duyệt video thành công"})
    return jsonify({"status": "error", "message": "Không tìm thấy video cần duyệt"}), 404

@app.route("/api/videos/<video_id>/reject", methods=["POST"])
def reject_video(video_id):
    """Người dùng loại bỏ video không ưng ý."""
    registry = load_video_registry()
    for v in registry:
        if v.get("id") == video_id or v.get("file_name") == video_id:
            v["status"] = "rejected"
            add_log("APPROVAL", f"❌ Người dùng đã TỪ CHỐI video: '{v.get('title')}'")
            break
    save_video_registry(registry)
    return jsonify({"status": "ok", "message": "Đã loại bỏ video"})

@app.route("/api/videos/process_manual", methods=["POST"])
def trigger_manual_process():
    """Kích hoạt tiến trình render Việt Hóa & Lách Bản Quyền từ Web Dashboard."""
    data = request.json or {}
    url = data.get("url", "").strip()
    script = data.get("script", "").strip()
    voice = data.get("voice", "vi-VN-NamMinhNeural")
    has_text = bool(data.get("has_text_overlay", False))

    def run_bg():
        try:
            from auto_reup_processor import AutoReupProcessor
            proc = AutoReupProcessor()
            video_input = None
            if url:
                add_log("REUP", f"Đang tải video nguồn từ link: {url}...")
                video_input = proc.download_url(url)
            else:
                raw_dir = os.path.join(BASE_DIR, "raw_videos")
                raw_files = [
                    os.path.join(raw_dir, f)
                    for f in os.listdir(raw_dir)
                    if f.lower().endswith((".mp4", ".mov", ".mkv"))
                ]
                if raw_files:
                    video_input = raw_files[0]

            if not video_input or not os.path.isfile(video_input):
                add_log("REUP", "[-] Không tìm thấy video nguồn để xử lý.")
                return

            add_log("REUP", f"🚀 Đang render video: {os.path.basename(video_input)} với giọng {voice}...")
            res = proc.process_video(
                input_path=video_input,
                script_text=script if script else None,
                voice=voice,
                has_text_overlay=has_text,
                hflip=(not has_text),
                pattern_interrupt=True,
                send_webhook=True
            )
            if res:
                add_log("REUP", f"🎉 Đã hoàn tất render! Video thành phẩm: {os.path.basename(res)}")
        except Exception as ex:
            add_log("ERROR", f"Lỗi khi render video từ Web Dashboard: {ex}")

    threading.Thread(target=run_bg, daemon=True).start()
    return jsonify({"status": "ok", "message": "Đã tiếp nhận yêu cầu và bắt đầu xử lý ngầm."})

if __name__ == "__main__":
    add_log("SYS", "TikTok Farm Studio Web Server đã khởi động tại cổng 5000.")
    print("=" * 60)
    print("🌐 TIKTOK FARM STUDIO - WEB INTERFACE")
    print("👉 Mở trình duyệt truy cập: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
