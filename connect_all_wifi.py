"""
Script tự động kết nối WiFi 'Limia Media' đồng loạt cho TOÀN BỘ 17 thiết bị Android.
Sử dụng quyền Root (KernelSU) để cấp cấu hình mạng chuẩn xác và kiểm tra Internet ngay lập tức.
"""

import os
import sys
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SSID = "Limia Media"
PASSWORD = "123123123"


def get_connected_devices() -> Tuple[List[str], str]:
    """Tìm danh sách máy trên port 5037 hoặc 5038."""
    for p in ["5037", "5038"]:
        cmd = ["adb", "-P", p, "devices"] if p != "5037" else ["adb", "devices"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        devs = []
        for line in res.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devs.append(parts[0])
        if devs:
            return devs, p
    return [], "5037"


def connect_device_wifi(serial: str, port: str) -> dict:
    base = ["adb", "-P", port, "-s", serial] if port != "5037" else ["adb", "-s", serial]
    
    # 1. Bật WiFi
    subprocess.run(base + ["shell", "su", "-c", "svc wifi enable"], capture_output=True)
    
    # 2. Gửi lệnh kết nối WiFi qua su pipe
    connect_cmd = f"cmd -w wifi connect-network '{SSID}' wpa2 {PASSWORD}\n"
    p = subprocess.Popen(base + ["shell", "su"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p.communicate(input=connect_cmd)

    # 3. Đợi 5 giây để thiết bị nhận IP từ Router
    time.sleep(5)

    # 4. Kiểm tra IP và Ping
    ip_out = subprocess.run(base + ["shell", "ip", "route", "get", "8.8.8.8"], capture_output=True, text=True).stdout
    local_ip = "Chưa nhận IP"
    if "src" in ip_out:
        tokens = ip_out.split()
        if "src" in tokens:
            idx = tokens.index("src")
            if idx + 1 < len(tokens):
                local_ip = tokens[idx + 1]

    ping_res = subprocess.run(base + ["shell", "ping", "-c", "1", "-W", "2", "8.8.8.8"], capture_output=True, text=True).stdout
    is_ok = ("1 packets transmitted, 1" in ping_res) or ("1 received" in ping_res)

    status = "INTERNET TỐT (OK) ✅" if is_ok else "ĐANG KẾT NỐI... ⏳"

    return {
        "serial": serial,
        "ip": local_ip,
        "status": status
    }


def main():
    devices, port = get_connected_devices()
    if not devices:
        print("[-] Không tìm thấy thiết bị ADB nào!")
        return

    print("=" * 70)
    print(f"📡 ĐANG KẾT NỐI WIFI '{SSID}' CHO {len(devices)} THIẾT BỊ...")
    print("=" * 70)

    results = []
    with ThreadPoolExecutor(max_workers=min(len(devices), 17)) as executor:
        futures = [executor.submit(connect_device_wifi, dev, port) for dev in devices]
        for f in futures:
            results.append(f.result())

    print(f"\n{'STT':<4} | {'SERIAL':<20} | {'IP WIFI NHẬN ĐƯỢC':<18} | {'TRẠNG THÁI'}")
    print("-" * 70)
    for idx, r in enumerate(results, 1):
        print(f"{idx:<4} | {r['serial']:<20} | {r['ip']:<18} | {r['status']}")
    print("=" * 70)
    print("🎉 HOÀN TẤT CẤU HÌNH WIFI CHO TOÀN BỘ MÁY!")


if __name__ == "__main__":
    main()
