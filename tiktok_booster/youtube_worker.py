# -*- coding: utf-8 -*-
"""
YouTube Ultra-Lightweight Headless HTTP Worker
----------------------------------------------
- Điều khiển Chromium không đầu (Headless Playwright).
- Chặn 100% hình ảnh, CSS, fonts, banner để giảm 85% RAM/CPU.
- Tự động nhận diện YouTube Shorts (6s-12s) hoặc Video dài (35s-50s vượt luật 30s).
- Giả lập nguồn traffic uy tín (Google Search, Facebook, Twitter, Zalo).
- Tải stream googlevideo thật và gửi đầy đủ Playback Heartbeat (watchtime ping).
- Hỗ trợ xoay vòng Proxy (Rotating Proxy) chống giới hạn 3-5 view/IP của YouTube.
"""

import sys
import os
import time
import random
import re
import argparse
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

REFERRERS = [
    "https://www.google.com/",
    "https://www.google.com.vn/",
    "https://l.facebook.com/",
    "https://t.co/",
    "https://zalo.me/",
    "https://www.youtube.com/",
]

BLOCKED_RESOURCE_TYPES = {"image", "stylesheet", "font", "media_audio"}
BLOCKED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".css"
}

def load_proxies(proxy_file: str = "proxies.txt") -> list:
    """Đọc danh sách proxy từ file"""
    proxies = []
    candidates = [
        proxy_file,
        os.path.join(os.path.dirname(__file__), proxy_file),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), proxy_file),
    ]
    target_path = None
    for c in candidates:
        if os.path.exists(c):
            target_path = c
            break

    if target_path:
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Match IP:PORT:USER:PASS or IP:PORT
                    parts = line.split(':')
                    if len(parts) == 4:
                        proxies.append({
                            'server': f"http://{parts[0]}:{parts[1]}",
                            'username': parts[2],
                            'password': parts[3]
                        })
                    elif len(parts) == 2:
                        proxies.append({'server': f"http://{parts[0]}:{parts[1]}"})
                    elif line.startswith('http'):
                        proxies.append({'server': line})
    return proxies

class YouTubeHeadlessWorker:
    def __init__(self, video_url: str, min_watch: int = None, max_watch: int = None, proxy_list: list = None):
        self.video_url = video_url.strip()
        self.is_shorts = '/shorts/' in self.video_url
        
        # Tự động set thời gian xem tối ưu
        if min_watch is None or max_watch is None:
            if self.is_shorts:
                self.min_watch = min_watch or 7
                self.max_watch = max_watch or 12
            else:
                self.min_watch = min_watch or 35
                self.max_watch = max_watch or 48
        else:
            self.min_watch = min_watch
            self.max_watch = max_watch

        self.proxy_list = proxy_list or []
        self.proxy_idx = 0
        self.playwright = None

    def get_next_proxy(self):
        """Lấy proxy xoay vòng"""
        if not self.proxy_list:
            return None
        p = self.proxy_list[self.proxy_idx % len(self.proxy_list)]
        self.proxy_idx += 1
        return p

    def run_single_view(self, view_index: int) -> bool:
        """Thực hiện 1 lượt xem YouTube độc lập kèm đổi IP / Session"""
        current_proxy = self.get_next_proxy()
        proxy_info = current_proxy['server'] if current_proxy else "IP Gốc"

        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--mute-audio',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-background-timer-throttling',
        ]
        
        launch_opts = {'headless': True, 'args': launch_args}
        if current_proxy:
            launch_opts['proxy'] = current_proxy

        browser = None
        success = False
        watch_seconds = random.randint(self.min_watch, self.max_watch)

        try:
            browser = self.playwright.chromium.launch(**launch_opts)
            ref = random.choice(REFERRERS)
            ua = random.choice(USER_AGENTS)

            context = browser.new_context(
                user_agent=ua,
                viewport={"width": 1280, "height": 800},
                locale="vi-VN",
                timezone_id="Asia/Ho_Chi_Minh",
                extra_http_headers={"Referer": ref}
            )
            page = context.new_page()

            stream_chunks = 0
            heartbeats = 0

            # Bộ lọc tài nguyên siêu nhẹ
            def handle_route(route):
                req = route.request
                u_lower = req.url.lower()
                if req.resource_type in BLOCKED_RESOURCE_TYPES or any(u_lower.endswith(ext) for ext in BLOCKED_EXTENSIONS):
                    route.abort()
                else:
                    route.continue_()

            def handle_request(req):
                nonlocal stream_chunks, heartbeats
                u = req.url
                if 'googlevideo.com' in u:
                    stream_chunks += 1
                elif 'stats/watchtime' in u or 'stats/playback' in u:
                    heartbeats += 1

            page.route("**/*", handle_route)
            page.on("request", handle_request)

            # 1. Truy cập video
            page.goto(self.video_url, timeout=25000, wait_until="networkidle")

            # 2. Xử lý popup chấp thuận (Consent) nếu có
            try:
                btn = page.query_selector('button[aria-label*="Accept"], button[aria-label*="Agree"], button[aria-label*="Đồng ý"]')
                if btn:
                    btn.click()
            except:
                pass

            # 3. Kích hoạt phát video
            page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v) {
                        v.muted = true;
                        if (v.paused) v.play();
                    }
                }
            """)

            # 4. Giữ thời lượng xem (Watch time)
            time.sleep(watch_seconds)

            cur_time = page.evaluate("() => document.querySelector('video')?.currentTime || 0")
            is_paused = page.evaluate("() => document.querySelector('video')?.paused")

            if stream_chunks > 0 and cur_time > 2.0:
                success = True
                print(f"[{time.strftime('%H:%M:%S')}] View #{view_index:03d}: [Thành công] TimePlayed={cur_time:.1f}s/{watch_seconds}s | Chunks={stream_chunks} | Heartbeats={heartbeats} | Proxy={proxy_info}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] View #{view_index:03d}: [Chưa hoàn tất] TimePlayed={cur_time:.1f}s | Chunks={stream_chunks} | Paused={is_paused}")

            context.close()

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] View #{view_index:03d}: [Lỗi] {str(e)[:80]}")

        finally:
            if browser:
                browser.close()

        return success

    def run_batch(self, total_views: int, min_delay: int = 3, max_delay: int = 7):
        """Chạy chuỗi lượt xem YouTube"""
        v_type = "YouTube Shorts (Tối ưu 6s-12s)" if self.is_shorts else "YouTube Video Dài (Vượt luật >30s)"
        print("\n" + "=" * 68)
        print("🚀 BẮT ĐẦU CHẠY YOUTUBE HEADLESS HTTP WORKER")
        print(f"🎯 Target URL    : {self.video_url}")
        print(f"📂 Phân loại     : {v_type}")
        print(f"📊 Mục tiêu      : {total_views} lượt xem")
        print(f"⏱️ Watch Time    : {self.min_watch}s - {self.max_watch}s / lượt")
        print(f"⏳ Delay nghỉ     : {min_delay}s - {max_delay}s")
        print(f"🌐 Proxy Pool    : {len(self.proxy_list)} proxy sẵn sàng xoay vòng")
        print("=" * 68 + "\n")

        self.playwright = sync_playwright().start()
        success_count = 0

        try:
            for i in range(1, total_views + 1):
                ok = self.run_single_view(i)
                if ok:
                    success_count += 1
                
                if i < total_views:
                    delay = random.randint(min_delay, max_delay)
                    time.sleep(delay)

        except KeyboardInterrupt:
            print("\n⚠️ Người dùng bấm tạm dừng tiến trình!")
        finally:
            if self.playwright:
                self.playwright.stop()
            print("\n" + "=" * 68)
            print(f"🏁 KẾT THÚC TIẾN TRÌNH: {success_count}/{total_views} lượt xem hợp lệ.")
            print("=" * 68)

def main():
    parser = argparse.ArgumentParser(description="YouTube Headless HTTP Worker")
    parser.add_argument("--url", type=str, default="https://www.youtube.com/shorts/qk3pEXQ43aA", help="Link video YouTube / Shorts")
    parser.add_argument("--views", type=int, default=3, help="Số lượt xem cần bơm")
    parser.add_argument("--min-watch", type=int, default=None, help="Thời gian xem tối thiểu (mặc định tự nhận diện)")
    parser.add_argument("--max-watch", type=int, default=None, help="Thời gian xem tối đa (mặc định tự nhận diện)")
    parser.add_argument("--min-delay", type=int, default=3, help="Nghỉ tối thiểu giữa các view (giây)")
    parser.add_argument("--max-delay", type=int, default=7, help="Nghỉ tối đa giữa các view (giây)")
    parser.add_argument("--proxy", type=str, default=None, help="Proxy đơn lẻ (ví dụ: http://ip:port)")
    parser.add_argument("--proxy-file", type=str, default="proxies.txt", help="File danh sách proxy xoay vòng")

    args = parser.parse_args()

    # Load proxy pool
    proxies = []
    if args.proxy:
        proxies = [{'server': args.proxy}]
    else:
        proxies = load_proxies(args.proxy_file)

    worker = YouTubeHeadlessWorker(
        video_url=args.url,
        min_watch=args.min_watch,
        max_watch=args.max_watch,
        proxy_list=proxies
    )
    worker.run_batch(
        total_views=args.views,
        min_delay=args.min_delay,
        max_delay=args.max_delay
    )

if __name__ == "__main__":
    main()
