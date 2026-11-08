import subprocess
import tarfile
import re
import os

# Pull leveldb from 9889da304447393259
cmd = "adb -P 5037 -s 9889da304447393259 shell \"su -c 'tar -cf /sdcard/ls.tar /data/data/com.golike/app_webview/'\""
subprocess.run(cmd, shell=True)

subprocess.run(["adb", "-P", "5037", "-s", "9889da304447393259", "pull", "/sdcard/ls.tar", "d:/TOOL TIKTOK/ls.tar"])

if os.path.exists("d:/TOOL TIKTOK/ls.tar"):
    try:
        t = tarfile.open("d:/TOOL TIKTOK/ls.tar")
        tokens = set()
        for m in t.getmembers():
            if m.isfile() and ('leveldb' in m.name or 'LocalStorage' in m.name or 'Cookies' in m.name):
                f = t.extractfile(m)
                if f:
                    content = f.read()
                    found = re.findall(rb'eyJ[a-zA-Z0-9_\-]{20,}\.[a-zA-Z0-9_\-]{20,}\.[a-zA-Z0-9_\-]+', content)
                    for tok in found:
                        tokens.add(tok.decode())
        print(f"Found {len(tokens)} JWT tokens:")
        for tok in tokens:
            print(tok)
    except Exception as e:
        print("Tar error:", e)
