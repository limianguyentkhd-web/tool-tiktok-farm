"""
Script tự động cài đặt GPS JoyStick và rải 17 tọa độ thực tế tại các thành phố lớn cho 17 máy.
- Tự động cài đặt APK
- Cấp quyền SYSTEM MOCK LOCATION
- Kích hoạt dịch vụ Fake GPS với tọa độ riêng biệt cho từng máy
"""

import os
import sys
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Danh sách 17 tọa độ thực tế tại các quận huyện sầm uất Việt Nam
LOCATIONS = [
    {"city": "Hà Nội - Hoàn Kiếm", "lat": 21.028511, "lng": 105.854167},
    {"city": "Hà Nội - Cầu Giấy", "lat": 21.036237, "lng": 105.790583},
    {"city": "Hà Nội - Đống Đa", "lat": 21.018072, "lng": 105.827725},
    {"city": "Hà Nội - Hai Bà Trưng", "lat": 21.006849, "lng": 105.852318},
    {"city": "Hà Nội - Thanh Xuân", "lat": 20.993712, "lng": 105.809314},
    {"city": "Hà Nội - Nam Từ Liêm", "lat": 21.020521, "lng": 105.764512},
    {"city": "TP.HCM - Quận 1 (Bến Nghé)", "lat": 10.776889, "lng": 106.700806},
    {"city": "TP.HCM - Quận 3", "lat": 10.784361, "lng": 106.684444},
    {"city": "TP.HCM - Bình Thạnh", "lat": 10.810583, "lng": 106.697417},
    {"city": "TP.HCM - Quận 7 (Phú Mỹ Hưng)", "lat": 10.732667, "lng": 106.716667},
    {"city": "TP.HCM - Tân Bình", "lat": 10.801472, "lng": 106.654806},
    {"city": "TP.HCM - TP. Thủ Đức", "lat": 10.850028, "lng": 106.771917},
    {"city": "TP.HCM - Quận 10", "lat": 10.774611, "lng": 106.666917},
    {"city": "Đà Nẵng - Hải Châu", "lat": 16.054407, "lng": 108.202167},
    {"city": "Đà Nẵng - Sơn Trà", "lat": 16.082472, "lng": 108.243139},
    {"city": "Hải Phòng - Hồng Bàng", "lat": 20.865139, "lng": 106.683833},
    {"city": "Cần Thơ - Ninh Kiều", "lat": 10.034167, "lng": 105.787639}
]

APK_PATH = r"D:\TOOL TIKTOK\GPS_JoyStick.apk"
PKG_NAME = "com.theappninjas.fakegpsjoystick"


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


def setup_device_gps(serial: str, port: str, loc_info: dict) -> dict:
    base = ["adb", "-P", port, "-s", serial] if port != "5037" else ["adb", "-s", serial]
    
    # 1. Cài đặt APK
    subprocess.run(base + ["install", "-r", "-d", "-g", APK_PATH], capture_output=True)

    # 2. Bật chế độ vị trí (High accuracy GPS)
    subprocess.run(base + ["shell", "settings", "put", "secure", "location_mode", "3"], capture_output=True)

    # 3. Cấp quyền Mock Location bằng quyền root
    subprocess.run(base + ["shell", "su", "-c", f"appops set {PKG_NAME} android:mock_location allow"], capture_output=True)
    subprocess.run(base + ["shell", "su", "-c", f"pm grant {PKG_NAME} android.permission.ACCESS_FINE_LOCATION"], capture_output=True)
    subprocess.run(base + ["shell", "su", "-c", f"pm grant {PKG_NAME} android.permission.ACCESS_COARSE_LOCATION"], capture_output=True)

    # 4. Bật service Fake GPS với tọa độ
    lat = loc_info["lat"]
    lng = loc_info["lng"]
    start_cmd = (
        f"am start-foreground-service -a {PKG_NAME}.START "
        f"--ef lat {lat} --ef lng {lng} --ef alt 10.0 --ef spd 0.0"
    )
    subprocess.run(base + ["shell", "su", "-c", start_cmd], capture_output=True)

    return {
        "serial": serial,
        "city": loc_info["city"],
        "coords": f"{lat:.4f}, {lng:.4f}"
    }


def main():
    devices = get_devices()
    if not devices:
        print("[-] Không tìm thấy thiết bị ADB nào!")
        return

    print("=" * 75)
    print(f"🗺️  ĐANG CÀI ĐẶT & RẢI TỌA ĐỘ GPS CHO {len(devices)} THIẾT BỊ...")
    print("=" * 75)

    results = []
    with ThreadPoolExecutor(max_workers=min(len(devices), 17)) as executor:
        futures = []
        for idx, (serial, port) in enumerate(devices):
            loc = LOCATIONS[idx % len(LOCATIONS)]
            futures.append(executor.submit(setup_device_gps, serial, port, loc))

        for f in futures:
            results.append(f.result())

    print(f"\n{'STT':<4} | {'SERIAL':<20} | {'ĐỊA ĐIỂM FAKE':<28} | {'TỌA ĐỘ GPS'}")
    print("-" * 75)
    for idx, r in enumerate(results, 1):
        print(f"{idx:<4} | {r['serial']:<20} | {r['city']:<28} | {r['coords']}")
    print("=" * 75)
    print("🎉 ĐÃ HOÀN TẤT THIẾT LẬP FAKE GPS CHO TOÀN BỘ 17 MÁY!")


if __name__ == "__main__":
    main()
