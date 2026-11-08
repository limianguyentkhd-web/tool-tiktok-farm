import xml.etree.ElementTree as ET
tree = ET.parse('d:/TOOL TIKTOK/ui_input.xml')
for n in tree.iter():
    t = n.get('text', '')
    c = n.get('class', '')
    b = n.get('bounds', '')
    rid = n.get('resource-id', '')
    if t or 'Edit' in c or 'Button' in c:
        print(f'{c} | text="{t}" | id="{rid}" | bounds={b}')
