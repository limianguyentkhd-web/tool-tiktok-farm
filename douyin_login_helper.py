"""
Công cụ Hỗ Trợ Đăng Nhập Douyin Tự Động (Douyin Login & Cookie Extractor)
Hỗ trợ 2 cách:
1. Tự động bật cửa sổ trình duyệt để quét mã QR (đã fix lỗi timeout, tải ngay trong 2s).
2. Dán trực tiếp chuỗi Cookie từ Chrome đã đăng nhập sẵn.
"""

import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "douyin_cookies.json")
COOKIE_TXT = os.path.join(os.path.dirname(__file__), "douyin_cookie.txt")


def save_cookie_string(cookie_str: str):
    """Lưu chuỗi cookie (dạng header k1=v1; k2=v2) thành file json và txt."""
    cookie_str = cookie_str.strip(' "\'')
    if not cookie_str:
        print("[-] Chuỗi cookie rỗng!")
        return False

    with open(COOKIE_TXT, "w", encoding="utf-8") as f:
        f.write(cookie_str)

    cookie_list = []
    for item in cookie_str.split(";"):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            cookie_list.append({"name": k.strip(), "value": v.strip(), "domain": ".douyin.com", "path": "/"})

    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(cookie_list, f, ensure_ascii=False, indent=2)

    print("\n========================================================")
    print(f"🎉 ĐÃ LƯU THÀNH CÔNG {len(cookie_list)} COOKIE DOUYIN!")
    print(f"📂 File lưu: {COOKIE_FILE}")
    print("========================================================")
    return True


def login_via_qr():
    """Bật cửa sổ Chromium để người dùng quét mã QR (dùng wait_until='commit' chống timeout)."""
    print("\n[*] Đang bật trình duyệt trên màn hình của bạn...")
    print("[*] Vui lòng mở ứng dụng Douyin trên điện thoại -> Sẵn sàng Quét mã QR...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--no-sandbox"
            ]
        )
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("[*] Đang kết nối máy chủ Douyin (không chờ tải video nền)...")
        try:
            # wait_until='commit': Nhận phản hồi là mở ngay, không bị treo timeout
            page.goto("https://www.douyin.com", wait_until="commit", timeout=30000)
        except Exception as e:
            print(f"[!] Chú ý: {e}")

        print("\n👉 CỬA SỔ DOUYIN ĐÃ HIỆN TRÊN MÀN HÌNH!")
        print("👉 NẾU CHƯA THẤY MÃ QR, HÃY BẤM NÚT 'ĐĂNG NHẬP' MÀU ĐỎ TRÊN GÓC PHẢI MÀN HÌNH.")
        print("[*] Tool đang theo dõi ngầm, ngay khi bạn quét xong tool sẽ tự lưu Cookie và đóng lại...")

        logged_in = False
        start_time = time.time()
        while time.time() - start_time < 180:
            try:
                cookies = context.cookies()
                cookie_dict = {c["name"]: c["value"] for c in cookies}

                # Nhận diện khi đã đăng nhập
                if any(k in cookie_dict for k in ["sessionid", "sessionid_ss", "sid_guard", "passport_auth_status"]):
                    logged_in = True
                    print("\n========================================================")
                    print("🎉 CHÚC MỪNG! ĐÃ PHÁT HIỆN BẠN ĐĂNG NHẬP THÀNH CÔNG!")
                    print("========================================================")

                    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)

                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    with open(COOKIE_TXT, "w", encoding="utf-8") as f:
                        f.write(cookie_str)

                    print(f"[+] Đã lưu cấu hình Cookie vào: {COOKIE_FILE}")
                    print(f"[+] Mở khóa thành công quyền tải TOÀN BỘ video của kênh!")
                    time.sleep(2)
                    break
            except Exception:
                pass

            time.sleep(2)

        if not logged_in:
            print("[-] Hết thời gian chờ (180s) hoặc bạn đã tắt trình duyệt.")

        try:
            browser.close()
        except Exception:
            pass


def main():
    print("=================================================================")
    print("🔑 CÔNG CỤ ĐĂNG NHẬP DOUYIN ĐỂ MỞ KHÓA TẢI SẠCH TOÀN BỘ KÊNH")
    print("=================================================================")
    print("[1] 📷 Bật cửa sổ Quét Mã QR (Tự động lưu sau khi quét)")
    print("[2] 📋 Dán chuỗi Cookie từ Chrome (Nếu đã đăng nhập trên Chrome)")
    print("[0] Thoát")
    print("=================================================================")

    choice = input("👉 Nhập lựa chọn (1/2): ").strip()

    if choice == "1":
        login_via_qr()
    elif choice == "2":
        print("\nCách lấy Cookie từ Chrome đang mở của bạn:")
        print("1. Tại tab Douyin trên Chrome, nhấn F12 -> chọn thẻ 'Console'")
        print("2. Gõ lệnh: copy(document.cookie) rồi nhấn Enter (hoặc copy từ thẻ Application/Network)")
        print("3. Dán (Ctrl+V) vào đây:")
        c_str = input("👉 Dán Cookie vào đây: ").strip()
        if c_str:
            save_cookie_string(c_str)


if __name__ == "__main__":
    main()
