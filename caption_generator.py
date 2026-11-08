"""
Mô-đun đấu nối API Key (Gemini, OpenAI, DeepSeek, Groq, OpenRouter) 
để tự động sinh Caption TikTok triệu view & Hashtag chuẩn SEO.
"""

import json
import os
import sys
from typing import Dict, Optional
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "api_config.json")

DEFAULT_CONFIG = {
    "provider": "gemini",
    "api_key": "",
    "model": "gemini-2.5-flash",
    "base_url": "",
    "niche": "Chia sẻ cuộc sống, xu hướng, giải trí",
    "style": "Hấp dẫn, giữ chân 3s đầu, kèm call to action"
}


def load_config() -> dict:
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class AICaptionGenerator:
    def __init__(self):
        self.config = load_config()

    def set_api_key(self, provider: str, api_key: str, model: Optional[str] = None) -> None:
        """Lưu API key và nhà cung cấp vào cấu hình."""
        self.config["provider"] = provider.lower()
        self.config["api_key"] = api_key.strip()
        if model:
            self.config["model"] = model.strip()
        else:
            if self.config["provider"] == "gemini":
                self.config["model"] = "gemini-2.5-flash"
            elif self.config["provider"] == "openai":
                self.config["model"] = "gpt-4o-mini"
            elif self.config["provider"] == "deepseek":
                self.config["model"] = "deepseek-chat"
            elif self.config["provider"] == "groq":
                self.config["model"] = "llama-3.3-70b-versatile"

        save_config(self.config)
        print(f"[+] Đã lưu cấu hình API: Nhà cung cấp={self.config['provider']} | Model={self.config['model']}")

    def generate_caption(self, topic_or_filename: str, custom_instruction: str = "") -> str:
        """
        Gọi API sinh caption TikTok hấp dẫn + hashtag chuẩn SEO.
        """
        api_key = self.config.get("api_key", "").strip()
        if not api_key:
            return f"Video hay mỗi ngày! Xem ngay đừng bỏ lỡ #fyp #xuhuong #trending"

        provider = self.config.get("provider", "gemini").lower()
        model = self.config.get("model", "gemini-2.5-flash")

        system_prompt = (
            "Bạn là một chuyên gia sáng tạo nội dung TikTok hàng đầu với hàng triệu người theo dõi. "
            "Nhiệm vụ của bạn là viết 1 caption TikTok tiếng Việt cực kỳ cuốn hút, giữ chân người xem trong 3 giây đầu, "
            "văn phong tự nhiên đời thường, kèm 4-7 hashtag thịnh hành chuẩn SEO TikTok.\n"
            "YÊU CẦU QUAN TRỌNG:\n"
            "- Không viết lời mở đầu, không viết giải thích (như 'Dưới đây là...', 'Đây là caption...').\n"
            "- Không đặt văn bản trong dấu ngoặc kép.\n"
            "- Chỉ trả về duy nhất nội dung caption và các hashtag trên cùng đoạn hoặc xuống dòng ngắn gọn."
        )

        user_content = f"Chủ đề / Tên video: {topic_or_filename}\n"
        if custom_instruction:
            user_content += f"Yêu cầu đặc biệt: {custom_instruction}\n"
        else:
            user_content += f"Chủ đề ngách: {self.config.get('niche', 'Đời sống, giải trí')}\n"

        try:
            if provider == "gemini":
                return self._call_gemini(api_key, model, system_prompt, user_content)
            elif provider in ["openai", "deepseek", "groq", "openrouter", "custom"]:
                return self._call_openai_compatible(provider, api_key, model, system_prompt, user_content)
            else:
                return self._call_gemini(api_key, model, system_prompt, user_content)
        except Exception as e:
            print(f"[-] Lỗi gọi AI API ({provider}): {e}")
            return f"Video thú vị hôm nay! #fyp #xuhuong #viral"

    def _call_gemini(self, api_key: str, model: str, system_prompt: str, user_content: str) -> str:
        # Hỗ trợ gemini-2.5-flash, gemini-1.5-flash, gemini-1.5-pro
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_content}]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 250
            }
        }
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
        return "Xem ngay video siêu cuốn! #fyp #xuhuong #trending"

    def _call_openai_compatible(self, provider: str, api_key: str, model: str, system_prompt: str, user_content: str) -> str:
        base_urls = {
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "openrouter": "https://openrouter.ai/api/v1"
        }
        base_url = self.config.get("base_url") or base_urls.get(provider, "https://api.openai.com/v1")
        url = f"{base_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.8,
            "max_tokens": 250
        }
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        data = res.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return "Xem ngay video cực đỉnh hôm nay! #fyp #xuhuong #trending"


def configure_interactive():
    gen = AICaptionGenerator()
    cfg = gen.config

    print("======================================================")
    print("🔑 CẤU HÌNH ĐẤU NỐI API KEY SINH CAPTION TỰ ĐỘNG (AI)")
    print("======================================================")
    print(f"Nhà cung cấp hiện tại : {cfg.get('provider')}")
    print(f"Model hiện tại        : {cfg.get('model')}")
    current_key = cfg.get('api_key', '')
    masked_key = (current_key[:6] + "..." + current_key[-4:]) if len(current_key) > 10 else ("(Chưa cấu hình)" if not current_key else current_key)
    print(f"API Key hiện tại      : {masked_key}")
    print("======================================================")
    print("[1] Google Gemini API (Khuyên dùng - Miễn phí, tốc độ cao)")
    print("[2] OpenAI API (ChatGPT / GPT-4o-mini)")
    print("[3] DeepSeek API (Siêu rẻ, thông minh)")
    print("[4] Groq / OpenRouter / Custom OpenAI endpoint")
    print("[5] Test thử sinh caption với API Key hiện tại")
    print("[0] Quay lại")
    print("======================================================")

    choice = input("👉 Chọn nhà cung cấp API (0-5): ").strip()

    if choice == "1":
        key = input("👉 Nhập Gemini API Key (lấy miễn phí tại aistudio.google.com): ").strip()
        if key:
            model = input("Nhập Model (nhấn Enter để dùng mặc định 'gemini-2.5-flash'): ").strip() or "gemini-2.5-flash"
            gen.set_api_key("gemini", key, model)

    elif choice == "2":
        key = input("👉 Nhập OpenAI API Key: ").strip()
        if key:
            model = input("Nhập Model (nhấn Enter để dùng 'gpt-4o-mini'): ").strip() or "gpt-4o-mini"
            gen.set_api_key("openai", key, model)

    elif choice == "3":
        key = input("👉 Nhập DeepSeek API Key: ").strip()
        if key:
            model = input("Nhập Model (nhấn Enter để dùng 'deepseek-chat'): ").strip() or "deepseek-chat"
            gen.set_api_key("deepseek", key, model)

    elif choice == "4":
        prov = input("Nhập tên dịch vụ (groq / openrouter / custom): ").strip().lower() or "custom"
        key = input("👉 Nhập API Key: ").strip()
        base_url = input("Nhập Base URL (vd: https://api.groq.com/openai/v1): ").strip()
        model = input("Nhập tên Model: ").strip()
        if key:
            gen.config["base_url"] = base_url
            gen.set_api_key(prov, key, model)

    elif choice == "5":
        topic = input("Nhập chủ đề video muốn test: ").strip() or "Mẹo sống khỏe mỗi ngày"
        print(f"\n[*] Đang gọi AI API tạo caption cho chủ đề '{topic}'...")
        cap = gen.generate_caption(topic)
        print("\n" + "=" * 50)
        print("🎬 CAPTION ĐƯỢC TẠO RA:")
        print(cap)
        print("=" * 50 + "\n")


if __name__ == "__main__":
    configure_interactive()
