# -*- coding: utf-8 -*-
"""
Module Xử Lý Video Reup & Lách Bản Quyền Đa Kênh (Video Processor)
Tự động tải video từ kênh nguồn của từng nick và render chống gậy bản quyền.
"""

import os
import re
import time
import random
import subprocess
from typing import Optional, List, Tuple
import imageio_ffmpeg
from yt_dlp import YoutubeDL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_videos")
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "videos")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

class VideoProcessor:
    def __init__(self):
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    def get_duration(self, video_path: str) -> float:
        try:
            cmd = [self.ffmpeg_path, "-i", video_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", line)
                    if match:
                        h, m, s = match.groups()
                        return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            pass
        return 0.0

    def download_video(self, url: str, output_dir: str = RAW_DIR) -> Optional[Tuple[str, str]]:
        """
        Tải video chất lượng tốt nhất không logo từ Douyin, TikTok, Shorts, Reels.
        Trả về (đường_dẫn_file, tiêu_đề_gốc).
        """
        os.makedirs(output_dir, exist_ok=True)
        out_tmpl = os.path.join(output_dir, "%(title).80s_%(id)s.%(ext)s")
        ydl_opts = {
            "outtmpl": out_tmpl,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return None
                filename = ydl.prepare_filename(info)
                if not filename.endswith(".mp4"):
                    filename = os.path.splitext(filename)[0] + ".mp4"
                title = info.get("title", "")
                return filename, title
        except Exception as e:
            print(f"[-] Lỗi tải video từ {url}: {e}")
            return None

    def anti_detect_render(
        self,
        input_path: str,
        output_path: str,
        hflip: bool = False,
        speed_range: Tuple[float, float] = (1.03, 1.05),
        zoom_range: Tuple[float, float] = (1.03, 1.05)
    ) -> bool:
        """
        Lách thuật toán ByteDance:
        - Cắt đầu đuôi ngẫu nhiên (Trim)
        - Phóng to & Cắt viền (Zoom & Crop)
        - Đổi tốc độ tự nhiên (Speed & Pitch)
        - Chỉnh tương phản, độ sáng nhẹ (Color Grading)
        - Xóa siêu dữ liệu & hash MD5 mới
        """
        if not os.path.isfile(input_path):
            return False

        duration = self.get_duration(input_path)
        if duration <= 3.0:
            return False

        trim_head = round(random.uniform(0.5, 1.2), 2)
        trim_tail = round(random.uniform(0.6, 1.2), 2)
        target_duration = max(2.0, duration - trim_head - trim_tail)

        speed = round(random.uniform(*speed_range), 3)
        pts = round(1.0 / speed, 4)
        zoom = round(random.uniform(*zoom_range), 3)

        contrast = round(random.uniform(1.02, 1.04), 3)
        brightness = round(random.uniform(-0.01, 0.02), 3)
        saturation = round(random.uniform(1.02, 1.05), 3)

        v_filters = []
        if hflip:
            v_filters.append("hflip")
        v_filters.append(f"scale={zoom}*iw:{zoom}*ih,crop=iw/{zoom}:ih/{zoom}")
        v_filters.append(f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation}")
        v_filters.append(f"setpts={pts}*PTS")

        vf_str = ",".join(v_filters)
        af_str = f"atempo={speed}"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = [
            self.ffmpeg_path, "-y",
            "-ss", str(trim_head),
            "-i", input_path,
            "-t", str(target_duration),
            "-vf", vf_str,
            "-af", af_str,
            "-map_metadata", "-1",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
        return res.returncode == 0 and os.path.isfile(output_path)
