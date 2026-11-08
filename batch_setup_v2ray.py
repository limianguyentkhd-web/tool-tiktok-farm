# -*- coding: utf-8 -*-
"""
Script nạp 5 proxy vào 5 máy qua v2rayNG tự động
Tuyệt đối không can thiệp máy mẫu (ce031713dba2c72101 trên port 5038)
"""
import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

DEVICES_PROXIES = [
    {
        "id": 1,
        "serial": "9889da304447393259",
        "name": "Proxy_1",
        "ip": "160.250.185.49",
        "port": "14102",
        "user": "ntnKhj",
        "pass": "oExYql",
        "already_done": True
    },
    {
        "id": 2,
        "serial": "988a17344c564b5657",
        "name": "Proxy_2",
        "ip": "160.250.166.242",
        "port": "22393",
        "user": "ntnKhj",
        "pass": "oExYql",
        "already_done": False
    },
    {
        "id": 3,
        "serial": "ce01182188dbdcee0c",
        "name": "Proxy_3",
        "ip": "160.250.183.232",
        "port": "30546",
        "user": "ntnKhj",
        "pass": "oExYql",
        "already_done": False
    },
    {
        "id": 4,
        "serial": "ce011821c38b263b05",
        "name": "Proxy_4",
        "ip": "160.30.191.96",
        "port": "18817",
        "user": "ntnKhj",
        "pass": "oExYql",
        "already_done": False
    },
    {
        "id": 5,
        "serial": "ce011821c45dc4060c",
        "name": "Proxy_5",
        "ip": "157.15.38.228",
        "port": "30096",
        "user": "ntnKhj",
        "pass": "oExYql",
        "already_done": False
    }
]

def adb_shell(serial, cmd):
    res = subprocess.run(["adb", "-s", serial, "shell", cmd], capture_output=True, text=True)
    return res.stdout.strip()

def setup_single_device(item):
    serial = item["serial"]
    name = item["name"]
    ip = item["ip"]
    port = item["port"]
    user = item["user"]
    pwd = item["pass"]
    
    print(f"\n==================================================")
    print(f"[*] Bắt đầu nạp {name} ({ip}:{port}) vào máy {serial}")
    print(f"==================================================")
    
    # 1. Cố định portrait
    adb_shell(serial, "settings put system accelerometer_rotation 0")
    adb_shell(serial, "settings put system user_rotation 0")
    
    # 2. Bật v2rayNG
    adb_shell(serial, "am force-stop com.v2ray.ang")
    time.sleep(0.5)
    adb_shell(serial, "am start -n com.v2ray.ang/com.v2ray.ang.ui.MainActivity")
    time.sleep(2)
    
    # 3. Bấm dấu +
    print("[1/6] Mở menu thêm cấu hình (+)...")
    adb_shell(serial, "input tap 911 136")
    time.sleep(1)
    
    # 4. Chọn Type manually[HTTP]
    print("[2/6] Chọn Type manually[HTTP]...")
    adb_shell(serial, "input tap 500 1018")
    time.sleep(1.5)
    
    # 5. Điền thông tin
    print(f"[3/6] Nhập thông số proxy: Remarks={name}, IP={ip}, Port={port}...")
    # Remarks
    adb_shell(serial, "input tap 500 460")
    time.sleep(0.4)
    adb_shell(serial, f"input text {name}")
    
    # Address (IP)
    adb_shell(serial, "input tap 500 670")
    time.sleep(0.4)
    adb_shell(serial, f"input text {ip}")
    
    # Port
    adb_shell(serial, "input tap 500 880")
    time.sleep(0.4)
    for _ in range(5):
        adb_shell(serial, "input keyevent 67")
    adb_shell(serial, f"input text {port}")
    
    # User
    adb_shell(serial, "input tap 500 1090")
    time.sleep(0.4)
    adb_shell(serial, f"input text {user}")
    
    # Password
    adb_shell(serial, "input tap 500 1300")
    time.sleep(0.4)
    adb_shell(serial, f"input text {pwd}")
    
    # 6. Lưu cấu hình
    print("[4/6] Lưu cấu hình...")
    adb_shell(serial, "input tap 1016 136")
    time.sleep(2)
    
    # 7. Bật kết nối
    print("[5/6] Bấm kết nối VPN...")
    adb_shell(serial, "input tap 964 1925")
    time.sleep(1.5)
    
    # Kiểm tra xem có popup ConfirmDialog không
    focus = adb_shell(serial, "dumpsys window | grep mCurrentFocus")
    if "ConfirmDialog" in focus or "vpndialogs" in focus:
        print("[!] Phát hiện popup cấp quyền VPN, bấm OK...")
        adb_shell(serial, "input tap 781 1951")
        time.sleep(1.5)
    else:
        # Nhấp nhẹ thử phòng hờ
        adb_shell(serial, "input tap 781 1951")
        time.sleep(1)
        
    # 8. Test kết nối
    print("[6/6] Kiểm tra ping & IP...")
    adb_shell(serial, "input tap 300 2060")
    time.sleep(3)
    
    # Chụp ảnh xác nhận
    local_img = f"C:/Users/Admin/.gemini/antigravity/brain/612f5864-e377-4aa9-a143-bf7f13dcbded/v2ray_{name}.png"
    adb_shell(serial, f"screencap -p /sdcard/v2ray_{name}.png")
    subprocess.run(["adb", "-s", serial, "pull", f"/sdcard/v2ray_{name}.png", local_img], capture_output=True)
    print(f"[✓] Đã lưu ảnh kiểm tra: {local_img}")
    return local_img

def main():
    print("=== TIẾN HÀNH NẠP 5 PROXY CHO 5 MÁY ĐIỆN THOẠI KHÁC NHAU ===")
    for item in DEVICES_PROXIES:
        if item.get("already_done"):
            print(f"[+] Máy {item['id']} ({item['serial']}) đã hoàn thành kết nối trước đó: {item['ip']}")
            continue
        try:
            setup_single_device(item)
            time.sleep(2)
        except Exception as e:
            print(f"[-] Lỗi trên máy {item['serial']}: {e}")

if __name__ == "__main__":
    main()
