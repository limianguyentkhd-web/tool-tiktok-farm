import xml.etree.ElementTree as ET
tree = ET.parse('d:/TOOL TIKTOK/cam_ui.xml')
for n in tree.iter():
    if n.get('clickable') == 'true':
        print(f"{n.get('class')} | text='{n.get('text')}' | desc='{n.get('content-desc')}' | id='{n.get('resource-id')}' | bounds={n.get('bounds')}")
