import os, sys
sys.path.append(r"D:\TOOL TIKTOK")
from auto_reup_processor import AutoReupProcessor

processor = AutoReupProcessor()
input_file = r"D:\TOOL TIKTOK\raw_videos\Những tình tiết hài hước trong Avengers #shorts_wa19sR8qlgk.mp4"
output_file = r"D:\TOOL TIKTOK\videos\ready_avengers_funny.mp4"

print("Starting fresh anti-reup render...")
success = processor.process_video(
    input_path=input_file,
    output_path=output_file,
    hflip=False,
    speed_range=(1.03, 1.05),
    zoom_range=(1.03, 1.05),
    trim_head_range=(0.5, 0.9),
    trim_tail_range=(0.8, 1.3)
)

if success:
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"SUCCESS: Rendered {output_file} ({size_mb:.2f} MB)")
else:
    print("FAILED to render video")
