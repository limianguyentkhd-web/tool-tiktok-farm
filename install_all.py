"""
Script tự động cài đặt APK bất kỳ (TikTok, v2rayNG, Proxy...) vào TOÀN BỘ các thiết bị Android đang kết nối.
Hỗ trợ đa luồng, tự nhận diện cổng ADB (5037 / 5038), tự cấp quyền (-g).
"""

import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def get_connected_devices() -> Tuple[List[str], str]:
    """Tự động tìm danh sách máy trên port 5037 hoặc 5038."""
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


def install_apk_on_device(serial: str, port: str, apk_path: str) -> None:
    cmd_base = ["adb", "-P", port, "-s", serial] if port != "5037" else ["adb", "-s", serial]
    apk_name = os.path.basename(apk_path)
    
    print(f"[*] [{serial}] Đang cài đặt {apk_name}...")
    res = subprocess.run(cmd_base + ["install", "-r", "-d", "-g", apk_path], capture_output=True, text=True)
    
    if "Success" in res.stdout:
        print(f"[+] [{serial}] CÀI ĐẶT THÀNH CÔNG! ✅")
    else:
        err = res.stderr.strip() or res.stdout.strip()
        print(f"[-] [{serial}] THẤT BẠI: {err} ❌")


def main(apk_path: str):
    if not os.path.isfile(apk_path):
        print(f"[-] Không tìm thấy file APK tại: {apk_path}")
        return

    devices, port = get_connected_devices()
    if not devices:
        print("[-] Không tìm thấy thiết bị ADB nào đang kết nối!")
        return

    print("=" * 65)
    print(f"🚀 Chuẩn bị cài đặt APK vào {len(devices)} thiết bị (Port ADB: {port}):")
    print(f"📦 File APK: {os.path.basename(apk_path)} ({os.path.getsize(apk_path) / 1024 / 1024:.1f} MB)")
    print("=" * 65)

    with ThreadPoolExecutor(max_workers=min(len(devices), 17)) as executor:
        futures = [executor.submit(install_apk_on_device, dev, port, apk_path) for dev in devices]
        for f in futures:
            f.result()

    print("\n🎉 ĐÃ HOÀN TẤT CÀI ĐẶT CHO TOÀN BỘ CÁC MÁY!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_apk = sys.argv[1]
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        apk_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith(".apk")]
        target_apk = apk_files[0] if apk_files else ""

    main(target_apk)
