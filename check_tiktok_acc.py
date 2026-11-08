import urllib.request
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

url = "https://www.tiktok.com/@nguyennminh256"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
try:
    html = urllib.request.urlopen(req, timeout=5).read().decode("utf-8")
    title = re.search(r"<title>(.*?)</title>", html)
    print("Page Title:", title.group(1) if title else "Không có title")
    if "Couldn't find this account" in html:
        print("Trạng thái: TÀI KHOẢN KHÔNG TỒN TẠI (ĐÃ BỊ XÓA HOẶC BỊ QUÉT BAN)")
    else:
        print("Trạng thái: Có dữ liệu trả về")
except Exception as e:
    print("Error:", e)
