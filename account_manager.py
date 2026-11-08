import os
import sys
import csv
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "danh_sach_tai_khoan_farm.csv")
JSON_FILE = os.path.join(BASE_DIR, "tai_khoan_farm.json")
DB_FILE = os.path.join(BASE_DIR, "farm_database.db")

CSV_HEADERS = [
    "STT",
    "Serial May ADB",
    "Ten May / Vi Tri Box",
    "Kenh TikTok (Username)",
    "Ten Hien Thi (Nickname)",
    "Loai Dang Nhap (Gmail/FB/TikTok)",
    "Email / Tai Khoan Dang Nhap",
    "Mat Khau (Password)",
    "Email Khoi Phuc",
    "Mat Khau Email Khoi Phuc",
    "Ma 2FA",
    "Proxy / IP Rieng",
    "Chu De Kenh (Niche)",
    "Thu Muc Video Gan Rieng",
    "Tong Video Da Dang",
    "Lan Dang Gan Nhat",
    "Tieu De Video Gan Nhat",
    "Link Kenh Nguon Goc Da Lay",
    "Trang Thai Kenh",
    "Ghi Chu"
]

class FarmAccountManager:
    def __init__(self, csv_file: str = CSV_FILE, json_file: str = JSON_FILE):
        self.csv_file = csv_file
        self.json_file = json_file
        self._init_database_table()

    def _init_database_table(self):
        """Khởi tạo bảng quản lý tài khoản trong SQLite nếu chưa có."""
        if not os.path.isfile(DB_FILE):
            return
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS farm_accounts (
                serial TEXT PRIMARY KEY,
                box_name TEXT,
                username TEXT,
                nickname TEXT,
                login_type TEXT,
                login_user TEXT,
                login_pass TEXT,
                recovery_email TEXT,
                recovery_pass TEXT,
                two_fa TEXT,
                proxy TEXT,
                topic TEXT,
                video_folder TEXT,
                total_posts INTEGER DEFAULT 0,
                last_posted_at TEXT,
                last_video_title TEXT,
                last_source_url TEXT,
                status TEXT DEFAULT 'Live',
                note TEXT
            )
            """)
            conn.commit()

    def get_latest_post_for_serial(self, serial: str) -> Dict[str, str]:
        """Tra cứu lịch sử đăng gần nhất của máy trong database."""
        if not os.path.isfile(DB_FILE):
            return {}
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("""
                SELECT * FROM post_history 
                WHERE device_serial = ? AND status = 'SUCCESS'
                ORDER BY id DESC LIMIT 1
                """, (serial,))
                row = cur.fetchone()
                if row:
                    # Đếm tổng số bài đã đăng
                    cur.execute("SELECT COUNT(*) FROM post_history WHERE device_serial = ? AND status = 'SUCCESS'", (serial,))
                    total = cur.fetchone()[0]
                    return {
                        "total_posts": total,
                        "last_posted_at": row["timestamp"],
                        "last_video_title": row["caption"][:50],
                        "last_source_url": row["source_url"] or row["source_channel"]
                    }
        except Exception:
            pass
        return {}

    def scan_and_generate_template(self, active_devices: Optional[List[str]] = None) -> List[dict]:
        """
        Quét toàn bộ danh sách máy đang có và tạo bảng dữ liệu chuẩn:
        - Điền đầy đủ thông tin máy mẫu đã đăng bài
        - Để trống mật khẩu, email cho các máy còn lại để người dùng tự điền bổ sung
        """
        if active_devices is None:
            # Lấy thiết bị qua ADB
            import subprocess
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, errors="replace")
            active_devices = [
                line.split()[0]
                for line in res.stdout.strip().splitlines()[1:]
                if line.strip() and "\tdevice" in line
            ]

        # Đọc dữ liệu cũ nếu đã tồn tại để không ghi đè mất mật khẩu người dùng đã gõ
        existing_data = {}
        if os.path.isfile(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    old_list = json.load(f)
                    for item in old_list:
                        existing_data[item.get("serial")] = item
            except Exception:
                pass

        accounts = []
        for idx, serial in enumerate(active_devices, 1):
            old = existing_data.get(serial, {})
            hist = self.get_latest_post_for_serial(serial)

            # Máy mẫu đã chạy test live
            if serial == "ce031713dba2c72101":
                acc = {
                    "stt": idx,
                    "serial": serial,
                    "box_name": old.get("box_name") or f"May_{idx:02d} (SM-G998B)",
                    "username": old.get("username") or "@nguyennminhh256",
                    "nickname": old.get("nickname") or "_ngminh",
                    "login_type": old.get("login_type") or "Gmail Cu",
                    "login_user": old.get("login_user") or "",
                    "login_pass": old.get("login_pass") or "",
                    "recovery_email": old.get("recovery_email") or "",
                    "recovery_pass": old.get("recovery_pass") or "",
                    "two_fa": old.get("two_fa") or "",
                    "proxy": old.get("proxy") or "",
                    "topic": old.get("topic") or "Review Phim / Marvel",
                    "video_folder": old.get("video_folder") or "videos/phim",
                    "total_posts": hist.get("total_posts", 2),
                    "last_posted_at": hist.get("last_posted_at", "2026-10-30 00:22:12"),
                    "last_video_title": hist.get("last_video_title", "Tại sao Stormbreaker lại có ý thức tự chủ?"),
                    "last_source_url": hist.get("last_source_url", "https://www.youtube.com/shorts/qk3pEXQ43aA (@zim_video)"),
                    "status": old.get("status") or "Live (Da Dang Bai)",
                    "note": old.get("note") or "May mau chay rat muot"
                }
            else:
                acc = {
                    "stt": idx,
                    "serial": serial,
                    "box_name": old.get("box_name") or f"May_{idx:02d} (SM-G998B)",
                    "username": old.get("username") or f"@kenh_farm_{idx:02d}",
                    "nickname": old.get("nickname") or f"User_{idx:02d}",
                    "login_type": old.get("login_type") or "Gmail Cu",
                    "login_user": old.get("login_user") or "",
                    "login_pass": old.get("login_pass") or "",
                    "recovery_email": old.get("recovery_email") or "",
                    "recovery_pass": old.get("recovery_pass") or "",
                    "two_fa": old.get("two_fa") or "",
                    "proxy": old.get("proxy") or "",
                    "topic": old.get("topic") or ("Thoi Trang" if idx % 2 == 0 else "Gia Dung"),
                    "video_folder": old.get("video_folder") or ("videos/thoi_trang" if idx % 2 == 0 else "videos/gia_dung"),
                    "total_posts": hist.get("total_posts", 0),
                    "last_posted_at": hist.get("last_posted_at", ""),
                    "last_video_title": hist.get("last_video_title", ""),
                    "last_source_url": hist.get("last_source_url", ""),
                    "status": old.get("status") or "San sang / Cho nuoi",
                    "note": old.get("note") or ""
                }
            accounts.append(acc)

        # Lưu ra JSON
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)

        # Lưu ra CSV / Excel (UTF-8-SIG mở Excel trên Windows không lỗi font)
        with open(self.csv_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            for a in accounts:
                writer.writerow([
                    a["stt"],
                    a["serial"],
                    a["box_name"],
                    a["username"],
                    a["nickname"],
                    a["login_type"],
                    a["login_user"],
                    a["login_pass"],
                    a["recovery_email"],
                    a["recovery_pass"],
                    a["two_fa"],
                    a["proxy"],
                    a["topic"],
                    a["video_folder"],
                    a["total_posts"],
                    a["last_posted_at"],
                    a["last_video_title"],
                    a["last_source_url"],
                    a["status"],
                    a["note"]
                ])

        print(f"[+] ✅ Đã tạo / cập nhật Danh Sách Tài Khoản Farm ({len(accounts)} máy) thành công!")
        print(f"📁 File Excel: {self.csv_file}")
        print(f"📄 File JSON: {self.json_file}")
        return accounts

    def print_summary(self):
        """In tóm tắt bảng tài khoản ra màn hình console."""
        if not os.path.isfile(self.csv_file):
            self.scan_and_generate_template()

        with open(self.csv_file, "r", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))
            rows = reader[1:]

        print("\n" + "="*85)
        print("📋 DANH SÁCH QUẢN LÝ TÀI KHOẢN PHONE FARM TIKTOK")
        print("="*85)
        for r in rows:
            print(f"[{r[0]:>2}] Máy: {r[2]} ({r[1]})")
            print(f"     Kênh: {r[3]} ({r[4]}) | Loại: {r[5]} | Chủ đề: {r[12]}")
            print(f"     Đã đăng: {r[14]} video | Lần cuối: {r[15] or 'Chưa đăng'} | Nguồn: {r[17] or 'Chưa có'}")
            print(f"     Trạng thái: {r[18]}")
            print("-" * 85)


if __name__ == '__main__':
    mgr = FarmAccountManager()
    mgr.scan_and_generate_template()
    mgr.print_summary()
    print("\n👉 Bạn có thể mở trực tiếp file 'danh_sach_tai_khoan_farm.csv' bằng Excel để bổ sung mật khẩu bất cứ lúc nào!")
