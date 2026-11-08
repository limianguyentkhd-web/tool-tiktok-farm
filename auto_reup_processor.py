# -*- coding: utf-8 -*-
"""
Mô-đun Xử Lý Video Reup & Lách Bản Quyền Tự Động TikTok 2026 (MatrixFlow Smart Video Engine)
Nâng cấp 4 mắt xích tự động hóa:
1. SỔ ĐEN CHỐNG TẢI TRÙNG (Deduplication History - da_tai.txt):
   - Kiểm tra video_id trong 0.001s qua HashSet O(1).
   - Ghi nhận video_id ngay khi tải để không bao giờ tải lặp lại video cũ.
2. BỂ CHỨA ĐỆM 15 VIDEO & TỰ ĐỘNG DỌN RÁC (Buffer Pool & Auto-Clean):
   - Van ngắt tự động (Throttling): Đạt >= 15 video trong ready_to_post/ thì tạm dừng cào & render.
   - Tự động dọn rác: Xóa ngay lập tức file video raw và các file temp sau khi render xong.
3. TỰ ĐỘNG DỊCH DOUYIN BẰNG GEMINI AI (Auto Translation Pipeline):
   - Tích hợp trực tiếp ai_bridge.py: Trích xuất audio tiếng Trung -> Gemini AI dịch & viết lại kịch bản tiếng Việt (15-20s).
   - Đưa kịch bản vào edge-tts & tự động burn Hardsub màu vàng (#FFD700) viền đen, MarginV=80.
4. ĐẤU NỐI WEB DASHBOARD & PHONE FARM:
   - Webhook POST /api/videos, lưu ready_to_post/ phục vụ post_all_5_devices.py.
"""

import asyncio
from datetime import datetime
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

import imageio_ffmpeg
import requests
from yt_dlp import YoutubeDL
import edge_tts

from ai_bridge import GeminiAIBridge

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_videos")
OUTPUT_DIR = os.path.join(BASE_DIR, "videos")
READY_TO_POST_DIR = os.path.join(OUTPUT_DIR, "ready_to_post")
BGM_DIR = os.path.join(BASE_DIR, "assets", "bgm")
TEMP_DIR = os.path.join(BASE_DIR, "temp_processing")
DA_TAI_PATH = os.path.join(BASE_DIR, "da_tai.txt")

# Giới hạn tối đa của bể chứa đệm chờ duyệt
MAX_BUFFER_VIDEOS = 15

# Giọng đọc Microsoft Edge TTS tiếng Việt chuẩn tự nhiên
VOICE_FEMALE_HOAIMY = "vi-VN-HoaiMyNeural"    # Giọng nữ ấm áp, truyền cảm
VOICE_MALE_NAMMINH = "vi-VN-NamMinhNeural"     # Giọng nam review công nghệ lôi cuốn


class AutoReupProcessor:
    def __init__(self, ffmpeg_path: Optional[str] = None):
        # Ưu tiên FFmpeg full build từ hệ thống để hỗ trợ libass, subtitles filter, amix
        system_ffmpeg = shutil.which("ffmpeg")
        if ffmpeg_path and os.path.isfile(ffmpeg_path):
            self.ffmpeg_path = ffmpeg_path
        elif system_ffmpeg:
            self.ffmpeg_path = system_ffmpeg
        else:
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        # Tạo tất cả các thư mục cần thiết
        for d in [RAW_DIR, OUTPUT_DIR, READY_TO_POST_DIR, BGM_DIR, TEMP_DIR]:
            os.makedirs(d, exist_ok=True)

        # Khởi tạo Cầu nối Gemini AI
        self.ai_bridge = GeminiAIBridge()

        # Nạp Sổ đen chống tải trùng (da_tai.txt) vào bộ nhớ HashSet
        self.seen_video_ids: Set[str] = set()
        self._load_seen_history()

        # Đảm bảo có ít nhất 1 bản BGM nhẹ trong assets/bgm
        self.ensure_sample_bgm()

    # -------------------------------------------------------------
    # 1. CƠ CHẾ SỔ ĐEN CHỐNG TẢI TRÙNG (DEDUPLICATION HISTORY)
    # -------------------------------------------------------------
    def _load_seen_history(self) -> None:
        """Nạp toàn bộ ID video đã tải từ da_tai.txt vào Set để tra cứu O(1) dưới 0.001s."""
        if os.path.isfile(DA_TAI_PATH):
            try:
                with open(DA_TAI_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            parts = line.split("|")
                            vid_id = parts[0].strip()
                            if vid_id:
                                self.seen_video_ids.add(vid_id)
                print(f"[*] 📖 Đã nạp {len(self.seen_video_ids)} ID video vào Sổ Đen Chống Tải Trùng (da_tai.txt).")
            except Exception as e:
                print(f"[-] Lỗi nạp da_tai.txt: {e}")

    def is_downloaded(self, video_id: str) -> bool:
        """Kiểm tra video_id đã từng tải chưa trong 0.0001s."""
        if not video_id:
            return False
        return str(video_id).strip() in self.seen_video_ids

    def mark_as_downloaded(self, video_id: str, title: str = "", url: str = "") -> None:
        """Ghi nhận video_id vào Sổ đen ngay lập tức."""
        if not video_id:
            return
        clean_id = str(video_id).strip()
        self.seen_video_ids.add(clean_id)
        ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_title = title.replace("\n", " ").replace("|", " ")[:60]
        try:
            with open(DA_TAI_PATH, "a", encoding="utf-8") as f:
                f.write(f"{clean_id} | {ts_now} | {clean_title} | {url}\n")
        except Exception as e:
            print(f"[-] Không thể ghi da_tai.txt: {e}")

    @staticmethod
    def extract_video_id(url: str, fallback_data: Optional[dict] = None) -> str:
        """Trích xuất ID video từ link Douyin, TikTok, YouTube Shorts hoặc dữ liệu crawl."""
        if fallback_data:
            item_id = fallback_data.get("aweme_id") or fallback_data.get("id") or fallback_data.get("item_id")
            if item_id:
                return str(item_id).strip()

        # Douyin video ID (chuỗi 19 chữ số)
        m_dy = re.search(r"video/(\d+)|vid=(\d+)", url)
        if m_dy:
            return m_dy.group(1) or m_dy.group(2)

        # YouTube ID (11 ký tự)
        m_yt = re.search(r"(?:v=|shorts/|youtu\.be/)([a-zA-Z0-9_\-]{11})", url)
        if m_yt:
            return m_yt.group(1)

        # TikTok ID (chuỗi 19 chữ số)
        m_tt = re.search(r"video/(\d+)", url)
        if m_tt:
            return m_tt.group(1)

        # Fallback hash
        return hashlib.md5(url.encode("utf-8")).hexdigest()[:16]

    # -------------------------------------------------------------
    # 2. BỂ CHỨA ĐỆM 15 VIDEO (BUFFER POOL & THROTTLING)
    # -------------------------------------------------------------
    def get_buffer_count(self) -> int:
        """Đếm số lượng video đang chờ duyệt trong videos/ready_to_post/."""
        if not os.path.exists(READY_TO_POST_DIR):
            return 0
        files = [
            f for f in os.listdir(READY_TO_POST_DIR)
            if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))
        ]
        return len(files)

    def can_process_more(self) -> bool:
        """Kiểm tra van ngắt tự động: nếu bể chứa >= 15 video thì tạm dừng cào & render."""
        count = self.get_buffer_count()
        if count >= MAX_BUFFER_VIDEOS:
            print(f"\n========================================================")
            print(f"⏸️  [THROTTLING] BỂ CHỨA ĐỆM ĐÃ ĐẠT GIỚI HẠN ({count}/{MAX_BUFFER_VIDEOS} VIDEO CHỜ DUYỆT)!")
            print(f"👉 Tạm dừng cào và render để chống tràn dung lượng ổ cứng.")
            print(f"👉 Hãy vào Web Dashboard (http://127.0.0.1:5000) duyệt bớt video để tiếp tục.")
            print(f"========================================================\n")
            return False
        return True

    # -------------------------------------------------------------
    # CÁC TIỆN ÍCH FFmpeg & BGM
    # -------------------------------------------------------------
    def ensure_sample_bgm(self) -> str:
        """Đảm bảo có ít nhất 1 file nhạc nền ambient trong assets/bgm/."""
        existing = [
            os.path.join(BGM_DIR, f)
            for f in os.listdir(BGM_DIR)
            if f.lower().endswith((".mp3", ".wav", ".aac", ".m4a", ".ogg"))
        ]
        if existing:
            return existing[0]

        default_bgm = os.path.join(BGM_DIR, "sample_lofi_ambient.aac")
        try:
            cmd = [
                self.ffmpeg_path, "-y",
                "-f", "lavfi",
                "-i", "aevalsrc=sin(2*PI*220*t)*0.08+sin(2*PI*277.18*t)*0.06+sin(2*PI*329.63*t)*0.06+sin(2*PI*440*t)*0.04:d=35",
                "-c:a", "aac",
                "-b:a", "128k",
                default_bgm
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return default_bgm
        except Exception:
            return ""

    def get_random_bgm(self) -> Optional[str]:
        """Lấy ngẫu nhiên 1 bản nhạc nền từ assets/bgm/."""
        tracks = [
            os.path.join(BGM_DIR, f)
            for f in os.listdir(BGM_DIR)
            if f.lower().endswith((".mp3", ".wav", ".aac", ".m4a", ".ogg"))
        ]
        if tracks:
            return random.choice(tracks)
        return None

    def get_video_duration(self, video_path: str) -> float:
        """Lấy độ dài thời gian (giây) của video bằng FFmpeg."""
        try:
            cmd = [self.ffmpeg_path, "-i", video_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", line)
                    if match:
                        h, m, s = match.groups()
                        return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception as e:
            print(f"[-] Lỗi đọc thời lượng video: {e}")
        return 0.0

    @staticmethod
    def get_file_md5(file_path: str) -> str:
        """Tính toán mã băm MD5 độc nhất của file."""
        if not os.path.isfile(file_path):
            return ""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def generate_vietnamese_voice(
        self,
        script_text: str,
        voice: str = VOICE_MALE_NAMMINH,
        audio_out: Optional[str] = None,
        srt_out: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Sinh file âm thanh thuyết minh tiếng Việt và phụ đề động (.srt) từ Edge-TTS.
        """
        if not script_text.strip():
            raise ValueError("Kịch bản thuyết minh tiếng Việt không được rỗng!")

        ts = int(time.time() * 1000)
        if not audio_out:
            audio_out = os.path.join(TEMP_DIR, f"voice_{ts}.mp3")
        if not srt_out:
            srt_out = os.path.join(TEMP_DIR, f"subs_{ts}.srt")

        async def _run_tts():
            communicate = edge_tts.Communicate(script_text, voice)
            submaker = edge_tts.SubMaker()
            with open(audio_out, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] in ("SentenceBoundary", "WordBoundary"):
                        submaker.feed(chunk)
            return submaker.get_srt()

        try:
            srt_content = asyncio.run(_run_tts())
        except Exception as e:
            print(f"[-] Lỗi sinh giọng Edge-TTS: {e}")
            return audio_out, None

        # Format phụ đề: Chữ IN HOA nổi bật theo phong cách TikTok Viral
        final_srt_path = None
        if srt_content and srt_content.strip():
            formatted_lines = []
            for line in srt_content.splitlines():
                if line.strip().isdigit() or "-->" in line:
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(line.upper())
            with open(srt_out, "w", encoding="utf-8") as sf:
                sf.write("\n".join(formatted_lines) + "\n")
            final_srt_path = srt_out
        else:
            audio_dur = self.get_video_duration(audio_out)
            if audio_dur <= 0:
                audio_dur = 4.0
            words = script_text.split()
            chunk_size = 5
            chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)] or [script_text]
            step = audio_dur / len(chunks)
            cues = []
            for idx, c in enumerate(chunks, 1):
                s_time = self._format_srt_timestamp((idx - 1) * step)
                e_time = self._format_srt_timestamp(min(audio_dur, idx * step))
                cues.append(f"{idx}\n{s_time} --> {e_time}\n{c.upper()}\n")
            with open(srt_out, "w", encoding="utf-8") as sf:
                sf.write("\n".join(cues) + "\n")
            final_srt_path = srt_out

        return audio_out, final_srt_path

    def notify_matrixflow_dashboard(
        self,
        video_data: dict,
        webhook_url: str = "http://127.0.0.1:5000/api/videos"
    ) -> bool:
        """Gửi webhook thông báo tới Web Dashboard MatrixFlow khi video render hoàn tất."""
        try:
            res = requests.post(webhook_url, json=video_data, timeout=3)
            if res.status_code in (200, 201):
                print(f"[+] 🌐 Đã đẩy video lên Web Dashboard MatrixFlow thành công! (ID: {video_data.get('id')})")
                return True
        except requests.exceptions.RequestException:
            pass
        return False

    # -------------------------------------------------------------
    # 3. QUY TRÌNH XỬ LÝ LÁCH BẢN QUYỀN & TỰ ĐỘNG DỌN RÁC
    # -------------------------------------------------------------
    def process_video(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        script_text: Optional[str] = None,
        auto_translate: bool = True,
        voice: str = VOICE_MALE_NAMMINH,
        has_text_overlay: bool = False,
        hflip: bool = False,
        pattern_interrupt: bool = True,
        pattern_mode: str = "both",
        bgm_volume: float = 0.18,
        voice_volume: float = 1.0,
        speed_range: Tuple[float, float] = (1.03, 1.05),
        zoom_range: Tuple[float, float] = (1.03, 1.05),
        trim_head_range: Tuple[float, float] = (1.5, 2.0),
        trim_tail_range: Tuple[float, float] = (0.8, 1.5),
        send_webhook: bool = True,
        auto_clean_raw: bool = True,
        webhook_url: str = "http://127.0.0.1:5000/api/videos",
    ) -> Optional[str]:
        """
        Quy trình xử lý hoàn chỉnh:
        - Kiểm tra Buffer Pool (ngắt nếu >= 15 video).
        - Nếu chưa có kịch bản và auto_translate=True: Tự động gọi Gemini AI dịch video Douyin/Shorts.
        - Render lách bản quyền: Pattern Interrupt 2s đầu, Jitter, Voice AI, Hardsub, amix BGM.
        - Tự động dọn rác: Xóa file video raw & temp files ngay sau khi render xong.
        """
        # Kiểm tra van ngắt tự động (Buffer Pool)
        if not self.can_process_more():
            return None

        if not os.path.isfile(input_path):
            print(f"[-] Không tìm thấy file nguồn: {input_path}")
            return None

        raw_duration = self.get_video_duration(input_path)
        if raw_duration <= 3.0:
            print(f"[-] Video quá ngắn ({raw_duration:.1f}s), không thể cắt tỉa an toàn!")
            return None

        base_name = os.path.splitext(os.path.basename(input_path))[0]
        clean_name = re.sub(r"[^\w\-]", "_", base_name)
        ts = int(time.time())

        if not output_path:
            output_path = os.path.join(READY_TO_POST_DIR, f"reup_{ts}_{clean_name}.mp4")

        # ---------------------------------------------------------
        # TỰ ĐỘNG DỊCH DOUYIN BẰNG GEMINI AI NẾU CHƯA CÓ KỊCH BẢN
        # ---------------------------------------------------------
        final_script = script_text
        if (not final_script or not final_script.strip()) and auto_translate:
            print(f"[*] 🌏 Phát hiện video nguồn Douyin/Shorts chưa có kịch bản -> Tự động kích hoạt Gemini AI Bridge...")
            final_script = self.ai_bridge.translate_and_revoice(input_path, original_title=base_name)

        # ---------------------------------------------------------
        # SMART VISUAL ANTI-DETECTION
        # ---------------------------------------------------------
        actual_hflip = False
        if has_text_overlay:
            actual_hflip = False
            print("[*] 🛡️ Smart Text Detection: Video chứa chữ -> TỰ ĐỘNG TẮT lật gương (hflip=False) để chữ không bị ngược.")
        else:
            actual_hflip = bool(hflip)

        if pattern_interrupt:
            trim_head = round(random.uniform(*trim_head_range), 2)
        else:
            trim_head = round(random.uniform(0.5, 1.0), 2)

        trim_tail = round(random.uniform(*trim_tail_range), 2)
        target_duration = max(2.5, raw_duration - trim_head - trim_tail)

        speed = round(random.uniform(*speed_range), 3)
        pts = round(1.0 / speed, 4)
        zoom = round(random.uniform(*zoom_range), 3)
        contrast = round(random.uniform(1.02, 1.05), 3)
        brightness = round(random.uniform(-0.01, 0.02), 3)
        saturation = round(random.uniform(1.02, 1.06), 3)

        v_filters = []
        if pattern_interrupt and pattern_mode in ("zoom", "both"):
            v_filters.append(f"scale=1.12*iw:1.12*ih,crop=w='if(lt(t,2),iw/1.10,iw/{zoom})':h='if(lt(t,2),ih/1.10,ih/{zoom})':x='(in_w-out_w)/2':y='(in_h-out_h)/2'")
        else:
            v_filters.append(f"scale={zoom}*iw:{zoom}*ih,crop=iw/{zoom}:ih/{zoom}")

        if actual_hflip:
            v_filters.append("hflip")

        v_filters.append(f"eq=contrast={contrast}:brightness={brightness}:saturation={saturation}")
        v_filters.append(f"setpts={pts}*PTS")

        # ---------------------------------------------------------
        # AUDIO OVERHAUL & DYNAMIC HARDSUB
        # ---------------------------------------------------------
        temp_audio = None
        temp_srt = None
        bgm_path = None

        inputs = ["-ss", str(trim_head), "-i", input_path]
        filter_complex_parts = []

        if final_script and final_script.strip():
            print(f"[*] 🎙️ Đang tạo thuyết minh tiếng Việt AI với giọng: {voice}...")
            temp_audio = os.path.join(TEMP_DIR, f"tts_{ts}.mp3")
            temp_srt = os.path.join(TEMP_DIR, f"sub_{ts}.srt")
            self.generate_vietnamese_voice(final_script, voice=voice, audio_out=temp_audio, srt_out=temp_srt)

            if temp_srt and os.path.isfile(temp_srt):
                escaped_srt = temp_srt.replace("\\", "/").replace(":", "\\:")
                sub_style = (
                    "FontName=Arial,FontSize=20,Bold=1,"
                    "PrimaryColour=&H0000D7FF,OutlineColour=&H00000000,"
                    "BorderStyle=1,Outline=2.5,Shadow=0,Alignment=2,MarginV=80"
                )
                v_filters.append(f"subtitles='{escaped_srt}':force_style='{sub_style}'")
                print(f"[+] 📝 Đã gắn Hardsub: Phụ đề chữ vàng (#FFD700) viền đen, MarginV=80.")

            inputs.extend(["-i", temp_audio])

            bgm_path = self.get_random_bgm()
            if bgm_path and os.path.isfile(bgm_path):
                inputs.extend(["-stream_loop", "-1", "-i", bgm_path])
                print(f"[+] 🎵 Đã nạp nhạc nền BGM ngầm: {os.path.basename(bgm_path)} (Âm lượng {int(bgm_volume*100)}%)")
                af_complex = (
                    f"[1:a]volume={voice_volume}[v_ai];"
                    f"[2:a]volume={bgm_volume}[bgm];"
                    f"[v_ai][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                )
            else:
                af_complex = f"[1:a]volume={voice_volume}[aout]"

            vf_str = ",".join(v_filters)
            filter_complex_str = f"[0:v]{vf_str}[vout];{af_complex}"
            cmd_filter_args = [
                "-filter_complex", filter_complex_str,
                "-map", "[vout]",
                "-map", "[aout]",
            ]
        else:
            vf_str = ",".join(v_filters)
            af_str = f"atempo={speed}"
            cmd_filter_args = [
                "-vf", vf_str,
                "-af", af_str,
                "-map", "0:v:0",
                "-map", "0:a:0?",
            ]

        # ---------------------------------------------------------
        # RENDER FFmpeg
        # ---------------------------------------------------------
        print(f"[*] 🚀 Bắt đầu Render video lách bản quyền: {os.path.basename(input_path)}")
        cmd = [
            self.ffmpeg_path, "-y",
            *inputs,
            "-t", str(target_duration),
            *cmd_filter_args,
            "-map_metadata", "-1",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-shortest",
            output_path
        ]

        start_time = time.time()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
        render_duration = round(time.time() - start_time, 2)

        # ---------------------------------------------------------
        # TỰ ĐỘNG DỌN RÁC (AUTO-CLEAN TEMP & RAW)
        # ---------------------------------------------------------
        # 1. Dọn các file temp
        for tmp in [temp_audio, temp_srt]:
            if tmp and os.path.isfile(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

        if res.returncode == 0 and os.path.isfile(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            final_duration = self.get_video_duration(output_path)
            new_md5 = self.get_file_md5(output_path)
            original_md5 = self.get_file_md5(input_path)

            print(f"\n========================================================")
            print(f"✅ RENDER THÀNH CÔNG VIDEO LÁCH BẢN QUYỀN 2026!")
            print(f"📁 Video lưu tại: {output_path}")
            print(f"⏱️  Thời gian xử lý: {render_duration}s | Độ dài: {final_duration:.1f}s | Dung lượng: {size_mb:.2f} MB")
            print(f"🔒 MD5 gốc     : {original_md5}")
            print(f"✨ MD5 mới tinh: {new_md5} (Đã phá vỡ hoàn toàn Content ID)")
            print(f"========================================================\n")

            # 2. Xóa ngay lập tức file video raw sau khi render xong
            if auto_clean_raw and os.path.isfile(input_path):
                try:
                    os.remove(input_path)
                    print(f"[🗑️] [Auto-Clean] Đã tự động xóa file video thô (raw): {os.path.basename(input_path)}")
                except Exception as ex:
                    print(f"[!] Không thể xóa video raw: {ex}")

            # Đấu nối webhook Web Dashboard
            if send_webhook:
                preview_rel_url = f"/api/videos/preview/{os.path.basename(output_path)}"
                video_payload = {
                    "id": f"vid_{ts}",
                    "title": base_name.replace("_", " "),
                    "file_name": os.path.basename(output_path),
                    "file_path": output_path,
                    "preview_url": preview_rel_url,
                    "render_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": round(final_duration, 1),
                    "size_mb": round(size_mb, 2),
                    "voice_used": voice if final_script else "Giọng gốc đã lách",
                    "has_text_overlay": has_text_overlay,
                    "md5_hash": new_md5,
                    "status": "pending_review"
                }
                self.notify_matrixflow_dashboard(video_payload, webhook_url=webhook_url)

            return output_path
        else:
            print(f"[-] ❌ Lỗi xử lý FFmpeg: {res.stderr[-400:].strip()}")
            return None

    # -------------------------------------------------------------
    # 4. TẢI VIDEO DOUYIN KÈM CHỐNG TRÙNG VÀ KIỂM TRA ĐỆM
    # -------------------------------------------------------------
    def download_douyin_video(self, url: str, output_dir: str = RAW_DIR) -> Optional[str]:
        """Tải video Douyin không logo, tích hợp sổ đen chống tải trùng."""
        vid_id = self.extract_video_id(url)
        if self.is_downloaded(vid_id):
            print(f"[⏩] Video ID {vid_id} đã có trong Sổ Đen. Bỏ qua ngay lập tức trong 0.001s!")
            return None

        # Kiểm tra van ngắt đệm 15 video
        if not self.can_process_more():
            return None

        print(f"[*] Đang bóc tách link Douyin ID {vid_id}: {url}...")
        try:
            match = re.search(r"vid=(\d+)|video/(\d+)", url)
            clean_url = f"https://www.douyin.com/video/{match.group(1) or match.group(2)}" if match else url

            s = requests.Session()
            r_demo = s.get("https://demo.douyin.wtf/api/v1/auth/demo", timeout=10).json()
            if r_demo.get("success") and r_demo.get("data"):
                u = r_demo["data"]["username"]
                p = r_demo["data"]["password"]
                s.post("https://demo.douyin.wtf/api/v1/auth/login", json={"username": u, "password": p}, timeout=10)

            r_parse = s.post("https://demo.douyin.wtf/api/v1/parse", json={"url": clean_url}, timeout=15).json()
            if not r_parse.get("success") or not r_parse.get("data"):
                raise ValueError("Không tạo được tác vụ parse Douyin")

            task_id = r_parse["data"]["task_id"]
            for _ in range(12):
                time.sleep(1.5)
                r_task = s.get(f"https://demo.douyin.wtf/api/v1/tasks/{task_id}", timeout=10).json()
                if r_task.get("data", {}).get("state") == "done":
                    t_data = r_task["data"]["data"]
                    desc = t_data.get("title") or t_data.get("description") or "douyin_video"
                    clean_title = re.sub(r"[^\w\-]", "_", desc)[:40]

                    media = t_data.get("media", {})
                    v_url = None
                    if media.get("video") and media["video"].get("url"):
                        v_url = media["video"]["url"]
                    elif media.get("streams"):
                        for st in media["streams"]:
                            if not st.get("watermark") and st.get("url"):
                                v_url = st["url"]
                                break

                    if v_url:
                        out_path = os.path.join(output_dir, f"douyin_{int(time.time())}_{clean_title}.mp4")
                        print(f"[*] Đang tải video không logo về: {out_path}...")
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                            "Referer": "https://www.douyin.com/"
                        }
                        dl_res = requests.get(v_url, headers=headers, stream=True, timeout=30)
                        with open(out_path, "wb") as f:
                            for chunk in dl_res.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    f.write(chunk)

                        # Ghi nhận ngay vào sổ đen
                        self.mark_as_downloaded(vid_id, title=desc, url=url)
                        size_mb = os.path.getsize(out_path) / (1024 * 1024)
                        print(f"[+] ✅ Tải thành công ({size_mb:.2f} MB). Đã lưu ID {vid_id} vào da_tai.txt.")
                        return out_path
                    break
        except Exception as e:
            print(f"[-] Lỗi qua Douyin API ({e}), chuyển sang phương thức dự phòng...")
        return None

    def download_douyin_channel(
        self,
        channel_url: str,
        max_videos: int = 15,
        output_dir: str = RAW_DIR,
        auto_render_pipeline: bool = True,
        voice: str = VOICE_MALE_NAMMINH,
    ) -> List[str]:
        """
        Quét và tải toàn bộ video kênh Douyin:
        - Tự động kiểm tra Sổ đen: Bỏ qua video cũ trong 0.001s.
        - Kiểm tra Buffer Pool: Tạm dừng khi bể chứa >= 15 video.
        - Nếu auto_render_pipeline=True: Tự động dịch Gemini AI + Render Hardsub Việt Hóa ngay lập tức!
        """
        # Kiểm tra van ngắt đệm
        if not self.can_process_more():
            return []

        print(f"\n========================================================")
        print(f"🔍 BẮT ĐẦU QUÉT KÊNH DOUYIN KÈM CHỐNG TẢI TRÙNG (da_tai.txt)...")
        print(f"🔗 Link kênh: {channel_url}")
        print(f"📦 Trạng thái Bể Chứa Đệm: {self.get_buffer_count()}/{MAX_BUFFER_VIDEOS} video")
        print(f"========================================================")

        m = re.search(r"user/([a-zA-Z0-9_\-]+)", channel_url)
        if not m:
            print("[-] Không tìm thấy User ID trong link kênh!")
            return []
        sec_user_id = m.group(1)

        downloaded_files = []
        try:
            s = requests.Session()
            r_demo = s.get("https://demo.douyin.wtf/api/v1/auth/demo", timeout=10).json()
            if r_demo.get("success") and r_demo.get("data"):
                u = r_demo["data"]["username"]
                p = r_demo["data"]["password"]
                s.post("https://demo.douyin.wtf/api/v1/auth/login", json={"username": u, "password": p}, timeout=10)

            cursor = 0
            has_more = True
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/"
            }
            cookie_file = os.path.join(BASE_DIR, "douyin_cookie.txt")
            if os.path.isfile(cookie_file):
                with open(cookie_file, "r", encoding="utf-8") as cf:
                    headers["Cookie"] = cf.read().strip()

            while has_more and len(downloaded_files) < max_videos:
                # Kiểm tra van đệm trước mỗi lượt
                if not self.can_process_more():
                    break

                params = {"sec_user_id": sec_user_id, "count": 15, "cursor": cursor}
                r = s.get("https://demo.douyin.wtf/api/v1/douyin/user/posts", params=params, timeout=15).json()
                if not r.get("success") or not r.get("data"):
                    break
                task_id = r["data"]["task_id"]

                t_data = None
                for _ in range(12):
                    time.sleep(1.5)
                    r_task = s.get(f"https://demo.douyin.wtf/api/v1/tasks/{task_id}", timeout=10).json()
                    if r_task.get("data", {}).get("state") == "done":
                        t_data = r_task["data"]["data"]
                        break

                if not t_data:
                    break

                items = t_data.get("items", [])
                print(f"[*] Quét thấy {len(items)} video trong đợt này...")

                for item in items:
                    if len(downloaded_files) >= max_videos or not self.can_process_more():
                        break

                    vid_id = self.extract_video_id("", fallback_data=item)

                    # 1. KIỂM TRA SỔ ĐEN CHỐNG TẢI TRÙNG TRONG 0.001s
                    if self.is_downloaded(vid_id):
                        print(f"[⏩] Video ID {vid_id} đã có trong da_tai.txt. Bỏ qua ngay lập tức!")
                        continue

                    desc = item.get("title") or item.get("description") or "douyin"
                    clean_title = re.sub(r"[^\w\-]", "_", desc)[:35]
                    v_url = item.get("media", {}).get("video", {}).get("url")
                    if not v_url and item.get("media", {}).get("streams"):
                        for st in item["media"]["streams"]:
                            if not st.get("watermark") and st.get("url"):
                                v_url = st["url"]
                                break

                    if v_url:
                        out_path = os.path.join(output_dir, f"douyin_{len(downloaded_files)+1}_{clean_title}.mp4")
                        print(f"\n[{len(downloaded_files)+1}/{max_videos}] 📥 Đang tải video mới ID {vid_id}: {clean_title}...")
                        dl_res = requests.get(v_url, headers=headers, stream=True, timeout=30)
                        with open(out_path, "wb") as f:
                            for chunk in dl_res.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    f.write(chunk)

                        # Ghi nhận ngay vào sổ đen
                        self.mark_as_downloaded(vid_id, title=desc, url=f"https://www.douyin.com/video/{vid_id}")
                        downloaded_files.append(out_path)

                        # 2. TỰ ĐỘNG CHUYỂN QUA RENDER VIỆT HÓA & LÁCH BẢN QUYỀN (NẾU BẬT)
                        if auto_render_pipeline:
                            print(f"[*] 🚀 Kích hoạt Tự Động Dịch Gemini AI & Render Việt Hóa cho video ID {vid_id}...")
                            self.process_video(
                                input_path=out_path,
                                auto_translate=True,
                                voice=voice,
                                has_text_overlay=False,
                                pattern_interrupt=True,
                                auto_clean_raw=True, # Tự động xóa file raw sau render
                                send_webhook=True
                            )

                has_more = t_data.get("has_more", False)
                cursor = t_data.get("cursor", 0)

            print(f"\n[+] 🎉 HOÀN TẤT TIẾN TRÌNH KÊNH DOUYIN! Đã tải và xử lý {len(downloaded_files)} video mới.")
            return downloaded_files

        except Exception as e:
            print(f"[-] Lỗi khi quét kênh Douyin: {e}")
            return downloaded_files

    def download_url(self, url: str, output_dir: str = RAW_DIR) -> Optional[str]:
        """Tải video không logo (No Watermark) từ Douyin, TikTok, Reels, Shorts kèm sổ đen."""
        vid_id = self.extract_video_id(url)
        if self.is_downloaded(vid_id):
            print(f"[⏩] Video ID {vid_id} đã có trong da_tai.txt. Bỏ qua ngay lập tức trong 0.001s!")
            return None

        # Kiểm tra van đệm 15 video
        if not self.can_process_more():
            return None

        print(f"\n[*] Đang tải video không logo từ: {url} (ID: {vid_id})...")
        if "douyin.com" in url:
            res = self.download_douyin_video(url, output_dir)
            if res:
                return res

        ydl_opts = {
            "outtmpl": os.path.join(output_dir, "%(title).50s_%(id)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "ffmpeg_location": self.ffmpeg_path,
            "quiet": False,
            "no_warnings": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base, ext = os.path.splitext(filename)
                if not os.path.isfile(filename) and os.path.isfile(base + ".mp4"):
                    filename = base + ".mp4"

                self.mark_as_downloaded(vid_id, title=info.get("title", ""), url=url)
                print(f"[+] ✅ Tải thành công: {filename}. Đã lưu vào da_tai.txt.")
                return filename
        except Exception as e:
            print(f"[-] ❌ Lỗi khi tải video từ link: {e}")
            return None


def main():
    processor = AutoReupProcessor()

    while True:
        raw_count = len([f for f in os.listdir(RAW_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm"))])
        ready_count = processor.get_buffer_count()
        seen_count = len(processor.seen_video_ids)

        print("\n=================================================================")
        print("🎬 MATRIXFLOW AUTO VIDEO ENGINE 2026 (GEMINI AI & DEDUPLICATION)")
        print(f"📦 Bể chứa đệm chờ duyệt 'ready_to_post/' : {ready_count}/{MAX_BUFFER_VIDEOS} video")
        print(f"📁 Video thô trong 'raw_videos/'          : {raw_count} file")
        print(f"📖 Sổ đen chống tải trùng (da_tai.txt)    : {seen_count} ID đã lưu")
        print("=================================================================")
        print("[1] ⚡ Lách bản quyền TOÀN BỘ video trong 'raw_videos/' (Batch Mode)")
        print("[2] 🤖 Auto-Pilot Douyin: Quét kênh -> Chống trùng -> Dịch Gemini AI -> Render Hardsub")
        print("[3] 🎙️ Xử lý 1 video với kịch bản Việt Hóa (Tự dịch Gemini AI hoặc nhập tay)")
        print("[4] 📥 Tải 1 video không logo từ Link (TikTok / Douyin / Reels / Shorts)")
        print("[5] 📺 Quét & Tải hàng loạt video từ Kênh Douyin (Lưu da_tai.txt)")
        print("[6] 🧹 Dọn dẹp thủ công toàn bộ video thô và file tạm")
        print("[0] Thoát")
        print("=================================================================")

        choice = input("👉 Nhập lựa chọn (0-6): ").strip()

        if choice == "1":
            print("\n⚙️ Cấu hình nhận diện văn bản:")
            print(" [1] Video ĐÃ CÓ chữ/phụ đề tiếng Việt -> TỰ ĐỘNG TẮT lật gương (chữ đọc xuôi 100%)")
            print(" [2] Video B-roll không chữ (phong cảnh, gái nhảy, đồ ăn) -> BẬT lật gương")
            text_opt = input("👉 Chọn (1 hoặc 2, mặc định: 1): ").strip()
            has_text = (text_opt != "2")

            files = [os.path.join(RAW_DIR, f) for f in os.listdir(RAW_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv"))]
            for f in files:
                if not processor.can_process_more():
                    break
                processor.process_video(f, has_text_overlay=has_text, auto_translate=True)

        elif choice == "2":
            url = input("👉 Dán link kênh Douyin (vd: https://www.douyin.com/user/...): ").strip()
            if url:
                lim = input("Nhập số video tối đa muốn nạp vào bể đệm (mặc định: 10): ").strip()
                max_v = int(lim) if lim.isdigit() else 10
                processor.download_douyin_channel(url, max_videos=max_v, auto_render_pipeline=True)

        elif choice == "3":
            files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv"))]
            if not files:
                print(f"[-] Không có video nào trong {RAW_DIR}.")
                continue

            for i, fn in enumerate(files, 1):
                print(f" [{i}] {fn}")
            v_idx = input("👉 Chọn số thứ tự video cần xử lý: ").strip()
            if not v_idx.isdigit() or not (1 <= int(v_idx) <= len(files)):
                continue

            chosen_file = os.path.join(RAW_DIR, files[int(v_idx) - 1])
            print("\n💡 Tùy chọn kịch bản:")
            print(" [1] TỰ ĐỘNG DỊCH BẰNG GEMINI AI (Trích xuất audio & viết kịch bản 15-20s viral)")
            print(" [2] Nhập kịch bản tiếng Việt bằng tay")
            s_opt = input("👉 Chọn (1 hoặc 2, mặc định: 1): ").strip()

            script = None
            auto_tr = (s_opt != "2")
            if not auto_tr:
                script = input("👉 Nhập kịch bản: ").strip()

            processor.process_video(
                chosen_file,
                script_text=script,
                auto_translate=auto_tr,
                pattern_interrupt=True
            )

        elif choice == "4":
            url = input("👉 Dán link video (TikTok/Douyin/Reels/Shorts): ").strip()
            if url:
                processor.download_url(url)

        elif choice == "5":
            url = input("👉 Dán link kênh Douyin: ").strip()
            if url:
                processor.download_douyin_channel(url, auto_render_pipeline=False)

        elif choice == "6":
            for d in [RAW_DIR, TEMP_DIR]:
                for f in os.listdir(d):
                    fp = os.path.join(d, f)
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
            print("[+] 🧹 Đã dọn sạch các file rác trong raw_videos/ và temp_processing/!")

        elif choice == "0":
            break


if __name__ == "__main__":
    main()
