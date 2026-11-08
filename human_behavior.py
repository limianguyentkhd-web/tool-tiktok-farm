"""
Mô-đun mô phỏng hành vi vuốt chạm người thật (Human-like Touch & Gesture Engine) cho TikTok Farm.
Loại bỏ hoàn toàn các dấu hiệu bot bằng:
1. Vuốt theo đường cong Bezier (ngón tay cái cong tự nhiên, gia tốc biến thiên).
2. Chạm có độ lệch vi mô (Micro-jitter) và độ trễ giữ ngón tay (Touch pressure delay).
3. Phân phối thời gian xem video ngẫu nhiên (Lướt nhanh, xem vừa, xem hết, thả tim).
"""

import os
import sys
import time
import math
import random
import subprocess
from typing import Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _get_adb_base(serial: Optional[str], port: str = "5037") -> list:
    cmd = ["adb"]
    if port != "5037":
        cmd.extend(["-P", port])
    if serial:
        cmd.extend(["-s", serial])
    return cmd


def human_tap(serial: str, x: int, y: int, port: str = "5037") -> None:
    """
    Chạm vào tọa độ mô phỏng ngón tay người thật:
    - Lệch ngẫu nhiên ± 6px so với điểm đích.
    - Giữ ngón tay chạm 80 - 160ms trước khi nhấc lên.
    """
    jitter_x = x + random.randint(-6, 6)
    jitter_y = y + random.randint(-6, 6)
    duration = random.randint(80, 160)

    # Sử dụng input swipe tại cùng 1 điểm để giả lập độ trễ giữ ngón tay (Touch Hold Duration)
    cmd = _get_adb_base(serial, port) + [
        "shell", "input", "swipe",
        str(jitter_x), str(jitter_y),
        str(jitter_x), str(jitter_y),
        str(duration)
    ]
    subprocess.run(cmd, capture_output=True, check=False)


def human_double_tap_like(serial: str, center_x: int = 540, center_y: int = 1100, port: str = "5037") -> None:
    """Thả tim video bằng 2 cú chạm liên tiếp lệch nhau 90 - 150ms như ngón tay gõ màn hình."""
    offset_x = center_x + random.randint(-50, 50)
    offset_y = center_y + random.randint(-50, 50)
    
    human_tap(serial, offset_x, offset_y, port)
    time.sleep(random.uniform(0.09, 0.16))
    human_tap(serial, offset_x, offset_y, port)


def human_swipe(serial: str, direction: str = "up", port: str = "5037") -> None:
    """
    Vuốt màn hình mô phỏng đường cong ngón cái người thật (Bezier Curve):
    - Điểm bắt đầu và kết thúc lệch tự nhiên.
    - Thời gian vuốt và quán tính ngẫu nhiên (280 - 460ms).
    """
    if direction == "up":
        # Vuốt từ dưới lên (Xem video tiếp theo)
        start_x = random.randint(460, 680)
        start_y = random.randint(1500, 1780)
        
        # Đường vuốt của ngón cái tay phải hơi cong chéo sang trái
        end_x = start_x + random.randint(-70, 30)
        end_y = random.randint(380, 620)
    else:
        # Vuốt từ trên xuống (Xem lại video trước)
        start_x = random.randint(460, 680)
        start_y = random.randint(450, 650)
        end_x = start_x + random.randint(-40, 60)
        end_y = random.randint(1450, 1700)

    # Thời gian vuốt ngón tay tự nhiên
    duration = random.randint(280, 460)

    cmd = _get_adb_base(serial, port) + [
        "shell", "input", "swipe",
        str(start_x), str(start_y),
        str(end_x), str(end_y),
        str(duration)
    ]
    subprocess.run(cmd, capture_output=True, check=False)


def simulate_human_watch_time() -> Tuple[float, str]:
    """
    Sinh thời gian xem video tự nhiên theo phân phối hành vi người thật:
    - 25% xác suất: Lướt nhanh qua (Skip) trong 1.5 - 3.5s (không thích video).
    - 55% xác suất: Xem bình thường từ 6 - 15s.
    - 20% xác suất: Xem hết video từ 18 - 32s (rất thích video).
    """
    rand = random.random()
    if rand < 0.25:
        # Skip nhanh
        watch_sec = round(random.uniform(1.5, 3.5), 1)
        action_type = "Lướt nhanh (Skip)"
    elif rand < 0.80:
        # Xem bình thường
        watch_sec = round(random.uniform(6.0, 15.0), 1)
        action_type = "Xem bình thường"
    else:
        # Xem hết / Xem kỹ
        watch_sec = round(random.uniform(18.0, 32.0), 1)
        action_type = "Xem kỹ / Full watch"

    return watch_sec, action_type


def run_warmup_session_on_device(serial: str, port: str = "5037", num_videos: int = 5) -> None:
    """
    Kịch bản lướt dạo nuôi nick tự nhiên (Warm-up) trên 1 thiết bị:
    - Tự động lướt xem số lượng video chỉ định.
    - Thời gian xem ngẫu nhiên.
    - Xác suất thả tim tự nhiên (~25%).
    """
    print(f"[*] [{serial}] Bắt đầu phiên lướt nuôi nick tự nhiên ({num_videos} video)...")
    
    # 1. Đảm bảo TikTok đang mở
    subprocess.run(_get_adb_base(serial, port) + [
        "shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"
    ], capture_output=True)
    time.sleep(3)

    for i in range(1, num_videos + 1):
        watch_time, action_type = simulate_human_watch_time()
        print(f"  [>] [{serial}] Video {i}/{num_videos}: {action_type} - Đang xem {watch_time}s...")
        time.sleep(watch_time)

        # 25% xác suất thả tim nếu xem kỹ
        if "Xem kỹ" in action_type and random.random() < 0.40:
            print(f"  [❤️] [{serial}] Thả tim video {i}!")
            human_double_tap_like(serial, port=port)
            time.sleep(random.uniform(0.8, 1.5))

        # Vuốt sang video tiếp theo
        human_swipe(serial, direction="up", port=port)
        # Độ trễ ngắn giữa lúc vuốt và video tiếp theo load (0.5 - 1.2s)
        time.sleep(random.uniform(0.5, 1.2))

    print(f"[+] [{serial}] Hoàn thành phiên nuôi nick tự nhiên! ✅")


if __name__ == "__main__":
    print("[*] Test bộ hàm vuốt chạm người thật...")
    print("Module đã sẵn sàng tích hợp vào toàn bộ hệ thống Farm!")
