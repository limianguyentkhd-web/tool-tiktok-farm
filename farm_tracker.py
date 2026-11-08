import os
import sys
import sqlite3
import csv
from datetime import datetime
from typing import Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r"d:\TOOL TIKTOK\farm_database.db"
CSV_PATH = r"d:\TOOL TIKTOK\lich_su_dang_bai.csv"

class FarmTracker:
    def __init__(self, db_path: str = DB_PATH, csv_path: str = CSV_PATH):
        self.db_path = db_path
        self.csv_path = csv_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Khởi tạo cấu trúc cơ sở dữ liệu quản lý hàng trăm kênh Phone Farm."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            # Bảng 1: Quản lý nguồn video tải về (Nguồn link, kênh gốc)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS video_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT UNIQUE,
                source_url TEXT,
                source_channel TEXT,
                video_title TEXT,
                downloaded_at TEXT
            )
            """)

            # Bảng 2: Quản lý chi tiết từng lượt đăng lên từng máy / tài khoản
            cur.execute("""
            CREATE TABLE IF NOT EXISTS post_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_serial TEXT,
                tiktok_account TEXT,
                topic TEXT,
                video_file TEXT,
                source_url TEXT,
                source_channel TEXT,
                caption TEXT,
                status TEXT
            )
            """)
            conn.commit()

    def record_download(self, file_name: str, source_url: str, source_channel: str = "", video_title: str = ""):
        """Ghi nhận video vừa tải về máy tính và link nguồn gốc."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO video_sources (file_name, source_url, source_channel, video_title, downloaded_at)
            VALUES (?, ?, ?, ?, ?)
            """, (file_name, source_url, source_channel, video_title, now))
            conn.commit()

    def get_source_info(self, file_name: str) -> Dict[str, str]:
        """Truy xuất link nguồn gốc từ tên file video."""
        base = os.path.basename(file_name)
        # Loại bỏ các prefix reup như ready_1_, reup_1793_
        clean_name = base
        for prefix in ["ready_1_", "ready_2_", "ready_3_", "ready_4_", "ready_5_"]:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):]

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM video_sources WHERE file_name LIKE ?", (f"%{clean_name[:25]}%",))
            row = cur.fetchone()
            if row:
                return {
                    "source_url": row["source_url"],
                    "source_channel": row["source_channel"],
                    "video_title": row["video_title"]
                }
        return {"source_url": "", "source_channel": "", "video_title": ""}

    def record_post(
        self,
        device_serial: str,
        tiktok_account: str,
        video_file: str,
        caption: str,
        topic: str = "chung",
        source_url: str = "",
        source_channel: str = "",
        status: str = "SUCCESS"
    ):
        """
        Ghi lại lịch sử đăng bài chi tiết:
        Máy nào -> Kênh nào -> Đăng video gì -> Lấy từ link kênh gốc nào -> Vào mấy giờ.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Nếu chưa truyền source_url, tự động tra cứu từ database nguồn tải
        if not source_url:
            src = self.get_source_info(video_file)
            source_url = src.get("source_url", "")
            source_channel = src.get("source_channel", "")

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO post_history (
                timestamp, device_serial, tiktok_account, topic, video_file, source_url, source_channel, caption, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, device_serial, tiktok_account, topic, os.path.basename(video_file), source_url, source_channel, caption, status))
            conn.commit()

        # Đồng bộ ra file CSV để người dùng mở bằng Excel xem trực tiếp
        self.export_to_csv()

    def is_video_already_handled(self, source_url_or_id: str) -> bool:
        """
        Cơ chế tự động rà soát chống trùng lặp:
        Kiểm tra xem link hoặc Video ID này đã từng được TẢI hoặc ĐĂNG chưa.
        Kiểm tra trên cả Database lẫn Thư mục ổ cứng (raw_videos, videos).
        """
        clean_id = source_url_or_id.strip()
        if not clean_id:
            return False

        # 1. Kiểm tra trong Cơ sở dữ liệu SQLite
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT id FROM video_sources 
            WHERE source_url LIKE ? OR file_name LIKE ?
            """, (f"%{clean_id}%", f"%{clean_id}%"))
            if cur.fetchone() is not None:
                return True
            
            cur.execute("""
            SELECT id FROM post_history
            WHERE source_url LIKE ? OR video_file LIKE ?
            """, (f"%{clean_id}%", f"%{clean_id}%"))
            if cur.fetchone() is not None:
                return True

        # 2. Kiểm tra trực tiếp trên ổ đĩa (raw_videos và videos)
        import glob
        base_dir = os.path.dirname(os.path.abspath(__file__))
        raw_matches = glob.glob(os.path.join(base_dir, "raw_videos", f"*{clean_id}*"))
        if raw_matches:
            return True
        ready_matches = glob.glob(os.path.join(base_dir, "videos", f"*{clean_id}*"))
        if ready_matches:
            return True

        return False

    def export_to_csv(self):
        """Xuất toàn bộ lịch sử đăng bài ra file CSV/Excel thân thiện."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM post_history ORDER BY id DESC")
            rows = cur.fetchall()

        fieldnames = [
            "ID", "Thời Gian Đăng", "Serial Máy", "Kênh TikTok", "Chủ Đề",
            "Tên File Video", "Link Nguồn Gốc", "Kênh Nguồn Gốc", "Caption Đã Đăng", "Trạng Thái"
        ]

        with open(self.csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            for r in rows:
                writer.writerow([
                    r["id"], r["timestamp"], r["device_serial"], r["tiktok_account"],
                    r["topic"], r["video_file"], r["source_url"], r["source_channel"],
                    r["caption"], r["status"]
                ])

    def has_posted(self, tiktok_account: str, source_url_or_file: str) -> bool:
        """Kiểm tra xem tài khoản này đã từng đăng video từ link này chưa (chống trùng bài)."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT id FROM post_history 
            WHERE tiktok_account = ? AND (source_url = ? OR video_file LIKE ?) AND status = 'SUCCESS'
            """, (tiktok_account, source_url_or_file, f"%{os.path.basename(source_url_or_file)}%"))
            return cur.fetchone() is not None

    def print_recent_logs(self, limit: int = 10):
        """In bảng báo cáo lịch sử đăng bài gần nhất ra màn hình console."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM post_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cur.fetchall()

        print("\n" + "="*85)
        print("📊 NHẬT KÝ LỊCH SỬ ĐĂNG BÀI TOÀN HỆ THỐNG PHONE FARM")
        print("="*85)
        if not rows:
            print("Chưa có lịch sử đăng bài nào được ghi nhận.")
            print("="*85)
            return

        for r in rows:
            print(f"[{r['timestamp']}] | Kênh: {r['tiktok_account']} | Máy: {r['device_serial']}")
            print(f"  🎬 Video: {r['video_file']}")
            print(f"  🔗 Nguồn gốc: {r['source_url'] or 'Tải trực tiếp/File sẵn'}")
            if r['source_channel']:
                print(f"  📺 Kênh nguồn: {r['source_channel']}")
            print(f"  📝 Caption: {r['caption'][:60]}...")
            print("-" * 85)

if __name__ == '__main__':
    tracker = FarmTracker()
    tracker.print_recent_logs()
