"""
Bộ điều phối cân bằng tải (Task Dispatcher & Staggered Load Balancer) cho dàn 17 máy Phone Farm.
Đảm bảo:
1. Không chạy 17 máy cùng 1 giây (tránh dồn băng thông USB & tránh TikTok phát hiện bot).
2. Chia thành các đợt (Batching) theo nhóm máy.
3. Tạo độ trễ ngẫu nhiên (Jitter / Random Delay) mô phỏng hành vi tự nhiên.
"""

import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Dict, Any

from device_manager import DeviceManager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class TaskDispatcher:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.dm = DeviceManager(self.config.get("system", {}).get("adb_ports", ["5037", "5038"]))
        self.devices = self.dm.devices

    def _load_config(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "system": {
                "max_concurrent_workers": 4,
                "batch_delay_min_seconds": 10,
                "batch_delay_max_seconds": 20,
                "action_delay_min_seconds": 2,
                "action_delay_max_seconds": 5
            }
        }

    def run_staggered(self, task_func: Callable[[str, DeviceManager], Any], task_name: str = "Tác vụ"):
        """
        Chạy tác vụ trên toàn bộ máy theo cơ chế cân bằng tải so le:
        - Chia máy thành các nhóm (Batch)
        - Giãn cách delay ngẫu nhiên giữa các máy
        - Nghỉ giữa các nhóm
        """
        sys_cfg = self.config.get("system", {})
        batch_size = sys_cfg.get("max_concurrent_workers", 4)
        act_min = sys_cfg.get("action_delay_min_seconds", 3)
        act_max = sys_cfg.get("action_delay_max_seconds", 8)
        batch_min = sys_cfg.get("batch_delay_min_seconds", 15)
        batch_max = sys_cfg.get("batch_delay_max_seconds", 30)

        total_devs = len(self.devices)
        if total_devs == 0:
            print("[-] Không tìm thấy thiết bị nào!")
            return

        # Chia danh sách 17 máy thành các nhóm (Batch)
        batches = [self.devices[i:i + batch_size] for i in range(0, total_devs, batch_size)]

        print("=" * 75)
        print(f"⚡ BỘ ĐIỀU PHỐI CÂN BẰNG TẢI DÀN MÁY ({total_devs} Thiết bị)")
        print(f"📋 Tác vụ: {task_name}")
        print(f"📦 Số nhóm chia: {len(batches)} nhóm (Tối đa {batch_size} máy/nhóm)")
        print(f"⏱️ Độ trễ ngẫu nhiên mỗi máy: {act_min}s - {act_max}s")
        print("=" * 75)

        for b_idx, batch in enumerate(batches, 1):
            print(f"\n🚀 >>> ĐANG CHẠY NHÓM {b_idx}/{len(batches)} ({len(batch)} máy): {', '.join(batch)}")

            def worker(serial: str):
                # Tạo độ trễ ngẫu nhiên trước khi thực hiện để không đè request cùng lúc
                delay = random.uniform(act_min, act_max)
                time.sleep(delay)
                try:
                    res = task_func(serial, self.dm)
                    print(f"  [+] [{serial}] Hoàn thành {task_name}! ✅")
                    return res
                except Exception as e:
                    print(f"  [-] [{serial}] Lỗi khi chạy: {e} ❌")
                    return None

            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                list(executor.map(worker, batch))

            # Nếu chưa phải nhóm cuối cùng thì nghỉ giữa các nhóm để tản nhiệt và hạ tải đường truyền
            if b_idx < len(batches):
                pause_time = random.uniform(batch_min, batch_max)
                print(f"⏳ Nghỉ giãn cách {pause_time:.1f} giây trước khi chuyển sang nhóm tiếp theo...")
                time.sleep(pause_time)

        print("\n🎉 TOÀN BỘ CÁC NHÓM ĐÃ HOÀN THÀNH TÁC VỤ AN TOÀN VÀ CÂN BẰNG TẢI!")


if __name__ == "__main__":
    # Test thử một tác vụ mẫu: Kiểm tra và mở giao diện TikTok
    def sample_task(serial: str, dm: DeviceManager):
        # Ví dụ: Mở TikTok
        dm.run_adb(serial, ["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
        return True

    dispatcher = TaskDispatcher()
    dispatcher.run_staggered(sample_task, task_name="Khởi động TikTok an toàn")
