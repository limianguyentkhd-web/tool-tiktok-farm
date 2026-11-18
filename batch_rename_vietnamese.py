import subprocess, time, base64, sys, re, xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

def rename_device(serial, new_name):
    print(f"\n========================================================")
    print(f"[*] ĐỔI TÊN TIẾNG VIỆT CÓ DẤU TRÊN SERIAL: {serial}")
    print(f"[*] Tên mới: '{new_name}'")
    print(f"========================================================")
    
    # 1. Set AdbIME
    subprocess.run(['adb', '-s', serial, 'shell', 'ime', 'set', 'com.android.adbkeyboard/.AdbIME'])
    
    # 2. Open TikTok
    subprocess.run(['adb', '-s', serial, 'shell', 'monkey', '-p', 'com.zhiliaoapp.musically', '-c', 'android.intent.category.LAUNCHER', '1'])
    time.sleep(3.5)
    
    # 3. Tap Profile tab (x=1000, y=2040)
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', '1000', '2040'])
    time.sleep(2.0)
    
    # 4. Tap Edit Profile pencil icon at (186, 131)
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', '186', '131'])
    time.sleep(2.5)
    
    # 5. Tap Name row (x=540, y=724)
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', '540', '724'])
    time.sleep(2.0)
    
    # Dump to check cooldown or Name input field
    subprocess.run(['adb', '-s', serial, 'shell', 'uiautomator', 'dump', '/sdcard/name_chk.xml'])
    subprocess.run(['adb', '-s', serial, 'pull', '/sdcard/name_chk.xml', r'D:\TOOL TIKTOK\name_chk.xml'])
    
    tree = ET.parse(r'D:\TOOL TIKTOK\name_chk.xml')
    cooldown = False
    for node in tree.iter():
        t = node.attrib.get('text', '')
        if 'after' in t.lower() or '7 days' in t.lower() and ('november' in t.lower() or 'tháng' in t.lower()):
            print(f"[-] Thông báo giới hạn 7 ngày: {t}")
            cooldown = True
            break
            
    if cooldown:
        print(f"[-] Máy {serial} đang trong thời gian giãn cách 7 ngày, nhấn Cancel quay lại.")
        subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', '108', '121'])
        return False
        
    # 6. Tap Clear button at (975, 506)
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', '975', '506'])
    time.sleep(1.0)
    
    # 7. Broadcast Unicode B64 text
    b64 = base64.b64encode(new_name.encode('utf-8')).decode('utf-8')
    print(f"[*] Đang gửi tên có dấu: '{new_name}' (B64: {b64})...")
    subprocess.run(['adb', '-s', serial, 'shell', 'am', 'broadcast', '-a', 'ADB_INPUT_B64', '--es', 'msg', b64])
    time.sleep(1.5)
    
    # 8. Tap Save (990, 121)
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', '990', '121'])
    time.sleep(2.0)
    
    # 9. Tap Confirm if dialog appears
    subprocess.run(['adb', '-s', serial, 'shell', 'uiautomator', 'dump', '/sdcard/confirm.xml'])
    subprocess.run(['adb', '-s', serial, 'pull', '/sdcard/confirm.xml', r'D:\TOOL TIKTOK\name_confirm.xml'])
    tree = ET.parse(r'D:\TOOL TIKTOK\name_confirm.xml')
    for node in tree.iter():
        t = node.attrib.get('text', '')
        if any(k in t.lower() for k in ['confirm', 'save', 'xác nhận']):
            b = node.attrib.get('bounds')
            m = re.findall(r'\d+', b)
            if m:
                cx = (int(m[0]) + int(m[2])) // 2
                cy = (int(m[1]) + int(m[3])) // 2
                print(f"[*] Bấm nút xác nhận {t} tại ({cx}, {cy})...")
                subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', str(cx), str(cy)])
                time.sleep(1.5)
                break
                
    print(f"[+] Hoàn tất đổi tên trên {serial} thành '{new_name}'!")
    return True

if __name__ == '__main__':
    targets = [
        ('ce0328219b0be8f50d', 'Bóng Đá 24H'),      # May_10
        ('ce04171425efd0f10d', 'Kỳ Quan Công Nghệ')  # May_11
    ]
    for s, name in targets:
        rename_device(s, name)
