import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')
DEV = '9889da304447393259'

def sh(cmd):
    return subprocess.run(['adb', '-s', DEV, 'shell'] + cmd, capture_output=True, text=True).stdout

# 1. Tap input field
print("Tapping input field...")
sh(['input', 'tap', '1050', '580'])
time.sleep(1)

# 2. Input TikTok profile link
link = 'https://www.tiktok.com/@hieunh.daily26'
print(f"Typing link: {link}")
sh(['input', 'text', link])
time.sleep(1)

# 3. Swipe up inside dialog (from 800 to 200)
print("Swiping up to reveal Kết nối button...")
sh(['input', 'swipe', '1000', '800', '1000', '200', '300'])
time.sleep(1)

# Dump UI to see exactly where Kết nối is
sh(['uiautomator', 'dump', '/sdcard/dump_add.xml'])
subprocess.run(['adb', '-s', DEV, 'pull', '/sdcard/dump_add.xml', 'dump_add.xml'], capture_output=True)

import xml.etree.ElementTree as ET
tree = ET.parse('dump_add.xml')
target_btn = None
for node in tree.iter():
    t = node.attrib.get('text', '') or node.attrib.get('content-desc', '')
    b = node.attrib.get('bounds', '')
    if 'Kết nối' in t:
        print(f"Found button: {t} at {b}")
        target_btn = b
        break

if target_btn:
    import re
    m = re.findall(r'\d+', target_btn)
    if len(m) == 4:
        cx = (int(m[0]) + int(m[2])) // 2
        cy = (int(m[1]) + int(m[3])) // 2
        print(f"Tapping Kết nối at ({cx}, {cy})...")
        sh(['input', 'tap', str(cx), str(cy)])
        time.sleep(3)

subprocess.run(['cmd', '/c', f'adb -s {DEV} exec-out screencap -p > bumx_add_result2.png'])
print("Done!")
