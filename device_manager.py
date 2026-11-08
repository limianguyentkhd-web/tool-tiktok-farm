"""
Mô-đun quản lý và tối ưu hóa phần cứng thiết bị Android (Samsung S21 Ultra)
Hỗ trợ tự động dò tìm cổng ADB (5037 / 5038), kiểm soát độ sáng, nhiệt độ, pin và âm thanh.
"""

import os
import sys
import subprocess
from typing import List, Dict, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class DeviceManager:
    def __init__(self, ports: List[str] = None):
        self.ports = ports or ["5037", "5038"]
        self.active_port = "5037"
        self.devices = []
        self.refresh_devices()

    def run_adb(self, serial: Optional[str], cmd_args: List[str]) -> str:
        cmd = ["adb"]
        if self.active_port != "5037":
            cmd.extend(["-P", self.active_port])
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(cmd_args)
        
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.stdout.decode("utf-8", errors="replace").strip()

    def refresh_devices(self) -> List[str]:
        """Tự động tìm kiếm thiết bị trên cả hai cổng 5037 và 5038."""
        for p in self.ports:
            cmd = ["adb", "-P", p, "devices"] if p != "5037" else ["adb", "devices"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = res.stdout.decode("utf-8", errors="replace").strip()
            devs = []
            for line in output.split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devs.append(parts[0])
            if devs:
                self.active_port = p
                self.devices = devs
                return devs
        self.devices = []
        return []

    def optimize_device(self, serial: str) -> None:
        """
        Tối ưu thiết bị giúp mát máy, chống nóng, tiết kiệm pin cho phone farm:
        - Giảm độ sáng về 0
        - Mute toàn bộ âm lượng (âm lượng media, chuông, thông báo)
        - Giữ màn hình sáng không bị sleep giữa chừng
        - Cố định xoay dọc (Portrait)
        """
        # 1. Giảm độ sáng về 0
        self.run_adb(serial, ["shell", "settings", "put", "system", "screen_brightness", "0"])
        # 2. Tắt chế độ tự động điều chỉnh độ sáng
        self.run_adb(serial, ["shell", "settings", "put", "system", "screen_brightness_mode", "0"])
        # 3. Tắt tự động xoay màn hình (cố định dọc)
        self.run_adb(serial, ["shell", "settings", "put", "system", "accelerometer_rotation", "0"])
        # 4. Tắt âm lượng media và chuông (Stream 3: Music, Stream 2: Ring, Stream 5: Notification)
        self.run_adb(serial, ["shell", "media", "volume", "--stream", "3", "--set", "0"])
        self.run_adb(serial, ["shell", "media", "volume", "--stream", "2", "--set", "0"])
        self.run_adb(serial, ["shell", "media", "volume", "--stream", "5", "--set", "0"])
        # 5. Đặt thời gian chờ tắt màn hình dài (30 phút = 1800000ms) để không bị khóa
        self.run_adb(serial, ["shell", "settings", "put", "system", "screen_off_timeout", "1800000"])

    def optimize_all_devices(self) -> None:
        """Tối ưu hóa toàn bộ dàn máy."""
        print(f"[*] Đang áp dụng thiết lập tối ưu (độ sáng 0%, tắt âm, chống sleep) cho {len(self.devices)} máy...")
        for dev in self.devices:
            self.optimize_device(dev)
        print("[+] Hoàn tất tối ưu phần cứng cho toàn bộ máy! Dàn máy sẽ chạy mát và tiết kiệm điện.")

    def get_device_health(self, serial: str) -> Dict[str, str]:
        """Đọc thông số nhiệt độ và tình trạng pin của máy."""
        battery_dump = self.run_adb(serial, ["shell", "dumpsys", "battery"])
        level = "N/A"
        temp = "N/A"
        for line in battery_dump.split("\n"):
            line = line.strip()
            if line.startswith("level:"):
                level = f"{line.split(':')[1].strip()}%"
            elif line.startswith("temperature:"):
                # Nhiệt độ đơn vị là 0.1 độ C (ví dụ 320 là 32.0 độ C)
                raw_t = int(line.split(':')[1].strip())
                temp = f"{raw_t / 10.0:.1f}°C"
        return {"serial": serial, "battery": level, "temperature": temp}

    def sleep_device(self, serial: str) -> None:
        """Đưa thiết bị vào chế độ Ngủ Đông Siêu Tiết Kiệm Điện (Mát máy, hạ CPU, tắt màn hình)."""
        self.run_adb(serial, ["shell", "settings", "put", "global", "low_power", "1"])
        self.run_adb(serial, ["shell", "settings", "put", "system", "screen_brightness", "0"])
        self.run_adb(serial, ["shell", "settings", "put", "global", "stay_on_while_plugged_in", "0"])
        self.run_adb(serial, ["shell", "svc", "power", "stayon", "false"])
        self.run_adb(serial, ["shell", "settings", "put", "system", "screen_off_timeout", "15000"])
        self.run_adb(serial, ["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
        self.run_adb(serial, ["shell", "cmd", "media_session", "volume", "--set", "0"])
        self.run_adb(serial, ["shell", "input", "keyevent", "26"])

    def wake_device(self, serial: str) -> None:
        """Đánh thức thiết bị dậy ngay lập tức để làm việc."""
        self.run_adb(serial, ["shell", "settings", "put", "global", "low_power", "0"])
        self.run_adb(serial, ["shell", "settings", "put", "system", "screen_off_timeout", "1800000"])
        self.run_adb(serial, ["shell", "input", "keyevent", "224"]) # WAKEUP
        self.run_adb(serial, ["shell", "input", "keyevent", "82"])  # UNLOCK


if __name__ == "__main__":
    dm = DeviceManager()
    print(f"[*] Tìm thấy {len(dm.devices)} thiết bị trên cổng ADB: {dm.active_port}")
    dm.optimize_all_devices()
    print("\n--- Báo cáo sức khỏe thiết bị ---")
    for d in dm.devices:
        h = dm.get_device_health(d)
        print(f"[{h['serial']}] Pin: {h['battery']} | Nhiệt độ: {h['temperature']}")
