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
raw_dir = r'd:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids'
os.makedirs(raw_dir, exist_ok=True)

video_items = []

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
                for a in aweme_list:
                    aid = a.get('aweme_id')
                    desc = a.get('desc', '')
                    play_urls = a.get('video', {}).get('play_addr', {}).get('url_list', [])
                    if aid and play_urls:
                        # Tránh trùng video đã tải hôm qua (7686548472787736934)
                        if aid != '7686548472787736934':
                            video_items.append({
                                'id': aid,
                                'desc': desc,
                                'urls': play_urls
                            })
                            print(f"[+] Thu thập video {len(video_items)}: ID {aid} - {desc[:35]}")
            except Exception as e:
                pass

    page.on('response', handle_response)
    print(f"[*] Đang kết nối kênh Douyin: {url}")
    try:
        page.goto(url, wait_until='networkidle', timeout=30000)
    except Exception as e:
        print(f"[*] Navigation note: {e}")

    browser.close()

print(f"\n[+] Tổng số video mới thu thập được: {len(video_items)}")

# Tải 5 video đầu tiên
downloaded_paths = []
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/'
}

for i, item in enumerate(video_items[:5], 1):
    aid = item['id']
    desc = item['desc']
    clean_title = re.sub(r'[^\w\-]', '_', desc)[:30]
    out_name = f"may{i}_raw_{aid}_{clean_title}.mp4"
    out_file = os.path.join(raw_dir, out_name)
    
    print(f"\n[{i}/5] Đang tải video {aid}: '{desc[:30]}'")
    download_success = False
    for v_url in item['urls']:
        try:
            r = requests.get(v_url, headers=headers, stream=True, timeout=30)
            if r.status_code == 200:
                with open(out_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                sz_mb = os.path.getsize(out_file) / (1024 * 1024)
                print(f"    ✅ Tải thành công! Dung lượng: {sz_mb:.2f} MB -> {out_name}")
                downloaded_paths.append(out_file)
                download_success = True
                break
        except Exception as e:
            print(f"    [-] Lỗi link {v_url[:40]}: {e}")
            
    if not download_success:
        print(f"    ❌ Thất bại tải video {aid}")

print(f"\n========================================================")
print(f"🎉 ĐÃ TẢI THÀNH CÔNG {len(downloaded_paths)}/5 VIDEO MỚI VỀ: {raw_dir}")
print(f"========================================================")
