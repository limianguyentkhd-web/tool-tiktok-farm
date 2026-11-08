import subprocess
import time
import xml.etree.ElementTree as ET
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
DEV = '9889da304447393259'

def sh(cmd):
    return subprocess.run(['adb', '-s', DEV, 'shell'] + cmd.split(' '), capture_output=True, text=True, errors='ignore').stdout

def tap(x, y):
    sh(f'input tap {x} {y}')
    time.sleep(1.5)

def get_elements():
    subprocess.run(['adb', '-s', DEV, 'shell', 'uiautomator', 'dump', '/data/local/tmp/dump.xml'], capture_output=True)
    res = subprocess.run(['adb', '-s', DEV, 'shell', 'cat', '/data/local/tmp/dump.xml'], capture_output=True)
    xml_data = res.stdout.decode('utf-8', errors='ignore')
    root = ET.fromstring(xml_data)
    elements = []
    for node in root.iter('node'):
        cd = node.attrib.get('content-desc', '').strip()
        txt = node.attrib.get('text', '').strip()
        cls = node.attrib.get('class', '')
        b = node.attrib.get('bounds', '')
        clickable = node.attrib.get('clickable', 'false') == 'true'
        if cd or txt:
            elements.append({'text': txt, 'desc': cd, 'class': cls, 'bounds': b, 'clickable': clickable})
    return elements

def print_screen_summary(title):
    print(f"\n==================== {title} ====================")
    elems = get_elements()
    for el in elems:
        val = el['desc'] if el['desc'] else el['text']
        val = val.replace('\n', ' | ')
        print(f"[{el['class'].split('.')[-1]}] (clickable={el['clickable']}, bounds={el['bounds']}): {val[:120]}")

# Currently on whatever was tapped:
print_screen_summary("CURRENT SCREEN (after tapping Kiem Tien)")
