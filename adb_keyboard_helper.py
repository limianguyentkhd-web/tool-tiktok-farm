"""
Module hỗ trợ nhập văn bản tiếng Việt có dấu trên Android qua ADB Keyboard
Hỗ trợ cả cổng ADB mặc định và cổng 5038 của Xiaowei Phone Farm.
"""

import base64
import os
import subprocess
import sys
from typing import Optional

# Cấu hình encoding utf-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ADB_PORT = os.environ.get("ANDROID_ADB_SERVER_PORT", "5038")


def _get_adb_base(serial: Optional[str] = None) -> list:
    cmd = ["adb", "-P", ADB_PORT]
    if serial:
        cmd.extend(["-s", serial])
    return cmd


def set_adb_keyboard(serial: Optional[str] = None) -> bool:
    """Kích hoạt và chọn ADB Keyboard làm bàn phím mặc định."""
    ime = "com.android.adbkeyboard/.AdbIME"
    subprocess.run(_get_adb_base(serial) + ["shell", "ime", "enable", ime], capture_output=True, check=False)
    res = subprocess.run(_get_adb_base(serial) + ["shell", "ime", "set", ime], capture_output=True, check=False)
    return res.returncode == 0


def type_vietnamese(text: str, serial: Optional[str] = None) -> bool:
    """
    Gõ văn bản tiếng Việt có dấu, emoji hoặc ký tự đặc biệt vào ô input đang focus.
    
    :param text: Nội dung cần gõ (hỗ trợ tiếng Việt đầy đủ dấu, emoji, xuống dòng)
    :param serial: Serial của máy Android (nếu có nhiều máy)
    """
    b64_text = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    cmd = _get_adb_base(serial) + [
        "shell",
        "am", "broadcast",
        "-a", "ADB_INPUT_B64",
        "--es", "msg", b64_text
    ]
    res = subprocess.run(cmd, capture_output=True, check=False)
    return res.returncode == 0


def clear_text(chars_count: int = 50, serial: Optional[str] = None) -> None:
    """Xóa các ký tự trước con trỏ bằng phím Backspace (KEYCODE_DEL = 67)."""
    cmd = _get_adb_base(serial) + ["shell", "input", "keyevent"] + ["67"] * min(chars_count, 100)
    subprocess.run(cmd, capture_output=True, check=False)


def setup_all_keyboards():
    """Thiết lập ADBKeyboard cho toàn bộ các thiết bị đang kết nối."""
    result = subprocess.run(["adb", "-P", ADB_PORT, "devices"], capture_output=True, text=True)
    lines = []
    for line in result.stdout.strip().split("\n")[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            lines.append(parts[0])

    print(f"[*] Thiết lập ADBKeyboard cho {len(lines)} thiết bị...")
    for dev in lines:
        set_adb_keyboard(dev)
    print(f"[+] Đã hoàn tất cấu hình bàn phím tiếng Việt cho {len(lines)} thiết bị!")


if __name__ == "__main__":
    setup_all_keyboards()
