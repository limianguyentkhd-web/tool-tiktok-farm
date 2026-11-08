import subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8')

devices = [
    ("May 1", "9889da304447393259", 5037),
    ("May 2", "988a17344c564b5657", 5037),
    ("May 3", "ce01182188dbdcee0c", 5037),
    ("May 4", "ce011821c38b263b05", 5037),
    ("May 5", "ce011821c45dc4060c", 5038),
    ("May 6", "ce031713ed1e10540d", 5037),
]

for name, s, p in devices:
    res = subprocess.run(f'adb -P {p} -s {s} shell su -c "cat /data/data/com.golike/app_webview/Default/Local\\ Storage/leveldb/*.log" 2>nul', shell=True, capture_output=True, text=True, errors='ignore')
    # search for username or email
    text = res.stdout
    print(f"=== {name} ({s}) ===")
    import re
    # look for "username":"..." or "name":"..."
    matches = re.findall(r'"username":"([^"]+)"', text)
    if not matches:
        matches = re.findall(r'"name":"([^"]+)"', text)
    print("Found names/usernames:", set(matches[:5]))
