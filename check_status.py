import subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8')

devices = [
    {"name": "May 1", "serial": "9889da304447393259", "port": "5037"},
    {"name": "May 2", "serial": "988a17344c564b5657", "port": "5037"},
    {"name": "May 3", "serial": "ce01182188dbdcee0c", "port": "5037"},
    {"name": "May 4", "serial": "ce011821c38b263b05", "port": "5037"},
    {"name": "May 5", "serial": "ce011821c45dc4060c", "port": "5038"},
    {"name": "May 6", "serial": "ce031713ed1e10540d", "port": "5037"},
]

for d in devices:
    cmd = f"adb -P {d['port']} -s {d['serial']} shell dumpsys window | findstr mCurrentFocus"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = res.stdout.strip()
    print(f"{d['name']} ({d['serial']}): {out}")
