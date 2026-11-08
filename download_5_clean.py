import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

video_ids = [
    ('may1', '7697173178645603803'),
    ('may2', '7690745570076825050'),
    ('may3', '7700576071301859226'),
    ('may4', '7700452193515029746'),
    ('may5', '7700174739202113458')
]

raw_out_dir = r"d:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids"
os.makedirs(raw_out_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/'
}

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for tag, vid_id in video_ids:
        print(f"\n[*] Đang lấy video cho {tag} (ID: {vid_id})...")
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        
        found_url = []
        def on_req(req):
            u = req.url
            if any(k in u for k in ['zjcdn.com', 'douyinvod.com', 'byteeffectser.com']):
                if 'video/tos' in u or 'mime_type=video' in u or '.mp4' in u:
                    found_url.append(u)

        page.on('request', on_req)
        try:
            page.goto(f"https://www.douyin.com/video/{vid_id}", timeout=20000)
        except Exception:
            pass
        
        # Đợi tối đa 5s để video stream xuất hiện
        for _ in range(5):
            if found_url:
                break
            time.sleep(1)
            
        context.close()
        
        if found_url:
            stream_url = found_url[0]
            print(f"[+] Tìm thấy stream URL: {stream_url[:80]}...")
            out_file = os.path.join(raw_out_dir, f"{tag}_{vid_id}.mp4")
            try:
                r = requests.get(stream_url, headers=headers, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(out_file, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    sz_mb = os.path.getsize(out_file) / (1024*1024)
                    print(f"[+] ✅ {tag} tải thành công: {sz_mb:.2f} MB")
                    results.append((tag, out_file))
                else:
                    print(f"[-] HTTP {r.status_code}")
            except Exception as e:
                print(f"[-] Lỗi download: {e}")
        else:
            print(f"[-] Không bắt được stream cho {tag}")

    browser.close()

print(f"\n========================================================")
print(f"🎉 TỔNG KẾT: Đã tải được {len(results)}/5 video!")
for tag, path in results:
    print(f" - {tag}: {path} ({os.path.getsize(path)} bytes)")
print(f"========================================================")
