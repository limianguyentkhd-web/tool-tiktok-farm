import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

url = 'https://www.douyin.com/user/MS4wLjABAAAAWB1D0tWinHezo1D8ymVa0ez-JXlw2cNQoDZv9Pyo46elLuYhrYSW0QM3TVHPeEhj'
out_path = r'd:\TOOL TIKTOK\douyin_captured_videos.json'

all_videos = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    def handle_response(response):
        if '/aweme/post' in response.url or '/web/aweme/post' in response.url:
            try:
                data = response.json()
                aweme_list = data.get('aweme_list', [])
                if aweme_list:
                    print(f"[+] Bắt được {len(aweme_list)} video từ API!")
                    for item in aweme_list:
                        all_videos.append(item)
                    # Ghi ngay lập tức ra file
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(all_videos, f, ensure_ascii=False, indent=2)
                    print(f"[+] Đã ghi file {out_path} thành công!")
            except Exception as e:
                print(f"[-] Lỗi parse response: {e}")

    page.on('response', handle_response)
    print('[*] Đang tải trang kênh với networkidle...')
    try:
        page.goto(url, wait_until='networkidle', timeout=35000)
    except Exception as e:
        print(f'[*] Page goto timeout/finished: {e}')

    time.sleep(2)
    browser.close()

print(f'Done! Total videos saved: {len(all_videos)}')
