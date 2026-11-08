import sys
import subprocess
import time
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
PORT = "5039"
SERIAL = "9889da304447393259"

def run_adb(args):
    return subprocess.run(["adb", "-P", PORT, "-s", SERIAL] + args, capture_output=True, text=True)

def tap(x, y):
    run_adb(["shell", "input", "tap", str(x), str(y)])
    time.sleep(1)

print("Tap vào radio chọn mail tại (840, 650)...")
tap(840, 650)
time.sleep(1)

run_adb(["shell", "uiautomator", "dump", "/sdcard/ui_radio.xml"])
run_adb(["pull", "/sdcard/ui_radio.xml", "ui_radio.xml"])

tree = ET.parse("ui_radio.xml")
for node in tree.getroot().iter():
    t = node.attrib.get("text", "")
    d = node.attrib.get("content-desc", "")
    b = node.attrib.get("bounds", "")
    if any(k in (t+d).lower() for k in ["next", "primehubcloud", "support"]):
        print(f"{t!r} | {d!r} | {b}")
