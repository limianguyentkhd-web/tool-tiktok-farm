"""
Công cụ kiểm tra kết nối mạng (Internet, Ping, WiFi, IP) trên toàn bộ dàn máy Android.
Hỗ trợ tự động nhận diện thiết bị và xuất bảng báo cáo trạng thái chi tiết.
"""

import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

# Cấu hình encoding utf-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def run_adb(cmd: list) -> str:
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.stdout.decode("utf-8", errors="replace")


def get_adb_devices() -> List[tuple]:
    """Tìm thiết bị trên cả port mặc định 5037 và port 5038 của Xiaowei."""
    for port in ["5037", "5038"]:
        cmd = ["adb", "-P", port, "devices"] if port != "5037" else ["adb", "devices"]
        out = run_adb(cmd)
        devs = []
        for line in out.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devs.append((parts[0], port))
        if devs:
            return devs
    return []


def check_device_network(serial: str, port: str) -> Dict[str, str]:
    base = ["adb", "-P", port, "-s", serial] if port != "5037" else ["adb", "-s", serial]
    
    # 1. Kiểm tra SSID WiFi
    wifi_info = run_adb(base + ["shell", "dumpsys wifi | grep mWifiInfo"])
    ssid = "Không có"
    if "SSID:" in wifi_info:
        for part in wifi_info.split(","):
            if "SSID:" in part:
                clean_ssid = part.split("SSID:")[1].strip().replace('"', '')
                if clean_ssid and clean_ssid != "<unknown ssid>":
                    ssid = clean_ssid
                break

    # 2. Ping Google DNS (8.8.8.8)
    ping_ip = run_adb(base + ["shell", "ping -c 1 -W 2 8.8.8.8"])
    has_ip_net = ("1 packets transmitted, 1" in ping_ip) or ("1 received" in ping_ip)

    # 3. Ping tiktok.com (kiểm tra DNS + Internet ra ngoài)
    ping_dns = run_adb(base + ["shell", "ping -c 1 -W 2 tiktok.com"])
    has_dns_net = ("1 packets transmitted, 1" in ping_dns) or ("1 received" in ping_dns)

    # 4. Lấy IP nội bộ
    ip_out = run_adb(base + ["shell", "ip route get 8.8.8.8"])
    local_ip = "Chưa có IP"
    if "src" in ip_out:
        tokens = ip_out.split()
        if "src" in tokens:
            idx = tokens.index("src")
            if idx + 1 < len(tokens):
                local_ip = tokens[idx + 1]

    # Đánh giá trạng thái
    if has_dns_net:
        status = "INTERNET TỐT ✅"
    elif has_ip_net:
        status = "LỖI DNS ⚠️"
    else:
        status = "MẤT MẠNG ❌"

    return {
        "serial": serial,
        "ssid": ssid,
        "local_ip": local_ip,
        "status": status
    }


def main():
    devices = get_adb_devices()
    if not devices:
        print("[-] Không tìm thấy thiết bị ADB nào đang kết nối!")
        return

    print("=" * 80)
    print(f"📡 ĐANG KIỂM TRA MẠNG INTERNET TRÊN {len(devices)} THIẾT BỊ...")
    print("=" * 80)

    results = []
    with ThreadPoolExecutor(max_workers=min(len(devices), 17)) as executor:
        futures = [executor.submit(check_device_network, dev, port) for dev, port in devices]
        for f in futures:
            results.append(f.result())

    # In bảng kết quả
    print(f"{'STT':<4} | {'SERIAL':<20} | {'WIFI SSID':<18} | {'IP NỘI BỘ':<16} | {'TRẠNG THÁI'}")
    print("-" * 80)
    for idx, r in enumerate(results, 1):
        print(f"{idx:<4} | {r['serial']:<20} | {r['ssid']:<18} | {r['local_ip']:<16} | {r['status']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
