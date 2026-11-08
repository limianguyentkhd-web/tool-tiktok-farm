import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

url = 'https://www.douyin.com/user/MS4wLjABAAAAWB1D0tWinHezo1D8ymVa0ez-JXlw2cNQoDZv9Pyo46elLuYhrYSW0QM3TVHPeEhj'
out_path = r'd:\TOOL TIKTOK\douyin_raw_api.json'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    captured_data = []

    def on_response(response):
        if '/aweme/post' in response.url or '/web/aweme/post' in response.url:
            try:
                d = response.json()
                if 'aweme_list' in d:
                    captured_data.append(d)
                    print(f"[+] Nhận gói API: {len(d.get('aweme_list', []))} video!")
            except Exception:
                pass

    page.on('response', on_response)
    print(f"[*] Đang tải trang kênh Douyin...")
    try:
        page.goto(url, timeout=30000)
    except Exception as e:
        print(f"[*] Goto exception (ignored): {e}")

    # Chờ tối đa 15s để các request API hoàn tất
    for _ in range(15):
        if captured_data:
            break
        time.sleep(1)

    browser.close()

if captured_data:
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(captured_data[0], f, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu dữ liệu vào {out_path} thành công!")
else:
    print("[-] Không bắt được gói API.")
