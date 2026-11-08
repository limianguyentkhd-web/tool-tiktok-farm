import time
import subprocess

SERIAL = "9889da304447393259"
PORT = "5037"

def adb(args):
    cmd = ["adb", "-s", SERIAL] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

def setup_http_proxy():
    # 1. Điền remarks
    adb(["shell", "input", "tap", "500", "460"])
    time.sleep(0.5)
    adb(["shell", "input", "text", "Proxy_1"])
    time.sleep(0.5)

    # 2. Điền address (160.250.185.49)
    adb(["shell", "input", "tap", "500", "670"])
    time.sleep(0.5)
    adb(["shell", "input", "text", "160.250.185.49"])
    time.sleep(0.5)

    # 3. Điền port (14102)
    adb(["shell", "input", "tap", "500", "880"])
    time.sleep(0.5)
    # Xoá 443 mặc định
    for _ in range(5):
        adb(["shell", "input", "keyevent", "67"])
    adb(["shell", "input", "text", "14102"])
    time.sleep(0.5)

    # 4. Điền User (ntnKhj)
    adb(["shell", "input", "tap", "500", "1090"])
    time.sleep(0.5)
    adb(["shell", "input", "text", "ntnKhj"])
    time.sleep(0.5)

    # 5. Điền Password (oExYql)
    adb(["shell", "input", "tap", "500", "1300"])
    time.sleep(0.5)
    adb(["shell", "input", "text", "oExYql"])
    time.sleep(0.5)

    # Đóng bàn phím
    adb(["shell", "input", "keyevent", "111"])
    time.sleep(0.8)

    # Bấm nút Lưu (Save configuration) ở góc trên bên phải [953,73][1080,199]
    adb(["shell", "input", "tap", "1016", "136"])
    time.sleep(2.0)

    # Bấm nút Kết Nối (Floating action button FAB) ở góc dưới [891,1852][1038,1999]
    print("[*] Bấm kết nối v2rayNG...")
    adb(["shell", "input", "tap", "964", "1925"])
    time.sleep(3.0)

    # Nếu có hộp thoại cấp quyền VPN của Android -> Bấm OK (thường ở góc dưới phải)
    adb(["shell", "input", "tap", "800", "1400"])
    adb(["shell", "input", "tap", "800", "1300"])
    adb(["shell", "input", "tap", "800", "1500"])

if __name__ == '__main__':
    setup_http_proxy()
