import subprocess
import xml.etree.ElementTree as ET
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
device = 'ce031713dba2c72101'

subprocess.run(['adb', '-s', device, 'shell', 'uiautomator', 'dump', '/data/local/tmp/dump_check.xml'])
out = subprocess.check_output(['adb', '-s', device, 'shell', 'cat', '/data/local/tmp/dump_check.xml']).decode('utf-8', errors='ignore')
root = ET.fromstring(out)

for n in root.iter():
    cls = n.attrib.get('class', '')
    txt = n.attrib.get('text', '')
    desc = n.attrib.get('content-desc', '')
    bounds = n.attrib.get('bounds', '')
    if cls == 'android.widget.Button' or 'tiktok' in txt.lower() or 'tiktok' in desc.lower():
        m = re.findall(r'\d+', bounds)
        cx = (int(m[0]) + int(m[2])) // 2 if len(m) == 4 else 0
        cy = (int(m[1]) + int(m[3])) // 2 if len(m) == 4 else 0
        print(f'{cls} | txt="{txt}" | desc="{desc}" | center=({cx}, {cy}) | bounds={bounds}')
