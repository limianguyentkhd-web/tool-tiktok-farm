import os
import random
import re
import subprocess
import sys
import imageio_ffmpeg

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
bgm_path = r"d:\TOOL TIKTOK\nhac_viet_bgm.mp3"
raw_dir = r"d:\TOOL TIKTOK\raw_videos\douyin_ootd_5vids"
ready_dir = r"d:\TOOL TIKTOK\videos\ootd_5vids_ready"
os.makedirs(ready_dir, exist_ok=True)

configs = [
    {
        'tag': 'may1',
        'raw_file': os.path.join(raw_dir, 'may1_7697173178645603803.mp4'),
        'bgm_start': 0,
        'trim_start': 0.2,
        'duration': 6.0,
    },
    {
        'tag': 'may2',
        'raw_file': os.path.join(raw_dir, 'may2_7690745570076825050.mp4'),
        'bgm_start': 15,
        'trim_start': 0.2,
        'duration': 5.0,
    },
    {
        'tag': 'may3',
        'raw_file': os.path.join(raw_dir, 'may3_7700576071301859226.mp4'),
        'bgm_start': 30,
        'trim_start': 0.2,
        'duration': 5.5,
    },
    {
        'tag': 'may4',
        'raw_file': os.path.join(raw_dir, 'may4_clean.mp4'),
        'bgm_start': 45,
        'trim_start': 0.5,
        'duration': 6.5,
    },
    {
        'tag': 'may5',
        'raw_file': os.path.join(raw_dir, 'may5_7700174739202113458.mp4'),
        'bgm_start': 65,
        'trim_start': 5.0, # đoạn đẹp của vlog
        'duration': 7.0,
    },
]

print("========================================================")
print("🎬 BẮT ĐẦU XỬ LÝ 5 VIDEO KHÁC NHAU + NHẠC VIỆT TRENDING")
print("========================================================")

output_files = []

for cfg in configs:
    tag = cfg['tag']
    raw_p = cfg['raw_file']
    out_p = os.path.join(ready_dir, f"{tag}_ootd_vietmusic.mp4")
    
    speed = round(random.uniform(1.03, 1.05), 3)
    pts = round(1.0 / speed, 4)
    zoom = round(random.uniform(1.03, 1.05), 3)
    contrast = round(random.uniform(1.02, 1.05), 3)
    brightness = round(random.uniform(-0.01, 0.02), 3)
    saturation = round(random.uniform(1.03, 1.06), 3)
    
    # Bộ lọc video: lật gương + zoom/crop + chỉnh màu + tốc độ
    vf = f"hflip,scale={zoom}*iw:{zoom}*ih,crop=iw/{zoom}:ih/{zoom},eq=contrast={contrast}:brightness={brightness}:saturation={saturation},setpts={pts}*PTS"
    
    dur = cfg['duration']
    bgm_s = cfg['bgm_start']
    t_start = cfg['trim_start']

    print(f"\n[*] Đang render {tag}...")
    print(f"    Raw: {os.path.basename(raw_p)}")
    print(f"    BGM Việt cắt từ giây thứ: {bgm_s}s | Độ dài video: {dur}s")

    cmd = [
        ffmpeg, "-y",
        "-ss", str(t_start),
        "-i", raw_p,
        "-ss", str(bgm_s),
        "-i", bgm_path,
        "-t", str(dur),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-map_metadata", "-1",
        out_p
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0 and os.path.isfile(out_p):
        sz_mb = os.path.getsize(out_p) / (1024*1024)
        print(f"    ✅ Hoàn thành: {out_p} ({sz_mb:.2f} MB)")
        output_files.append((tag, out_p))
    else:
        print(f"    ❌ Lỗi render {tag}: {res.stderr[-300:]}")

print("\n========================================================")
print(f"🎉 TỔNG KẾT: ĐÃ XUẤT THÀNH CÔNG {len(output_files)}/5 VIDEO MỚI + NHẠC VIỆT!")
for tag, p in output_files:
    print(f" - {tag}: {p} ({os.path.getsize(p)} bytes)")
print("========================================================")
