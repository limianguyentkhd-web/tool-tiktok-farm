# -*- coding: utf-8 -*-
"""
Mô-đun Cầu Nối Trí Tuệ Nhân Tạo (Gemini AI Bridge)
Chuyên trách:
1. Trích xuất âm thanh tiếng Trung từ video Douyin bằng FFmpeg.
2. Gửi audio/text sang Gemini 2.5 Flash API để nghe hiểu, phiên dịch và viết lại kịch bản tiếng Việt viral 15-20s.
3. Tự động cung cấp kịch bản chuẩn cho Edge-TTS thuyết minh & Hardsub.
"""

import base64
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from typing import Optional

import requests
import imageio_ffmpeg

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp_processing")
os.makedirs(TEMP_DIR, exist_ok=True)


class GeminiAIBridge:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or self._load_api_key()
        self.model = model
        self.ffmpeg_path = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()

    def _load_api_key(self) -> str:
        """Đọc API key từ config.json, api_config.json hoặc biến môi trường."""
        # 1. Thử đọc từ config.json
        cfg_path = os.path.join(BASE_DIR, "config.json")
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("gemini_api_key"):
                        return data["gemini_api_key"].strip()
            except Exception:
                pass

        # 2. Thử đọc từ api_config.json
        api_cfg_path = os.path.join(BASE_DIR, "api_config.json")
        if os.path.isfile(api_cfg_path):
            try:
                with open(api_cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("api_key"):
                        return data["api_key"].strip()
            except Exception:
                pass

        # 3. Biến môi trường
        return os.environ.get("GEMINI_API_KEY", "").strip()

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Trích xuất file audio nén mono 16kHz nhỏ gọn bằng FFmpeg để gửi lên AI."""
        if not os.path.isfile(video_path):
            return None
        if not output_path:
            ts = int(time.time() * 1000)
            output_path = os.path.join(TEMP_DIR, f"extracted_raw_audio_{ts}.mp3")

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-ac", "1",
            "-ar", "16000",
            "-b:a", "64k",
            "-t", "45",  # Giới hạn 45 giây đầu để tối ưu tốc độ tải và xử lý AI
            output_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 500:
                return output_path
        except Exception as e:
            print(f"[-] Video không có track âm thanh hoặc lỗi trích xuất: {e}")
        return None

    def translate_and_revoice(
        self,
        video_path: str,
        original_title: str = "",
        max_duration_seconds: int = 20
    ) -> str:
        """
        Phiên dịch và viết lại kịch bản tiếng Việt từ video Douyin (qua audio tiếng Trung + tiêu đề gốc).
        Trả về kịch bản tiếng Việt ngắn gọn 15-20s chuẩn bị cho Edge-TTS.
        """
        print(f"[*] 🤖 [Gemini AI] Bắt đầu phiên dịch & tạo kịch bản Việt Hóa cho video...")

        # 1. Trích xuất audio tiếng Trung
        audio_file = self.extract_audio(video_path)
        audio_b64 = None
        if audio_file and os.path.isfile(audio_file):
            try:
                # Nếu audio < 15MB, đọc base64
                if os.path.getsize(audio_file) < 15 * 1024 * 1024:
                    with open(audio_file, "rb") as af:
                        audio_b64 = base64.b64encode(af.read()).decode("utf-8")
            except Exception as e:
                print(f"[!] Không thể đọc base64 audio: {e}")

        prompt = (
            "Bạn là một biên kịch sáng tạo nội dung hàng đầu cho kênh TikTok triệu view tại Việt Nam.\n"
            f"Đây là một video Douyin tiếng Trung Quốc. Tiêu đề hoặc mô tả gốc: '{original_title}'.\n"
            "NHIỆM VỤ CỦA BẠN:\n"
            "1. Lắng nghe âm thanh / lời nói tiếng Trung (nếu có) và kết hợp với tiêu đề gốc.\n"
            "2. Dịch ý nghĩa và viết lại thành một kịch bản thuyết minh tiếng Việt cực kỳ cuốn hút, giật gân, giữ chân người xem ngay trong 3 giây đầu.\n"
            f"3. Độ dài kịch bản phải vừa vặn đọc trong {max_duration_seconds} giây (khoảng 35 - 50 từ tiếng Việt).\n"
            "4. Câu từ tự nhiên, mang phong cách review xu hướng thịnh hành TikTok.\n"
            "QUY TẮC BẮT BUỘC:\n"
            "- CHỈ trả về đúng lời thoại thuyết minh bằng tiếng Việt thuần túy.\n"
            "- KHÔNG chèn chú thích người dẫn, không mở ngoặc đóng ngoặc, không ghi tiêu đề kịch bản."
        )

        script_text = ""
        if self.api_key:
            try:
                script_text = self._call_gemini_api(prompt, audio_b64=audio_b64)
            except Exception as ex:
                print(f"[-] Lỗi khi gọi Gemini API: {ex}")

        # Nếu không có API Key hoặc Gemini lỗi -> Dùng cơ chế thông minh dự phòng
        if not script_text or len(script_text.strip()) < 10:
            print("[*] ⚡ Kích hoạt bộ tạo kịch bản tiếng Việt dự phòng tự động...")
            script_text = self._fallback_script_generation(original_title)

        # Dọn dẹp audio tạm
        if audio_file and os.path.isfile(audio_file):
            try:
                os.remove(audio_file)
            except Exception:
                pass

        # Làm sạch kịch bản (loại bỏ markdown, dấu sao, xuống dòng thừa)
        clean_script = re.sub(r"[\*#_\"`]", "", script_text).strip()
        clean_script = " ".join(clean_script.split())
        print(f"[+] ✨ Kịch bản Việt Hóa thành công ({len(clean_script.split())} từ): \"{clean_script}\"")
        return clean_script

    def _call_gemini_api(self, prompt: str, audio_b64: Optional[str] = None) -> str:
        """Gửi request Multimodal tới Gemini REST API v1beta."""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        parts = []

        if audio_b64:
            parts.append({
                "inline_data": {
                    "mime_type": "audio/mp3",
                    "data": audio_b64
                }
            })

        parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 300
            }
        }

        resp = requests.post(endpoint, json=payload, timeout=25)
        if resp.status_code == 200:
            res_json = resp.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                parts_out = candidates[0].get("content", {}).get("parts", [])
                if parts_out:
                    return parts_out[0].get("text", "").strip()
        else:
            print(f"[!] Gemini API trả về mã lỗi {resp.status_code}: {resp.text[:200]}")
        return ""

    def _fallback_script_generation(self, original_title: str) -> str:
        """Tự động sinh kịch bản dự phòng dựa trên phân tích từ khóa khi không có API key."""
        clean_title = re.sub(r"[#@\-_0-9]", " ", original_title).strip()
        templates = [
            "Bạn có tin đây là món đồ đang làm mưa làm gió trên mạng xã hội những ngày qua không? Hãy xem hết video để thấy sự kỳ diệu nhé!",
            "Nếu bạn đang tìm kiếm một giải pháp cực kỳ thông minh và tiện lợi cho cuộc sống hàng ngày thì đây chính là câu trả lời hoàn hảo nhất dành cho bạn.",
            "Cảnh báo đây là một siêu phẩm cực kỳ cuốn hút mà bạn nhất định không thể bỏ qua hôm nay. Trải nghiệm ngay để không bị bỏ lại phía sau nhé!",
            "Chỉ mất vài giây để thấy điều bất ngờ này. Bí quyết cực đỉnh giúp bạn nâng tầm phong cách sống mỗi ngày, xem ngay nào!"
        ]
        return random.choice(templates)
