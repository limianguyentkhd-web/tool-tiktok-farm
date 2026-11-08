import os
import sys
import glob

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from video_uploader import TikTokVideoUploader

def test_post():
    target_serial = "ce031713dba2c72101"
    files = glob.glob(r"d:\TOOL TIKTOK\videos\ready_*.mp4")
    if not files:
        print("[-] Không tìm thấy file video nào trong videos!")
        return

    # Chọn video đầu tiên (ready_1)
    chosen_video = files[0]
    print(f"[*] Đã chọn video: {os.path.basename(chosen_video)}")

    uploader = TikTokVideoUploader()
    # Cho AI tự sinh caption dựa theo tên video hoặc dùng auto
    success = uploader.upload_video(
        serial=target_serial,
        local_video_path=chosen_video,
        caption="auto"
    )

    if success:
        print("[+] 🎉 Đăng bài thử nghiệm thành công lên máy", target_serial)
    else:
        print("[-] ⚠️ Đăng bài chưa thành công, vui lòng kiểm tra lại màn hình máy.")

if __name__ == '__main__':
    test_post()
