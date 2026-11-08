import urllib.request
import re

url = "https://theappninjas.com/download/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
    links = [m.group(1) for m in re.finditer(r'href=["\'](https?://[^"\'>]+\.apk)["\']', html, re.I)]
    print("Links:", links)
    # Tìm link arm64
    arm64_link = next((l for l in links if "arm64" in l.lower()), links[0] if links else None)
    if arm64_link:
        print("Tải arm64:", arm64_link)
        urllib.request.urlretrieve(arm64_link, r"D:\TOOL TIKTOK\GPS_JoyStick.apk")
        print("Tải thành công!")
except Exception as e:
    print("Lỗi:", e)
