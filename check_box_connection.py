import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("1. ADB 5037:")
r1 = subprocess.run(["adb", "-P", "5037", "devices"], capture_output=True, text=True).stdout
print(r1.strip())

print("\n2. ADB 5038:")
r2 = subprocess.run([r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe", "-P", "5038", "devices"], capture_output=True, text=True).stdout
print(r2.strip())

print("\n3. Hardware PNP Check:")
out = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-PnpDevice -PresentOnly | Select-Object Status, Class, FriendlyName, InstanceId | ConvertTo-Json -Depth 2"], capture_output=True, text=True).stdout

try:
    data = json.loads(out)
    if isinstance(data, list):
        print(f"Total present devices: {len(data)}")
        matched = []
        for d in data:
            name = str(d.get("FriendlyName", ""))
            inst = str(d.get("InstanceId", ""))
            cls = str(d.get("Class", ""))
            status = str(d.get("Status", ""))
            combined = (name + " " + inst + " " + cls).lower()
            if any(k in combined for k in ["samsung", "android", "ch340", "1a86", "serial", "hub", "composite"]):
                matched.append(f"{status} | {cls} | {name} | {inst}")
        for m in matched:
            print("  ", m)
except Exception as e:
    print("JSON parse error:", e)
