import subprocess
import time
import random
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
DEV = 'ce031713ed1e10540d'

print("[May 6] Warmup daemon with auto-popup killer started!")

while True:
    try:
        # Check and kill popups
        subprocess.run(f"adb -s {DEV} shell uiautomator dump /sdcard/dump_m6.xml", shell=True, capture_output=True, timeout=8)
        subprocess.run(f"adb -s {DEV} pull /sdcard/dump_m6.xml dump_m6_local.xml", shell=True, capture_output=True, timeout=8)
        try:
            tree = ET.parse("dump_m6_local.xml")
            for n in tree.iter():
                t = n.attrib.get('text', '')
                if any(k in t for k in ["Got it", "Agree", "Đồng ý", "Not now", "Lúc khác"]):
                    b = n.attrib.get('bounds')
                    import re
                    m = re.findall(r'\d+', b)
                    if len(m) == 4:
                        cx, cy = (int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2
                        print(f"[May 6] Bấm đóng popup '{t}' tại ({cx}, {cy})...")
                        subprocess.run(f"adb -s {DEV} shell input tap {cx} {cy}", shell=True)
                        time.sleep(1)
        except Exception:
            pass

        watch_sec = random.randint(9, 20)
        time.sleep(watch_sec)

        if random.random() < 0.35:
            subprocess.run(f"adb -s {DEV} shell input tap 540 1000", shell=True)
            time.sleep(0.12)
            subprocess.run(f"adb -s {DEV} shell input tap 540 1000", shell=True)

        subprocess.run(f"adb -s {DEV} shell input swipe 540 1600 540 400 350", shell=True)
    except Exception as e:
        time.sleep(5)
