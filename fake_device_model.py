"""
Script tự động Fake dòng máy (Device Spoofing) và tạo Android ID mới cho 17 thiết bị Android.
Sử dụng công cụ resetprop của KernelSU để nạp trực tiếp vào RAM/Kernel hệ điều hành mà không cần khởi động lại.
Rải 17 dòng Flagship Samsung cao cấp (S24 Ultra, S23 Ultra, S22 Ultra, Z Fold 5...)
"""

import os
import sys
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# 17 Profile Samsung cao cấp thực tế
PROFILES = [
    {"name": "Galaxy S24 Ultra", "model": "SM-S928B", "device": "e3q", "product": "e3qxxx"},
    {"name": "Galaxy S24+", "model": "SM-S926B", "device": "e2q", "product": "e2qxxx"},
    {"name": "Galaxy S24", "model": "SM-S921B", "device": "e1q", "product": "e1qxxx"},
    {"name": "Galaxy S23 Ultra", "model": "SM-S918B", "device": "dm3q", "product": "dm3qxxx"},
    {"name": "Galaxy S23+", "model": "SM-S916B", "device": "dm2q", "product": "dm2qxxx"},
    {"name": "Galaxy S23", "model": "SM-S911B", "device": "dm1q", "product": "dm1qxxx"},
    {"name": "Galaxy S22 Ultra", "model": "SM-S908B", "device": "b0q", "product": "b0qxxx"},
    {"name": "Galaxy S22+", "model": "SM-S906B", "device": "g0q", "product": "g0qxxx"},
    {"name": "Galaxy S22", "model": "SM-S901B", "device": "r0q", "product": "r0qxxx"},
    {"name": "Galaxy Z Fold 5", "model": "SM-F946B", "device": "q5q", "product": "q5qxxx"},
    {"name": "Galaxy Z Flip 5", "model": "SM-F731B", "device": "b5q", "product": "b5qxxx"},
    {"name": "Galaxy Z Fold 4", "model": "SM-F936B", "device": "q4q", "product": "q4qxxx"},
    {"name": "Galaxy Z Flip 4", "model": "SM-F721B", "device": "b4q", "product": "b4qxxx"},
    {"name": "Galaxy Note 20 Ultra 5G", "model": "SM-N986B", "device": "c2s", "product": "c2sxxx"},
    {"name": "Galaxy S21 FE 5G", "model": "SM-G990B", "device": "r9s", "product": "r9sxxx"},
    {"name": "Galaxy S23 FE", "model": "SM-S711B", "device": "r11s", "product": "r11sxxx"},
    {"name": "Galaxy Z Fold 3 5G", "model": "SM-F926B", "device": "q2q", "product": "q2qxxx"}
]


def generate_random_android_id() -> str:
    """Tạo mã Android ID (SSAID) ngẫu nhiên 16 ký tự hex."""
    return "".join(random.choices("0123456789abcdef", k=16))


def get_devices():
    all_devs = []
    seen = set()
    for p in ["5037", "5038"]:
        cmd = ["adb", "-P", p, "devices"] if p != "5037" else ["adb", "devices"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                serial = parts[0]
                if serial not in seen:
                    seen.add(serial)
                    all_devs.append((serial, p))
    return all_devs


def spoof_device(serial: str, port: str, profile: dict) -> dict:
    base = ["adb", "-P", port, "-s", serial] if port != "5037" else ["adb", "-s", serial]
    
    model = profile["model"]
    dev = profile["device"]
    prod = profile["product"]
    new_android_id = generate_random_android_id()

    # Danh sách các props cần đổi
    cmds = [
        # Đổi Model máy
        f"resetprop ro.product.model {model}",
        f"resetprop ro.product.system.model {model}",
        f"resetprop ro.product.vendor.model {model}",
        f"resetprop ro.product.odm.model {model}",
        f"resetprop ro.product.product.model {model}",
        
        # Đổi Device / Name / Product
        f"resetprop ro.product.device {dev}",
        f"resetprop ro.product.name {prod}",
        f"resetprop ro.build.product {dev}",
        f"resetprop ro.product.manufacturer samsung",
        f"resetprop ro.product.brand samsung",
        
        # Đổi mã định danh thiết bị Android ID (TikTok dựa vào mã này để nhận diện thiết bị)
        f"settings put secure android_id {new_android_id}"
    ]

    # Thực thi hàng loạt qua su pipe
    full_script = "\n".join(cmds) + "\n"
    p = subprocess.Popen(base + ["shell", "su"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p.communicate(input=full_script)

    # Đọc lại giá trị kiểm tra
    chk_res = subprocess.run(base + ["shell", "getprop", "ro.product.model"], capture_output=True, text=True)
    applied_model = chk_res.stdout.strip()

    return {
        "serial": serial,
        "profile_name": profile["name"],
        "model": applied_model,
        "android_id": new_android_id
    }


def main():
    devices = get_devices()
    if not devices:
        print("[-] Không tìm thấy thiết bị ADB nào!")
        return

    print("=" * 80)
    print(f"📱 ĐANG TIẾN HÀNH FAKE DÒNG MÁY & ĐỔI ANDROID ID CHO {len(devices)} THIẾT BỊ...")
    print("=" * 80)

    results = []
    with ThreadPoolExecutor(max_workers=min(len(devices), 17)) as executor:
        futures = []
        for idx, (serial, port) in enumerate(devices):
            prof = PROFILES[idx % len(PROFILES)]
            futures.append(executor.submit(spoof_device, serial, port, prof))

        for f in futures:
            results.append(f.result())

    print(f"\n{'STT':<4} | {'SERIAL':<20} | {'DÒNG MÁY MỚI':<24} | {'MODEL MÃ':<12} | {'ANDROID ID'}")
    print("-" * 80)
    for idx, r in enumerate(results, 1):
        print(f"{idx:<4} | {r['serial']:<20} | {r['profile_name']:<24} | {r['model']:<12} | {r['android_id']}")
    print("=" * 80)
    print("🎉 HOÀN TẤT FAKE DÒNG MÁY VÀ ĐỔI TOÀN BỘ DANH TÍNH THIẾT BỊ CHO 17 MÁY!")


if __name__ == "__main__":
    main()
