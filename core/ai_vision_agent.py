# -*- coding: utf-8 -*-
"""
Tầng 2: Mắt Thần AI Cứu Hộ (Vision AI Rescue Agent)
Sử dụng Gemini Flash Vision API để nhìn ảnh chụp màn hình như mắt người thật,
tự phát hiện nút bấm hoặc cách thoát kẹt khi gặp sự cố lạ.
"""

import os
import json
import base64
import re
from typing import Dict, Any, Optional, Tuple
import requests

class VisionAIAgent:
    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def analyze_screen(self, image_path: str, screen_width: int, screen_height: int, current_goal: str = "Đăng video TikTok") -> Dict[str, Any]:
        """
        Gửi ảnh chụp màn hình lên Gemini Vision để nhận diện tình trạng và tọa độ thoát kẹt.
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Chưa nhập Gemini API Key trong phần Cài đặt.",
                "is_stuck": False
            }

        if not os.path.exists(image_path):
            return {"success": False, "error": "Không tìm thấy file ảnh màn hình.", "is_stuck": False}

        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}

            prompt = f"""
Bạn là chuyên gia giám sát và vận hành dàn Phone Farm TikTok tự động.
Mục tiêu hiện tại của máy: "{current_goal}".
Hãy quan sát bức ảnh chụp màn hình điện thoại đính kèm:
1. Màn hình này có đang bị vướng Popup, Dialog, Captcha, Thông báo lỗi hoặc kẹt không?
2. Nếu bị kẹt hoặc cần bấm để tiếp tục mục tiêu, hãy chỉ ra nút cần bấm (ví dụ dấu X đóng, nút Hủy, Bỏ qua, Tiếp tục, Cho phép...).

BẮT BUỘC trả về duy nhất một chuỗi JSON hợp lệ không có markdown codeblock, theo cấu trúc:
{{
  "is_stuck": true hoặc false,
  "issue": "mô tả ngắn tình trạng màn hình bằng tiếng Việt",
  "action": "click" hoặc "back" hoặc "restart" hoặc "none",
  "x_percent": số từ 0 đến 100 (tọa độ X tính theo phần trăm màn hình, ví dụ 85.5 nếu ở góc phải),
  "y_percent": số từ 0 đến 100 (tọa độ Y tính theo phần trăm màn hình, ví dụ 12.0 nếu ở góc trên)
}}
"""

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": img_b64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 500
                }
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Lỗi Gemini API HTTP {resp.status_code}: {resp.text[:200]}",
                    "is_stuck": False
                }

            result_json = resp.json()
            candidates = result_json.get("candidates", [])
            if not candidates:
                return {"success": False, "error": "AI không trả về kết quả", "is_stuck": False}

            text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            # Làm sạch JSON nếu AI bọc trong ```json ... ```
            cleaned = re.sub(r"^```(?:json)?\s*", "", text_content.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned.strip())

            data = json.loads(cleaned)
            
            # Tính tọa độ thực tế pixel từ phần trăm
            x_pct = float(data.get("x_percent", 50))
            y_pct = float(data.get("y_percent", 50))
            real_x = int(x_pct / 100.0 * screen_width)
            real_y = int(y_pct / 100.0 * screen_height)

            return {
                "success": True,
                "is_stuck": data.get("is_stuck", False),
                "issue": data.get("issue", ""),
                "action": data.get("action", "none"),
                "pixel_x": real_x,
                "pixel_y": real_y,
                "raw": data
            }

        except Exception as e:
            return {"success": False, "error": f"Lỗi phân tích AI: {str(e)}", "is_stuck": False}
