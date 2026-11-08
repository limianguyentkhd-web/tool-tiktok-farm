import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

targets = [
    ('May 3', 'ce01182188dbdcee0c', '5037', 'u0_a228'),
    ('May 4', 'ce011821c38b263b05', '5037', 'u0_a232'),
    ('May 5', 'ce011821c45dc4060c', '5038', 'u0_a228'),
]

tar_path = r'd:\TOOL TIKTOK\golike_data.tar'

for name, serial, port, uid in targets:
    print(f"Setting up {name} ({serial})...")
    subprocess.run(['adb', '-P', port, '-s', serial, 'shell', 'am', 'force-stop', 'com.golike'])
    subprocess.run(['adb', '-P', port, '-s', serial, 'push', tar_path, '/sdcard/golike_data.tar'])
    restore_cmd = f"sh -c 'cd /data/data/com.golike && tar -xf /sdcard/golike_data.tar && chown -R {uid}:{uid} .'"
    subprocess.run(['adb', '-P', port, '-s', serial, 'shell', 'su', '-c', restore_cmd])
    subprocess.run(['adb', '-P', port, '-s', serial, 'shell', 'settings', 'put', 'system', 'accelerometer_rotation', '0'])
    subprocess.run(['adb', '-P', port, '-s', serial, 'shell', 'settings', 'put', 'system', 'user_rotation', '0'])
    subprocess.run(['adb', '-P', port, '-s', serial, 'shell', 'monkey', '-p', 'com.golike', '1'], capture_output=True)
    print(f"{name} setup completed!")

time.sleep(3)
print("All 3 devices configured!")
