import subprocess
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

devices = [
    ('May 1', '9889da304447393259', '5037'),
    ('May 2', '988a17344c564b5657', '5037'),
    ('May 3', 'ce01182188dbdcee0c', '5037'),
    ('May 4', 'ce011821c38b263b05', '5037'),
    ('May 5', 'ce011821c45dc4060c', '5038'),
    ('May 6', 'ce031713ed1e10540d', '5037')
]

for name, s, port in devices:
    cmd = ['adb', '-P', port, '-s', s, 'shell', 'su -c "strings /data/data/com.golike/app_webview/Default/Local\\ Storage/leveldb/*.ldb /data/data/com.golike/app_webview/Default/Local\\ Storage/leveldb/*.log 2>/dev/null | grep -E \\"username|email|authorization\\""']
    p = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
    out = p.stdout.strip()
    # find username or authorization
    usernames = set(re.findall(r'"username":"([^"]+)"', out))
    print(f'{name} ({s}): usernames in localstorage={usernames}')
