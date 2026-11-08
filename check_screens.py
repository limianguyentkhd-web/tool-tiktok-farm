import subprocess
import os

adb_path = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"
art_dir = r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd"

devices = [
    ("May 1", "5038", "9889da304447393259", "now_m1.png"),
    ("May 2", "5038", "988a17344c564b5657", "now_m2.png"),
    ("May 3", "5037", "ce01182188dbdcee0c", "now_m3.png"),
    ("May 4", "5037", "ce011821c38b263b05", "now_m4.png"),
    ("May 5", "5038", "ce011821c45dc4060c", "now_m5.png"),
]

for name, port, serial, outfile in devices:
    outpath = os.path.join(art_dir, outfile)
    cmd = [adb_path, "-P", port, "-s", serial, "exec-out", "screencap", "-p"]
    with open(outpath, "wb") as f:
        subprocess.run(cmd, stdout=f)
    print(f"Captured {name} to {outfile}")
