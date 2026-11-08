import os
import re
import sys
import time
import requests
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

video_ids = [
    '7697173178645603803',
    '7690745570076825050',
    '7700576071301859226',
    '7700452193515029746',
    '7700174739202113458'
]

raw_out_dir = r"d:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids"
os.makedirs(raw_out_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/'
}

downloaded_files = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 720})

    for idx, vid_id in enumerate(video_ids, 1):
        target_url = f"https://www.douyin.com/video/{vid_id}"
        print(f"\n========================================================")
        print(f"[{idx}/5] Đang xử lý bóc tách video ID: {vid_id}...")
        print(f"🔗 URL: {target_url}")
        print(f"========================================================")

        captured = {'url': None}
        
        def on_req(request):
            u = request.url
            if ('zjcdn.com' in u or 'douyinvod.com' in u) and 'mime_type=video_mp4' in u:
                if not captured['url']:
                    captured['url'] = u

        page.on('request', on_req)
        try:
            page.goto(target_url, timeout=20000)
        except Exception:
            pass
        
        time.sleep(3)
        page.remove_listener('request', on_req)

        stream_url = captured['url']
        if stream_url:
            print(f"[+] Bắt được luồng stream gốc thành công!")
            out_file = os.path.join(raw_out_dir, f"raw_may{idx}_{vid_id}.mp4")
            try:
                r = requests.get(stream_url, headers=headers, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(out_file, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    sz_mb = os.path.getsize(out_file) / (1024*1024)
                    print(f"    ✅ Đã tải: {out_file} ({sz_mb:.2f} MB)")
                    downloaded_files.append((idx, vid_id, out_file))
                else:
                    print(f"    [-] Lỗi HTTP {r.status_code}")
            except Exception as e:
                print(f"    [-] Lỗi download: {e}")
        else:
            print(f"    [-] Không bắt được luồng stream cho {vid_id}")

    browser.close()

print(f"\n========================================================")
print(f"🎉 HOÀN TẤT! Đã tải thành công {len(downloaded_files)}/5 video raw khác nhau!")
for idx, vid_id, path in downloaded_files:
    print(f" - Máy {idx}: {path} ({os.path.getsize(path)} bytes)")
print(f"========================================================")
