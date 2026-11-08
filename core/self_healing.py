# -*- coding: utf-8 -*-
"""
Tầng 1: Bộ Tự Phục Hồi Quy Tắc (Self-Healing Engine & Auto-Dismiss Popups)
Tự động dập tắt mọi popup gây nghẽn, khởi động lại app khi bị đơ, không cần người trực.
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Tuple, Optional, List
from .device_manager import DeviceManager

DISMISS_KEYWORDS = [
    # Tiếng Việt
    "để sau", "không phải bây giờ", "hủy", "bỏ qua", "từ chối", 
    "đóng", "không cảm ơn", "lúc khác", "cho phép", "trong khi dùng ứng dụng",
    # English
    "not now", "later", "cancel", "skip", "dismiss", 
    "close", "no thanks", "allow", "while using the app"
]

class SelfHealingEngine:
    def __init__(self, device_mgr: DeviceManager, temp_dir: str = "logs"):
        self.dm = device_mgr
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

    def parse_bounds(self, bounds_str: str) -> Optional[Tuple[int, int]]:
        """Chuyển đổi chuỗi '[x1,y1][x2,y2]' thành tọa độ tâm (center_x, center_y)."""
        match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return (x1 + x2) // 2, (y1 + y2) // 2
        return None

    def auto_dismiss_popups(self, serial: str) -> bool:
        """
        Quét giao diện hiện tại của máy. Nếu phát hiện bất kỳ nút popup nào
        nằm trong danh sách DISMISS_KEYWORDS, tự động bấm dập tắt ngay lập tức.
        Trả về True nếu vừa dập tắt được 1 popup.
        """
        xml_path = os.path.join(self.temp_dir, f"dump_{serial}.xml")
        if not self.dm.dump_ui_xml(serial, xml_path):
            return False

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for elem in root.iter():
                text = (elem.attrib.get("text") or "").strip().lower()
                desc = (elem.attrib.get("content-desc") or "").strip().lower()
                bounds = elem.attrib.get("bounds", "")

                combined = f"{text} {desc}".strip()
                if not combined or not bounds:
                    continue

                for kw in DISMISS_KEYWORDS:
                    if kw == combined or (len(kw) > 3 and kw in combined):
                        center = self.parse_bounds(bounds)
                        if center:
                            cx, cy = center
                            print(f"[{serial}] [Tự phục hồi] Phát hiện popup: '{combined}'. Đang bấm tọa độ ({cx}, {cy})...")
                            self.dm.tap(serial, cx, cy)
                            return True
        except Exception as e:
            print(f"[{serial}] [Tự phục hồi] Lỗi đọc XML: {e}")
        finally:
            if os.path.exists(xml_path):
                try:
                    os.remove(xml_path)
                except Exception:
                    pass
        return False

    def recover_if_stuck(self, serial: str, package_name: str = "com.zhiliaoapp.musically", max_tries: int = 3) -> bool:
        """
        Cố gắng dập tắt popup liên tục tối đa max_tries lần.
        Nếu vẫn không thoát được kẹt, khởi động lại app để làm mới từ đầu.
        """
        for i in range(max_tries):
            if self.auto_dismiss_popups(serial):
                import time
                time.sleep(1.5)
            else:
                return True

        # Nếu vẫn bị kẹt -> Restart app
        print(f"[{serial}] [Tự phục hồi] Bị kẹt sâu, tiến hành khởi động lại {package_name}...")
        self.dm.force_stop(serial, package_name)
        import time
        time.sleep(2)
        self.dm.start_app(serial, f"{package_name}/com.ss.android.ugc.aweme.splash.SplashActivity")
        time.sleep(5)
        self.auto_dismiss_popups(serial)
        return False
