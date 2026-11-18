import subprocess, time, base64, sys, os, re

sys.stdout.reconfigure(encoding='utf-8')

SERIAL = '9889da304447393259' # May_04

def adb(args):
    cmd = ['adb', '-s', SERIAL] + args
    return subprocess.run(cmd, capture_output=True, text=True, errors='replace')

def tap(x, y, delay=1.5):
    adb(['shell', 'input', 'tap', str(x), str(y)])
    time.sleep(delay)

print("[*] 1. Setting AdbIME on May_04...")
adb(['shell', 'ime', 'set', 'com.android.adbkeyboard/.AdbIME'])

print("[*] 2. Opening TikTok...")
adb(['shell', 'monkey', '-p', 'com.zhiliaoapp.musically', '-c', 'android.intent.category.LAUNCHER', '1'])
time.sleep(4)

print("[*] 3. Navigating to Profile (tap x=1000, y=2040)...")
tap(1000, 2040, delay=2.5)

# Check if on Profile screen, find Edit profile button or Name
subprocess.run(['adb', '-s', SERIAL, 'shell', 'uiautomator', 'dump', '/sdcard/profile.xml'])
subprocess.run(['adb', '-s', SERIAL, 'pull', '/sdcard/profile.xml', r'D:\TOOL TIKTOK\m4_profile.xml'])

import xml.etree.ElementTree as ET
tree = ET.parse(r'D:\TOOL TIKTOK\m4_profile.xml')
edit_profile_bounds = None
for node in tree.iter():
    t = node.attrib.get('text', '')
    d = node.attrib.get('content-desc', '')
    if 'edit profile' in (t + d).lower() or 'sửa hồ sơ' in (t + d).lower():
        edit_profile_bounds = node.attrib.get('bounds')
        print(f"Found Edit Profile button: {edit_profile_bounds}")
        break

if edit_profile_bounds:
    # Parse bounds [x1, y1][x2, y2]
    import re
    m = re.findall(r'\d+', edit_profile_bounds)
    if m:
        cx = (int(m[0]) + int(m[2])) // 2
        cy = (int(m[1]) + int(m[3])) // 2
        print(f"[*] Tapping Edit Profile at ({cx}, {cy})...")
        tap(cx, cy, delay=2.5)
else:
    print("[*] Edit Profile button not found by text, tapping default position (350, 600)...")
    tap(350, 600, delay=2.5)

# Now in Edit Profile screen, dump to find Name field
subprocess.run(['adb', '-s', SERIAL, 'shell', 'uiautomator', 'dump', '/sdcard/edit.xml'])
subprocess.run(['adb', '-s', SERIAL, 'pull', '/sdcard/edit.xml', r'D:\TOOL TIKTOK\m4_edit.xml'])

tree = ET.parse(r'D:\TOOL TIKTOK\m4_edit.xml')
name_bounds = None
for node in tree.iter():
    t = node.attrib.get('text', '')
    d = node.attrib.get('content-desc', '')
    if t == 'Name' or 'tên' in t.lower() or 'Xem Gi Hom Nay' in t or 'xem gi' in t.lower():
        name_bounds = node.attrib.get('bounds')
        print(f"Found Name row: {t} at {name_bounds}")
        break

if name_bounds:
    m = re.findall(r'\d+', name_bounds)
    if m:
        cx = (int(m[0]) + int(m[2])) // 2
        cy = (int(m[1]) + int(m[3])) // 2
        tap(cx, cy, delay=2.0)
else:
    print("[*] Tapping default Name position (600, 724)...")
    tap(600, 724, delay=2.0)

# In Name edit screen, clear text
subprocess.run(['adb', '-s', SERIAL, 'shell', 'uiautomator', 'dump', '/sdcard/name_edit.xml'])
subprocess.run(['adb', '-s', SERIAL, 'pull', '/sdcard/name_edit.xml', r'D:\TOOL TIKTOK\m4_name_edit.xml'])
tree = ET.parse(r'D:\TOOL TIKTOK\m4_name_edit.xml')

# Find clear button or EditText
clear_btn = None
save_btn = None
for node in tree.iter():
    t = node.attrib.get('text', '')
    d = node.attrib.get('content-desc', '')
    b = node.attrib.get('bounds')
    if 'clear' in (t + d).lower() or 'xóa' in (t + d).lower():
        clear_btn = b
    if 'save' in (t + d).lower() or 'lưu' in (t + d).lower():
        save_btn = b

if clear_btn:
    m = re.findall(r'\d+', clear_btn)
    tap((int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2, delay=1.0)
else:
    # Select all and delete or tap clear icon at right of edittext
    tap(975, 506, delay=0.6)

# Send B64 text "Xem Gì Hôm Nay"
TARGET_NAME = "Xem Gì Hôm Nay"
b64_msg = base64.b64encode(TARGET_NAME.encode('utf-8')).decode('utf-8')
print(f"[*] Sending Unicode Vietnamese text: '{TARGET_NAME}' (b64: {b64_msg})...")
adb(['shell', 'am', 'broadcast', '-a', 'ADB_INPUT_B64', '--es', 'msg', b64_msg])
time.sleep(1.5)

# Find and tap Save button
if save_btn:
    m = re.findall(r'\d+', save_btn)
    tap((int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2, delay=2.0)
else:
    tap(990, 121, delay=2.0)

# Check for Confirm dialog
subprocess.run(['adb', '-s', SERIAL, 'shell', 'uiautomator', 'dump', '/sdcard/confirm.xml'])
subprocess.run(['adb', '-s', SERIAL, 'pull', '/sdcard/confirm.xml', r'D:\TOOL TIKTOK\m4_confirm.xml'])
tree = ET.parse(r'D:\TOOL TIKTOK\m4_confirm.xml')
for node in tree.iter():
    t = node.attrib.get('text', '')
    d = node.attrib.get('content-desc', '')
    if any(k in (t + d).lower() for k in ['confirm', 'xác nhận', 'save name', 'save']):
        b = node.attrib.get('bounds')
        print(f"Found Confirm button: {t} at {b}")
        m = re.findall(r'\d+', b)
        if m:
            tap((int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2, delay=2.0)
            break

# Take screenshot to verify
subprocess.run(['adb', '-s', SERIAL, 'shell', 'screencap', '-p', '/sdcard/after_rename.png'])
subprocess.run(['adb', '-s', SERIAL, 'pull', '/sdcard/after_rename.png', r'D:\TOOL TIKTOK\m4_after_rename.png'])
print("[+] Finished renaming May_04. Screenshot saved at D:\\TOOL TIKTOK\\m4_after_rename.png")
