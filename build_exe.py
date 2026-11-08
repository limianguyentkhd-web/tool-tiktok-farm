# -*- coding: utf-8 -*-
"""
Script Tự Động Đóng Gói Phần Mềm Thành File Chạy .EXE (PyInstaller Packager)
"""

import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("=" * 60)
    print("🚀 BẮT ĐẦU ĐÓNG GÓI TIKTOK FARM STUDIO RA FILE .EXE")
    print("=" * 60)

    # Đảm bảo có pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("[-] Đang cài đặt PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",                  # Đóng gói dạng thư mục phân phối tiện cập nhật
        "--windowed",                # Ẩn cửa sổ dòng lệnh đen khi chạy
        "--name", "TikTokFarmStudio",
        "--add-data", f"tai_khoan_farm.json;.",
        "--hidden-import", "PyQt6",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "imageio_ffmpeg",
        "--hidden-import", "requests",
        "main.py"
    ]

    print(f"[*] Đang thực thi lệnh: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=BASE_DIR)

    if res.returncode == 0:
        dist_dir = os.path.join(BASE_DIR, "dist", "TikTokFarmStudio")
        print("\n" + "=" * 60)
        print("🎉 ĐÓNG GÓI THÀNH CÔNG!")
        print(f"📂 Thư mục chứa phần mềm: {dist_dir}")
        print(f"👉 File thực thi: {os.path.join(dist_dir, 'TikTokFarmStudio.exe')}")
        print("=" * 60)
    else:
        print("\n[-] ❌ Quá trình đóng gói gặp lỗi!")

if __name__ == "__main__":
    build()
