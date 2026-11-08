import subprocess
import time
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

PROXIES = [
    {
        "id": 1,
        "port": 5038,
        "serial": "9889da304447393259",
        "name": "Proxy_1",
        "ip": "160.250.185.49",
        "proxy_port": "14102",
        "user": "ntnKhj",
        "pass": "oExYql"
    },
    {
        "id": 2,
        "port": 5038,
        "serial": "988a17344c564b5657",
        "name": "Proxy_2",
        "ip": "160.250.166.242",
        "proxy_port": "22393",
        "user": "ntnKhj",
        "pass": "oExYql"
    },
    {
        "id": 3,
        "port": 5037,
        "serial": "ce01182188dbdcee0c",
        "name": "Proxy_3",
        "ip": "160.250.183.232",
        "proxy_port": "30546",
        "user": "ntnKhj",
        "pass": "oExYql"
    },
    {
        "id": 4,
        "port": 5037,
        "serial": "ce011821c38b263b05",
        "name": "Proxy_4",
        "ip": "160.30.191.96",
        "proxy_port": "18817",
        "user": "ntnKhj",
        "pass": "oExYql"
    },
    {
        "id": 5,
        "port": 5038,
        "serial": "ce011821c45dc4060c",
        "name": "Proxy_5",
        "ip": "157.15.38.228",
        "proxy_port": "30096",
        "user": "ntnKhj",
        "pass": "oExYql"
    }
]

def adb_cmd(port, serial, cmd_list):
    full_cmd = [ADB, "-P", str(port), "-s", serial] + cmd_list
    res = subprocess.run(full_cmd, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()

def dump_ui(port, serial):
    adb_cmd(port, serial, ["shell", "uiautomator", "dump", "/sdcard/v2dump.xml"])
    xml_str = adb_cmd(port, serial, ["shell", "cat", "/sdcard/v2dump.xml"])
    try:
        return ET.fromstring(xml_str)
    except Exception as e:
        return None

def find_node(root, **kwargs):
    if root is None:
        return None
    for elem in root.iter():
        match = True
        for k, v in kwargs.items():
            if k == 'resource_id':
                if elem.get('resource-id') != v: match = False; break
            elif k == 'content_desc':
                if elem.get('content-desc') != v: match = False; break
            elif k == 'text':
                if elem.get('text') != v: match = False; break
            elif k == 'text_contains':
                if v not in elem.get('text', ''): match = False; break
        if match:
            return elem
    return None

def get_center(bounds_str):
    import re
    m = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
    if len(m) == 2:
        x1, y1 = int(m[0][0]), int(m[0][1])
        x2, y2 = int(m[1][0]), int(m[1][1])
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def fill_proxy_config(port, serial, item):
    print(f"[*] Nhập cấu hình proxy mới vào máy {serial}...")
    # Bấm dấu +
    root = dump_ui(port, serial)
    add_btn = find_node(root, content_desc="Add configuration") or find_node(root, resource_id="com.v2ray.ang:id/action_add")
    if add_btn:
        cx, cy = get_center(add_btn.get('bounds'))
        adb_cmd(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
    else:
        adb_cmd(port, serial, ["shell", "input", "tap", "911", "136"])
    time.sleep(1)

    # Chọn Type manually[HTTP]
    root = dump_ui(port, serial)
    http_opt = find_node(root, text_contains="HTTP") or find_node(root, text="Type manually[HTTP]")
    if http_opt:
        cx, cy = get_center(http_opt.get('bounds'))
        adb_cmd(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
    else:
        adb_cmd(port, serial, ["shell", "input", "tap", "500", "1018"])
    time.sleep(1.5)

    # Remarks
    adb_cmd(port, serial, ["shell", "input", "tap", "500", "460"])
    time.sleep(0.3)
    adb_cmd(port, serial, ["shell", "input", "text", item["name"]])
    time.sleep(0.3)

    # Address (IP)
    adb_cmd(port, serial, ["shell", "input", "tap", "500", "670"])
    time.sleep(0.3)
    adb_cmd(port, serial, ["shell", "input", "text", item["ip"]])
    time.sleep(0.3)

    # Port
    adb_cmd(port, serial, ["shell", "input", "tap", "500", "880"])
    time.sleep(0.3)
    for _ in range(5):
        adb_cmd(port, serial, ["shell", "input", "keyevent", "67"])
    adb_cmd(port, serial, ["shell", "input", "text", item["proxy_port"]])
    time.sleep(0.3)

    # User
    adb_cmd(port, serial, ["shell", "input", "tap", "500", "1090"])
    time.sleep(0.3)
    adb_cmd(port, serial, ["shell", "input", "text", item["user"]])
    time.sleep(0.3)

    # Password
    adb_cmd(port, serial, ["shell", "input", "tap", "500", "1300"])
    time.sleep(0.3)
    adb_cmd(port, serial, ["shell", "input", "text", item["pass"]])
    time.sleep(0.3)

    # Đóng bàn phím
    adb_cmd(port, serial, ["shell", "input", "keyevent", "111"])
    time.sleep(0.5)

    # Save
    adb_cmd(port, serial, ["shell", "input", "tap", "1016", "136"])
    time.sleep(1.5)

def activate_proxy(item):
    port = item["port"]
    serial = item["serial"]
    name = item["name"]
    ip = item["ip"]
    print(f"\n--- Xử lý Máy {item['id']} ({serial}) - {name} ({ip}:{item['proxy_port']}) ---")
    
    # 1. Cố định portrait
    adb_cmd(port, serial, ["shell", "settings", "put", "system", "accelerometer_rotation", "0"])
    adb_cmd(port, serial, ["shell", "settings", "put", "system", "user_rotation", "0"])
    
    # 2. Mở v2rayNG
    adb_cmd(port, serial, ["shell", "am", "start", "-n", "com.v2ray.ang/com.v2ray.ang.ui.MainActivity"])
    time.sleep(1.5)
    
    root = dump_ui(port, serial)
    if root is None:
        print("[-] Không đọc được UI")
        return False
        
    # Kiểm tra xem cấu hình đã có chưa
    config_node = find_node(root, text_contains=name) or find_node(root, text_contains=ip)
    if not config_node:
        print(f"[!] Chưa có cấu hình {name}, đang tiến hành nạp...")
        fill_proxy_config(port, serial, item)
        time.sleep(1.5)
        root = dump_ui(port, serial)
    else:
        print(f"[+] Đã có sẵn cấu hình {name}")
        
    # Chọn cấu hình đó nếu có
    config_node = find_node(root, text_contains=name) or find_node(root, text_contains=ip)
    if config_node:
        cx, cy = get_center(config_node.get('bounds'))
        adb_cmd(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
        time.sleep(0.5)

    # Kiểm tra nút FAB Start / Stop
    fab_node = find_node(root, resource_id="com.v2ray.ang:id/fab")
    if fab_node:
        desc = fab_node.get('content-desc', '')
        if 'Stop' in desc:
            print(f"[✓] Proxy {name} đang CHẠY (Connected)!")
            return True
        else:
            print(f"[*] Bấm nút Start Service...")
            cx, cy = get_center(fab_node.get('bounds'))
            adb_cmd(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
            time.sleep(2)
            
            # Xử lý dialog cấp quyền VPN nếu có
            root_after = dump_ui(port, serial)
            ok_btn = find_node(root_after, text="OK") or find_node(root_after, text="Ok") or find_node(root_after, resource_id="android:id/button1")
            if ok_btn:
                print("[!] Cấp quyền VPN Connection...")
                cx, cy = get_center(ok_btn.get('bounds'))
                adb_cmd(port, serial, ["shell", "input", "tap", str(cx), str(cy)])
                time.sleep(2)
    else:
        # Nhấp tọa độ mặc định của FAB
        print("[*] Nhấp tọa độ FAB mặc định (964, 1925)...")
        adb_cmd(port, serial, ["shell", "input", "tap", "964", "1925"])
        time.sleep(2)

    # Kiểm tra tiến trình
    ps_res = adb_cmd(port, serial, ["shell", "ps", "-A"])
    is_live = "RunSoLibV2RayDaemon" in ps_res
    print(f"[{'✓' if is_live else 'X'}] Trạng thái v2ray Daemon trên máy {serial}: {'ĐANG CHẠY' if is_live else 'CHƯA CHẠY'}")
    return is_live

def main():
    print("==================================================")
    print("     KÍCH HOẠT / ĐĂNG NHẬP 5 PROXY LÊN 5 MÁY      ")
    print("==================================================")
    for p in PROXIES:
        try:
            activate_proxy(p)
        except Exception as e:
            print(f"[-] Lỗi trên máy {p['serial']}: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
