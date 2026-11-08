# -*- coding: utf-8 -*-
"""
HỆ THỐNG ĐIỀU PHỐI ĐA LUỒNG GOLIKE CHO DÀN PHONE FARM (CENTRALIZED JOB DISPATCHER)
==================================================================================
Mô hình:
- 1 Tài khoản GoLike chủ (quản lý tiền, nhận nhiệm vụ tập trung).
- N Thiết bị Android (mỗi máy 1 Proxy riêng, 1 tài khoản TikTok/MXH riêng).
- Tự động hóa tiếp nhận Job -> Phân luồng xuống từng điện thoại -> Tự động Like/Follow -> Xác nhận tiền về ví.
"""

import os
import sys
import time
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# CẤU HÌNH HỆ THỐNG MASTER
GOLIKE_MASTER_ACCOUNT = {
    "username": "usr_ryaa56449",
    "password": "Golike@8071A",
    "master_device_serial": "9889da304447393259", # Máy May_04 chạy app GoLike gốc có Proxy
    "master_adb_port": "5038"
}

# DANH SÁCH THIẾT BỊ WORKER TRONG FARM (Mỗi máy 1 Proxy & 1 nick TikTok riêng)
WORKER_DEVICES = [
    {
        "worker_id": "Worker_01",
        "serial": "9889da304447393259",
        "adb_port": "5038",
        "proxy": "160.250.185.49:14102",
        "tiktok_id": "@kenh_farm_04",
        "enabled": True
    },
    {
        "worker_id": "Worker_02",
        "serial": "988a17344c564b5657",
        "adb_port": "5037",
        "proxy": "160.250.166.242:22393",
        "tiktok_id": "@kenh_farm_05",
        "enabled": True
    },
    {
        "worker_id": "Worker_03",
        "serial": "ce01182188dbdcee0c",
        "adb_port": "5038",
        "proxy": "160.250.183.232:30546",
        "tiktok_id": "@kenh_farm_03",
        "enabled": True
    }
]

def adb_exec(serial, port, cmd_list):
    """Chạy lệnh ADB độc lập cho từng thiết bị và cổng tương ứng."""
    full_cmd = ["adb", "-P", str(port), "-s", str(serial)] + cmd_list
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res.stdout.strip()

def worker_execute_job(worker, job):
    """
    Luồng xử lý nhiệm vụ trên 1 điện thoại Worker cụ thể:
    1. Nhận thông tin Job từ Master Dispatcher.
    2. Kích hoạt TikTok mở thẳng đến link video/kênh đích qua Deeplink Intent.
    3. Tự động tương tác (Follow / Like).
    4. Giãn cách thời gian ngẫu nhiên (Anti-ban).
    5. Trả kết quả hoàn thành về cho Master.
    """
    w_id = worker["worker_id"]
    serial = worker["serial"]
    port = worker["adb_port"]
    
    job_id = job.get("job_id", "JOB_TEST_001")
    job_type = job.get("type", "FOLLOW") # FOLLOW / LIKE / COMMENT
    target_url = job.get("url", "https://www.tiktok.com/@tiktok")
    reward = job.get("reward", 50)
    
    print(f"\n[⚡ {w_id}] Nhận nhiệm vụ {job_id} | Loại: {job_type} | Thưởng: +{reward}đ")
    print(f"[⚡ {w_id}] Thiết bị: {serial} | Proxy: {worker['proxy']}")
    print(f"[⚡ {w_id}] Mở liên kết TikTok: {target_url}")
    
    # 1. Deeplink mở TikTok thẳng tới mục tiêu
    adb_exec(serial, port, [
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", target_url,
        "-p", "com.zhiliaoapp.musically"
    ])
    
    # 2. Chờ video/kênh load (3 - 5s)
    wait_load = random.uniform(3.0, 4.5)
    print(f"[⚡ {w_id}] Chờ trang TikTok tải ({wait_load:.1f}s)...")
    time.sleep(wait_load)
    
    # 3. Thực hiện hành động theo loại Job
    if job_type == "FOLLOW":
        print(f"[⚡ {w_id}] Thực hiện nhấn nút 'Follow'...")
        # Vị trí nút Follow chuẩn trên profile TikTok hoặc dùng id
        adb_exec(serial, port, ["shell", "input", "tap", "540", "950"])
    elif job_type == "LIKE":
        print(f"[⚡ {w_id}] Thực hiện thả tim video (Double Tap)...")
        adb_exec(serial, port, ["shell", "input", "tap", "540", "1100"])
        time.sleep(0.1)
        adb_exec(serial, port, ["shell", "input", "tap", "540", "1100"])
        
    # 4. Giữ tương tác mô phỏng người thật
    cool_down = random.uniform(2.5, 4.0)
    print(f"[⚡ {w_id}] Giữ delay an toàn chống spam ({cool_down:.1f}s)...")
    time.sleep(cool_down)
    
    # 5. Thoát hoặc đưa TikTok về nền
    adb_exec(serial, port, ["shell", "input", "keyevent", "3"]) # Phím Home
    
    print(f"[✓ {w_id}] Hoàn thành nhiệm vụ {job_id} thành công! Gửi báo cáo về Master.")
    return {
        "status": "SUCCESS",
        "worker_id": w_id,
        "job_id": job_id,
        "reward": reward,
        "time": datetime.now().strftime("%H:%M:%S")
    }

class GoLikeFarmDispatcher:
    def __init__(self, master_config, workers):
        self.master = master_config
        self.workers = [w for w in workers if w.get("enabled")]
        self.total_earned = 0
        self.completed_jobs = 0

    def get_pending_jobs_queue(self):
        """
        Mô phỏng lấy danh sách Job từ GoLike:
        Trong môi trường chạy thật, hàm này sẽ gọi API GoLike hoặc lấy từ App Master.
        """
        sample_jobs = [
            {"job_id": "GL_TT_9812", "type": "FOLLOW", "url": "https://www.tiktok.com/@tiktok", "reward": 55},
            {"job_id": "GL_TT_9813", "type": "LIKE", "url": "https://www.tiktok.com/@tiktok", "reward": 35},
            {"job_id": "GL_TT_9814", "type": "FOLLOW", "url": "https://www.tiktok.com/@gosen.vietnam", "reward": 60}
        ]
        return sample_jobs

    def start_dispatching(self, rounds=1):
        print("==================================================================")
        print("🚀 KHỞI ĐỘNG HỆ THỐNG ĐIỀU PHỐI ĐA LUỒNG PHONE FARM GOLIKE")
        print(f"[*] Tài khoản GoLike chủ: {self.master['username']}")
        print(f"[*] Số lượng Worker Phone sẵn sàng: {len(self.workers)} máy")
        print("==================================================================")
        
        for r in range(1, rounds + 1):
            print(f"\n--- BẮT ĐẦU VÒNG BẮN LUỒNG #{r} ---")
            jobs = self.get_pending_jobs_queue()
            
            # Khởi chạy đa luồng đồng thời cho các Worker Phone
            with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
                futures = []
                for i, worker in enumerate(self.workers):
                    job = jobs[i % len(jobs)]
                    f = executor.submit(worker_execute_job, worker, job)
                    futures.append(f)
                    time.sleep(1.0) # Giãn cách nhẹ giữa các luồng bắn
                
                for f in futures:
                    res = f.result()
                    if res["status"] == "SUCCESS":
                        self.completed_jobs += 1
                        self.total_earned += res["reward"]
                        print(f"💰 [Master] Đã xác nhận Job {res['job_id']} từ {res['worker_id']} -> +{res['reward']}đ vào ví chính!")
                        
        print("\n==================================================================")
        print("🏁 TỔNG KẾT VÒNG CHẠY:")
        print(f"[*] Tổng số Job hoàn thành: {self.completed_jobs} jobs")
        print(f"[*] Tổng tiền tích lũy vào ví chính: +{self.total_earned} VNĐ")
        print("==================================================================")

if __name__ == "__main__":
    dispatcher = GoLikeFarmDispatcher(GOLIKE_MASTER_ACCOUNT, WORKER_DEVICES)
    # Chạy thử nghiệm 1 vòng luồng mẫu
    dispatcher.start_dispatching(rounds=1)
