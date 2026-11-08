import json
import os
import re
import sys
import time
import requests
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

url = 'https://www.douyin.com/user/MS4wLjABAAAAWB1D0tWinHezo1D8ymVa0ez-JXlw2cNQoDZv9Pyo46elLuYhrYSW0QM3TVHPeEhj'
out_json = r'd:\TOOL TIKTOK\douyin_channel_videos.json'
raw_dir = r'd:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids'
os.makedirs(raw_dir, exist_ok=True)

all_aweme = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    def handle_response(response):
        if '/aweme/post/' in response.url or '/web/aweme/post' in response.url:
            try:
                data = response.json()
                aweme_list = data.get('aweme_list', [])
                if aweme_list:
                    print(f'[*] Nhận API response với {len(aweme_list)} video!')
                    for a in aweme_list:
                        all_aweme.append(a)
            except Exception as e:
                pass

    page.on('response', handle_response)
    print(f'[*] Đang mở kênh Douyin: {url}')
    try:
        # Dùng wait_until='domcontentloaded' để không bị timeout bởi video streaming nền
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        time.sleep(5)
    except Exception as e:
        print(f'[*] goto warning: {e}')

    browser.close()

print(f'[+] Tổng số video bóc tách được: {len(all_aweme)}')
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(all_aweme, f, ensure_ascii=False, indent=2)

print(f'[+] Đã lưu danh sách video vào: {out_json}')
