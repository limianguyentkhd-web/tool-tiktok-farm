import os, sys, subprocess, imageio_ffmpeg

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
out_dir = r"C:\Users\Admin\.gemini\antigravity\brain\23e5b22c-cb4a-460b-87c2-9d7174dacd5f"

v1 = r"D:\TOOL TIKTOK\raw_videos\Chi tiết thú vị trong Avengers #shorts_qk3pEXQ43aA.mp4"
v2 = r"D:\TOOL TIKTOK\raw_videos\Những tình tiết hài hước trong Avengers #shorts_wa19sR8qlgk.mp4"

subprocess.run([ffmpeg, "-y", "-ss", "00:00:05", "-i", v1, "-vframes", "1", os.path.join(out_dir, "sample_v1.jpg")])
subprocess.run([ffmpeg, "-y", "-ss", "00:00:05", "-i", v2, "-vframes", "1", os.path.join(out_dir, "sample_v2.jpg")])
print("Extracted sample frames")
