import sys
import time
import subprocess
import re
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

GOLIKE_DEVICE = "9889da304447393259"
TIKTOK_DEVICE = "ce031713dba2c72101"
ADB_PORT = "5037"

def adb(dev, *args):
    cmd = ["adb", "-P", ADB_PORT, "-s", dev] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return res.stdout.strip()

def tap(dev, x, y):
    adb(dev, "shell", "input", "tap", str(x), str(y))

def dump_ui(dev):
    out = adb(dev, "exec-out", "uiautomator", "dump", "/dev/tty")
    if "<?xml" in out:
        out = out[out.find("<?xml"):]
        if "</hierarchy>" in out:
            out = out[:out.find("</hierarchy>") + 12]
        try:
            return ET.fromstring(out)
        except Exception as e:
            print("XML parse err:", e)
    return None

def find_nodes(root, tag_filter=None, text_pattern=None, desc_pattern=None):
    results = []
    if root is None:
        return results
    for node in root.iter('node'):
        cls = node.attrib.get('class', '')
        text = node.attrib.get('text', '')
        desc = node.attrib.get('content-desc', '')
        bounds = node.attrib.get('bounds', '')
        
        if tag_filter and tag_filter.lower() not in cls.lower():
            continue
        if text_pattern and not re.search(text_pattern, text, re.IGNORECASE):
            continue
        if desc_pattern and not re.search(desc_pattern, desc, re.IGNORECASE):
            continue
            
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            results.append({
                'class': cls,
                'text': text,
                'desc': desc,
                'bounds': (x1, y1, x2, y2),
                'center': (cx, cy),
                'checked': node.attrib.get('checked', 'false') == 'true'
            })
    return results

def print_screen_summary(dev):
    root = dump_ui(dev)
    if not root:
        print(f"[{dev}] Failed to dump UI")
        return
    print(f"=== UI Elements on {dev} ===")
    for node in root.iter('node'):
        text = node.attrib.get('text', '')
        desc = node.attrib.get('content-desc', '')
        bounds = node.attrib.get('bounds', '')
        cls = node.attrib.get('class', '')
        if (text or desc or 'edittext' in cls.lower() or 'button' in cls.lower()) and bounds != '[0,0][1080,2220]':
            print(f"  {cls} | txt='{text}' | desc='{desc}' | bounds={bounds}")

if __name__ == '__main__':
    print_screen_summary(GOLIKE_DEVICE)
