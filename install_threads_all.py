#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

ADB = r'C:\Program Files (x86)\xiaowei_android\tools\adb.exe'
APK_PATH = r'D:\TOOL TIKTOK\threads-455-0-0-0-5.apk'

if not os.path.exists(APK_PATH):
    print(f'LỖI: Không tìm thấy file {APK_PATH}')
    sys.exit(1)

def get_all_devices():
    devices = []
    for port in [5037, 5038]:
        res = subprocess.run([ADB, '-P', str(port), 'devices'], capture_output=True, text=True, errors='ignore')
        for line in res.stdout.strip().splitlines():
            parts = line.strip().split('\t')
            if len(parts) == 2 and parts[1] == 'device':
                devices.append((port, parts[0]))
    return devices

def install_on_device(port, serial, idx, total):
    print(f'[{idx}/{total}] Đang đẩy và cài đặt Threads lên {serial} (Port {port})...')
    cmd = [ADB, '-P', str(port), '-s', serial, 'install', '-r', '-d', '-g', APK_PATH]
    res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
    
    if 'Success' in res.stdout:
        print(f'  -> [THÀNH CÔNG] {serial}: Đã cài đặt Threads xong!')
        return serial, True, 'Success'
    else:
        cmd_retry = [ADB, '-P', str(port), '-s', serial, 'install', '-r', '-d', APK_PATH]
        res_retry = subprocess.run(cmd_retry, capture_output=True, text=True, errors='ignore')
        if 'Success' in res_retry.stdout:
            print(f'  -> [THÀNH CÔNG] {serial}: Đã cài đặt Threads xong (retry)!')
            return serial, True, 'Success'
        else:
            err = res_retry.stderr.strip() or res_retry.stdout.strip()
            print(f'  -> [THẤT BẠI] {serial}: {err}')
            return serial, False, err

def main():
    devices = get_all_devices()
    total = len(devices)
    size_mb = os.path.getsize(APK_PATH) / (1024 * 1024)
    print(f'====================================================')
    print(f'BẮT ĐẦU CÀI ĐẶT THREADS CHO {total} THIẾT BỊ')
    print(f'File APK: {APK_PATH} ({size_mb:.1f} MB)')
    print(f'====================================================')
    
    success_count = 0
    fail_count = 0
    
    # 5 concurrent threads to optimize USB bus bandwidth for ~120MB file
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(install_on_device, port, serial, i + 1, total): serial
            for i, (port, serial) in enumerate(devices)
        }
        for future in as_completed(futures):
            serial, ok, msg = future.result()
            if ok:
                success_count += 1
            else:
                fail_count += 1
                
    print(f'\n====================================================')
    print(f'HOÀN TẤT CÀI ĐẶT THREADS!')
    print(f'Thành công: {success_count}/{total} máy')
    if fail_count > 0:
        print(f'Thất bại: {fail_count}/{total} máy')
    print(f'====================================================')

if __name__ == '__main__':
    main()
