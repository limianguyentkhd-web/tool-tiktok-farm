import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

# 5 máy gắn proxy + 1 máy mẫu GoLike
KEEP_AWAKE = {
    "9889da304447393259": "Máy 1 (Proxy 1)",
    "988a17344c564b5657": "Máy 2 (Proxy 2)",
    "ce01182188dbdcee0c": "Máy 3 (Proxy 3)",
    "ce011821c38b263b05": "Máy 4 (Proxy 4)",
    "ce011821c45dc4060c": "Máy 5 (Proxy 5)",
    "ce031713dba2c72101": "Máy Mẫu GoLike (IP Gốc)"
}

def get_devices(port):
    res = subprocess.run([ADB, "-P", str(port), "devices"], capture_output=True, text=True)
    lines = [l.split('\t')[0].strip() for l in res.stdout.strip().split('\n')[1:] if '\tdevice' in l]
    return lines

all_devices = []
for p in [5037, 5038]:
    devs = get_devices(p)
    for d in devs:
        all_devices.append((p, d))

print(f"Tổng số thiết bị kết nối: {len(all_devices)}")
print("="*60)

sleeping_count = 0
awake_count = 0

for port, serial in all_devices:
    if serial in KEEP_AWAKE:
        # Đảm bảo máy thức (WAKEUP)
        subprocess.run([ADB, "-P", str(port), "-s", serial, "shell", "input", "keyevent", "224"])
        print(f"[+] GIỮ THỨC: {KEEP_AWAKE[serial]} ({serial})")
        awake_count += 1
    else:
        # Kiểm tra trạng thái màn hình
        pwr = subprocess.run([ADB, "-P", str(port), "-s", serial, "shell", "dumpsys power | grep mWakefulness"], capture_output=True, text=True).stdout
        if "Awake" in pwr:
            # Cho ngủ (KEYCODE_SLEEP 223)
            subprocess.run([ADB, "-P", str(port), "-s", serial, "shell", "input", "keyevent", "223"])
            # Phòng hờ nếu vẫn thức thì ấn Power (26)
            time.sleep(0.2)
            check_again = subprocess.run([ADB, "-P", str(port), "-s", serial, "shell", "dumpsys power | grep mWakefulness"], capture_output=True, text=True).stdout
            if "Awake" in check_again:
                subprocess.run([ADB, "-P", str(port), "-s", serial, "shell", "input", "keyevent", "26"])
        print(f"[-] CHO NGỦ : Máy rảnh {serial} (Port {port})")
        sleeping_count += 1

print("="*60)
print(f"[✓] ĐÃ CHO NGỦ XONG: {sleeping_count} MÁY RẢNH")
print(f"[✓] ĐANG HOẠT ĐỘNG  : {awake_count} MÁY CHÍNH (5 Máy Proxy + 1 Máy Mẫu GoLike)")
