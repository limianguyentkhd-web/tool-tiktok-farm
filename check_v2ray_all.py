import subprocess, time

ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

devices_map = [
    (5038, '9889da304447393259'),
    (5038, '988a17344c564b5657'),
    (5037, 'ce01182188dbdcee0c'),
    (5037, 'ce011821c38b263b05'),
    (5038, 'ce011821c45dc4060c'),
    (5037, 'ce031713dba2c72101'), # May mau
    (5038, '9889db393438353953'),
    (5037, 'ce031713ed1e10540d'),
    (5037, 'ce041714a5547e3202'),
    (5037, 'ce0517150b75dcb80c'),
    (5037, 'ce051715eaf458370d'),
    (5037, 'ce0718274d93800c01'),
    (5038, 'ce0328219b0be8f50d'),
    (5038, 'ce04171425efd0f10d'),
    (5038, 'ce0417146b840c3104'),
    (5038, 'ce10182a1b5c4f2405'),
    (5038, 'ce11171b2823ef0a04'),
]

for port, dev in devices_map:
    subprocess.run([ADB, '-P', str(port), '-s', dev, 'shell', 'am start -n com.v2ray.ang/com.v2ray.ang.ui.MainActivity'], capture_output=True)
    time.sleep(1)
    dump_path = f"/sdcard/dump_{dev[:4]}.xml"
    subprocess.run([ADB, '-P', str(port), '-s', dev, 'shell', f'uiautomator dump {dump_path}'], capture_output=True)
    local_path = f"d:/TOOL TIKTOK/dump_{dev[:4]}.xml"
    subprocess.run([ADB, '-P', str(port), '-s', dev, 'pull', dump_path, local_path], capture_output=True)
    
    proxy_found = "None"
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for marker in ['Proxy_1', 'Proxy_2', 'Proxy_3', 'Proxy_4', 'Proxy_5', '160.', '157.', 'http']:
            if marker in content:
                proxy_found = marker
                break
    except:
        pass
        
    r = subprocess.run([ADB, '-P', str(port), '-s', dev, 'shell', 'ps -A | grep -i v2ray'], capture_output=True, text=True)
    running = 'RunSoLib' in r.stdout
    print(f"Port {port} | Dev {dev} | Running: {running} | Config: {proxy_found}")
