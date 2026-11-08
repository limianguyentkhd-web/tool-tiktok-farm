import os, sys, subprocess, imageio_ffmpeg, re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

raw_dir = r"D:\TOOL TIKTOK\raw_videos"

for f in os.listdir(raw_dir):
    if not f.endswith(".mp4"):
        continue
    p = os.path.join(raw_dir, f)
    cmd = [ffmpeg, "-i", p]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    
    has_audio = "Audio:" in res.stderr
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    dur = dur_match.group(0) if dur_match else "Unknown"
    print(f"{f}")
    print(f"  {dur} | Has Audio: {has_audio}")
