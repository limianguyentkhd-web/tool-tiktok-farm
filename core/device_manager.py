# -*- coding: utf-8 -*-
"""
Module Quản lý Thiết Bị ADB Đa Cổng (Device Manager)
Hỗ trợ dàn Phone Farm nhiều máy cắm qua XiaoWei hoặc USB Hub.
"""

import os
import subprocess
import random
import time
from typing import List, Dict, Optional, Tuple

class DeviceManager:
    def __init__(self, adb_path: str, ports: List[str] = None):
        self.adb_path = adb_path
        self.ports = ports or ["5037", "5038", "5039"]
        self.device_port_map: Dict[str, str] = {} # serial -> port

    def run_adb(self, serial: str, args: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
        """Thực thi lệnh ADB với port tương ứng của serial."""
        port = self.device_port_map.get(serial, "5037")
        cmd = [self.adb_path, "-P", port, "-s", serial] + args
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                errors="replace"
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, 124, stdout="", stderr="Timeout")
        except Exception as e:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=str(e))

    def scan_devices(self) -> List[Dict[str, str]]:
        """Quét toàn bộ thiết bị qua các cổng ADB."""
        devices = []
        self.device_port_map.clear()
        
        for port in self.ports:
            try:
                cmd = [self.adb_path, "-P", port, "devices"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, errors="replace")
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if "\tdevice" in line:
                        serial = line.split("\t")[0].strip()
                        self.device_port_map[serial] = port
                        model = self.get_model(serial, port)
                        battery = self.get_battery(serial, port)
                        devices.append({
                            "serial": serial,
                            "port": port,
                            "model": model,
                            "battery": battery,
                            "status": "Online"
                        })
            except Exception as e:
                print(f"[!] Lỗi quét port {port}: {e}")
        return devices

    def get_model(self, serial: str, port: str = "5037") -> str:
        cmd = [self.adb_path, "-P", port, "-s", serial, "shell", "getprop", "ro.product.model"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3, errors="replace")
            return res.stdout.strip() or "Unknown"
        except Exception:
            return "Unknown"

    def get_battery(self, serial: str, port: str = "5037") -> str:
        cmd = [self.adb_path, "-P", port, "-s", serial, "shell", "dumpsys", "battery"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3, errors="replace")
            for line in res.stdout.splitlines():
                if "level:" in line:
                    return line.split(":")[1].strip() + "%"
        except Exception:
            pass
        return "N/A"

    def get_screen_size(self, serial: str) -> Tuple[int, int]:
        res = self.run_adb(serial, ["shell", "wm", "size"])
        for line in res.stdout.splitlines():
            if "Physical size:" in line:
                parts = line.split(":")[1].strip().split("x")
                if len(parts) == 2:
                    try:
                        return int(parts[0]), int(parts[1])
                    except ValueError:
                        pass
        return 1080, 2400

    def tap(self, serial: str, x: int, y: int, jitter: int = 5):
        """Chạm có độ lệch ngẫu nhiên mô phỏng ngón tay người."""
        jx = x + random.randint(-jitter, jitter)
        jy = y + random.randint(-jitter, jitter)
        self.run_adb(serial, ["shell", "input", "tap", str(jx), str(jy)])

    def human_swipe(self, serial: str, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = None):
        """Vuốt với thời lượng và quỹ đạo ngẫu nhiên."""
        if not duration_ms:
            duration_ms = random.randint(350, 600)
        sx = start_x + random.randint(-15, 15)
        sy = start_y + random.randint(-15, 15)
        ex = end_x + random.randint(-15, 15)
        ey = end_y + random.randint(-15, 15)
        self.run_adb(serial, ["shell", "input", "swipe", str(sx), str(sy), str(ex), str(ey), str(duration_ms)])

    def key_back(self, serial: str):
        self.run_adb(serial, ["shell", "input", "keyevent", "4"])

    def key_home(self, serial: str):
        self.run_adb(serial, ["shell", "input", "keyevent", "3"])

    def take_screenshot(self, serial: str, save_path: str) -> bool:
        """Chụp ảnh màn hình lưu trực tiếp về máy tính."""
        remote_path = "/sdcard/screen_dump.png"
        res = self.run_adb(serial, ["shell", "screencap", "-p", remote_path], timeout=8)
        if res.returncode == 0:
            res_pull = self.run_adb(serial, ["pull", remote_path, save_path], timeout=10)
            return res_pull.returncode == 0 and os.path.exists(save_path)
        return False

    def dump_ui_xml(self, serial: str, save_path: str) -> bool:
        """Dump UI XML để phân tích các thành phần và chữ trên màn hình."""
        remote_xml = "/sdcard/window_dump.xml"
        self.run_adb(serial, ["shell", "uiautomator", "dump", remote_xml], timeout=10)
        res_pull = self.run_adb(serial, ["pull", remote_xml, save_path], timeout=8)
        return res_pull.returncode == 0 and os.path.exists(save_path)

    def force_stop(self, serial: str, package_name: str):
        self.run_adb(serial, ["shell", "am", "force-stop", package_name])

    def start_app(self, serial: str, package_activity: str):
        self.run_adb(serial, ["shell", "am", "start", "-n", package_activity])

    def push_file(self, serial: str, local_path: str, remote_path: str) -> bool:
        res = self.run_adb(serial, ["push", local_path, remote_path], timeout=60)
        return res.returncode == 0

    def trigger_media_scan(self, serial: str, file_path: str):
        """Kích hoạt Android quét lại thư viện ảnh/video để file hiển thị ngay trong TikTok."""
        self.run_adb(serial, [
            "shell", "am", "broadcast",
            "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", f"file://{file_path}"
        ])
