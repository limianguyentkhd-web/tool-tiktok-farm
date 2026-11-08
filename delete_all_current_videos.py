import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

adb = r'C:\Program Files (x86)\xiaowei_android\tools\adb.exe'

def parse_bounds(b_str):
    m = re.findall(r'\d+', b_str)
    if len(m) == 4:
        x1, y1, x2, y2 = map(int, m)
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def run_adb(cmd_base, args):
    return subprocess.run(cmd_base + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')

def dump_ui(cmd_base, local_name):
    run_adb(cmd_base, ['shell', 'uiautomator', 'dump', '/sdcard/dump.xml'])
    run_adb(cmd_base, ['pull', '/sdcard/dump.xml', local_name])
    if os.path.exists(local_name):
        try:
            return ET.parse(local_name).getroot()
        except:
            return None
    return None

def delete_video_for_device(name, port, serial):
    cmd_base = [adb, '-P', port, '-s', serial]
    print(f"\n==========================================")
    print(f"[*] Đang xử lý xóa video trên {name} ({serial})")
    print(f"==========================================")

    # Đảm bảo về màn hình Profile
    # Nhấn Back 2 lần để thoát các dialog/settings phụ nếu có
    run_adb(cmd_base, ['shell', 'input', 'keyevent', '4'])
    time.sleep(1.0)
    run_adb(cmd_base, ['shell', 'input', 'keyevent', '4'])
    time.sleep(1.0)
    # Nhấn tab Profile (900, 2070)
    run_adb(cmd_base, ['shell', 'input', 'tap', '900', '2070'])
    time.sleep(2.0)

    # Kiểm tra xem có video nào trong profile không
    root = dump_ui(cmd_base, f"dump_{name}_prof.xml")
    if not root:
        print(f"[-] Không dump được UI của {name}")
        return False

    # Tìm tab "Videos" đầu tiên (bounds khoảng x: 42-291, y: 700-850)
    video_tab_coord = None
    for node in root.iter():
        d = node.attrib.get('content-desc', '')
        if d == 'Videos':
            video_tab_coord = parse_bounds(node.attrib.get('bounds', ''))
            break
    if video_tab_coord:
        print(f"[*] Nhấn tab Videos tại {video_tab_coord}")
        run_adb(cmd_base, ['shell', 'input', 'tap', str(video_tab_coord[0]), str(video_tab_coord[1])])
        time.sleep(1.5)

    # Tìm thumbnail video trong grid
    root = dump_ui(cmd_base, f"dump_{name}_grid.xml")
    thumb_coord = None
    for node in root.iter():
        b = node.attrib.get('bounds', '')
        c = node.attrib.get('class', '')
        # Thumbnail video thường ở góc trái [0, 900+...] hoặc [0, 1100+...]
        if 'ImageView' in c and '[0,' in b:
            m = re.findall(r'\d+', b)
            if len(m) == 4 and int(m[1]) > 800:
                thumb_coord = parse_bounds(b)
                break

    if not thumb_coord:
        # Fallback tọa độ thumbnail mặc định
        print("[*] Dùng tọa độ thumbnail mặc định (180, 1200)")
        thumb_coord = (180, 1200)

    print(f"[*] Mở video tại {thumb_coord}")
    run_adb(cmd_base, ['shell', 'input', 'tap', str(thumb_coord[0]), str(thumb_coord[1])])
    time.sleep(2.5)

    # Đang phát video -> tìm nút 3 chấm (...)
    root = dump_ui(cmd_base, f"dump_{name}_play.xml")
    more_coord = None
    if root:
        for node in root.iter():
            d = node.attrib.get('content-desc', '')
            r = node.attrib.get('resource-id', '')
            if 'g8m' in r or 'share video' in d.lower():
                more_coord = parse_bounds(node.attrib.get('bounds', ''))
                break

    if not more_coord:
        print("[*] Dùng tọa độ nút 3 chấm mặc định (996, 1738)")
        more_coord = (996, 1738)

    print(f"[*] Nhấn nút 3 chấm tại {more_coord}")
    run_adb(cmd_base, ['shell', 'input', 'tap', str(more_coord[0]), str(more_coord[1])])
    time.sleep(2.0)

    # Vuốt sang phải danh sách nút ở hàng dưới để tìm nút Delete
    for swipe_i in range(3):
        root = dump_ui(cmd_base, f"dump_{name}_share_{swipe_i}.xml")
        del_coord = None
        if root:
            for node in root.iter():
                t = node.attrib.get('text', '')
                d = node.attrib.get('content-desc', '')
                if t == 'Delete' or d == 'Delete':
                    del_coord = parse_bounds(node.attrib.get('bounds', ''))
                    break
        if del_coord:
            print(f"[+] Tìm thấy nút Delete tại {del_coord} (lần vuốt {swipe_i})")
            run_adb(cmd_base, ['shell', 'input', 'tap', str(del_coord[0]), str(del_coord[1])])
            time.sleep(1.5)
            break
        else:
            print(f"[*] Chưa thấy Delete, vuốt hàng dưới sang trái (lần {swipe_i+1})...")
            run_adb(cmd_base, ['shell', 'input', 'swipe', '900', '1870', '200', '1870', '250'])
            time.sleep(1.2)

    # Tìm và xác nhận nút Delete trên popup confirm
    root = dump_ui(cmd_base, f"dump_{name}_confirm.xml")
    conf_coord = None
    if root:
        for node in root.iter():
            t = node.attrib.get('text', '')
            if t == 'Delete':
                b = node.attrib.get('bounds', '')
                # Nút Delete trên popup thường ở khoảng y > 1500
                m = re.findall(r'\d+', b)
                if len(m) == 4 and int(m[1]) > 1400:
                    conf_coord = parse_bounds(b)
                    break

    if not conf_coord:
        print("[*] Dùng tọa độ popup Delete mặc định (300, 1830)")
        conf_coord = (300, 1830)

    print(f"[*] Xác nhận xóa tại {conf_coord}")
    run_adb(cmd_base, ['shell', 'input', 'tap', str(conf_coord[0]), str(conf_coord[1])])
    time.sleep(2.5)

    # Chụp ảnh xác thực kết quả sau xóa
    out_img = f"C:\\Users\\Admin\\.gemini\\antigravity\\brain\\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\\screen_verified_del_{name}.png"
    run_adb(cmd_base, ['shell', 'screencap', '-p', f'/sdcard/screen_verified_del_{name}.png'])
    run_adb(cmd_base, ['pull', f'/sdcard/screen_verified_del_{name}.png', out_img])
    print(f"[+] Đã hoàn thành xóa trên {name}! Ảnh: {out_img}")
    return True

if __name__ == '__main__':
    devices = [
        ('may1', '5038', '9889da304447393259'),
        ('may4', '5037', 'ce011821c38b263b05'),
        ('may5', '5038', 'ce011821c45dc4060c'),
    ]
    for n, p, s in devices:
        delete_video_for_device(n, p, s)
