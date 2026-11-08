import xml.etree.ElementTree as ET
tree = ET.parse(r"d:\TOOL TIKTOK\uidump.xml")
for e in tree.iter():
    d = (e.attrib.get('content-desc') or '').lower()
    t = (e.attrib.get('text') or '').lower()
    b = e.attrib.get('bounds')
    if 'more' in d or 'share' in d or 'delete' in d or 'more' in t:
        print(f"[{b}] desc='{d}' text='{t}'")
