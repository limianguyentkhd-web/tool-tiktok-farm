import subprocess, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

raw_dir = r"D:\TOOL TIKTOK\raw_videos"
for f in os.listdir(raw_dir):
    if not f.endswith(".mp4"):
        continue
    p = os.path.join(raw_dir, f)
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", p]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    try:
        d = json.loads(res.stdout)
        v = next((s for s in d.get("streams", []) if s["codec_type"] == "video"), None)
        a = next((s for s in d.get("streams", []) if s["codec_type"] == "audio"), None)
        dur = float(d.get("format", {}).get("duration", 0))
        print(f"{f}")
        print(f"  Duration: {dur:.2f}s | Video: {v['codec_name'] if v else 'None'} ({v['width'] if v else 0}x{v['height'] if v else 0}) | Audio: {a['codec_name'] if a else 'NO AUDIO'}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
