import subprocess, re, sys
sys.stdout.reconfigure(encoding='utf-8')
serial = '9889da304447393259'
subprocess.run(['adb', '-s', serial, 'shell', 'uiautomator', 'dump', '/sdcard/login_ui.xml'], capture_output=True)
subprocess.run(['adb', '-s', serial, 'pull', '/sdcard/login_ui.xml', 'login_ui.xml'], capture_output=True)
with open('login_ui.xml', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'<node [^>]*?text="([^"]*)"[^>]*?resource-id="([^"]*)"[^>]*?class="([^"]*)"[^>]*?bounds="([^"]*)"'
for m in re.finditer(pattern, text):
    t, r, c, b = m.groups()
    if t or 'EditText' in c or 'Button' in c:
        print(f"Class: {c.split('.')[-1]:15} | Text: {t[:25]:25} | Res: {r.split('/')[-1]:20} | Bounds: {b}")
