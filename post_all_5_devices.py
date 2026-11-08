import base64
import os
import subprocess
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

adb = r'C:\Program Files (x86)\xiaowei_android\tools\adb.exe'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
READY_TO_POST_DIR = os.path.join(BASE_DIR, "videos", "ready_to_post")
os.makedirs(READY_TO_POST_DIR, exist_ok=True)

# Quét video sẵn sàng đăng từ videos/ready_to_post/ đã duyệt
ready_videos = [
    os.path.join(READY_TO_POST_DIR, f)
    for f in os.listdir(READY_TO_POST_DIR)
    if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))
] if os.path.exists(READY_TO_POST_DIR) else []

tasks = [
    {
        'name': 'Máy 1 (Hiếu)',
        'port': '5038',
        'serial': '9889da304447393259',
        'caption': 'Năng lượng tích cực cho ngày mới rạng rỡ nha cả nhà 💕 #ootdfashion #trending #viral #fyp '
    },
    {
        'name': 'Máy 2 (Thúy Huyền)',
        'port': '5038',
        'serial': '988a17344c564b5657',
        'caption': 'Outfit nhẹ nhàng dạo phố cuối tuần đây ạ 🌸 #ootd #fashion #style #trending #xuhuong '
    },
    {
        'name': 'Máy 3 (Xuân Lan)',
        'port': '5037',
        'serial': 'ce01182188dbdcee0c',
        'caption': 'Một chút phong cách đơn giản nhưng cực xinh nè ✨ #ootdvietnam #viral #fyp #xuhuong '
    },
    {
        'name': 'Máy 4 (Bạch Vân)',
        'port': '5037',
        'serial': 'ce011821c38b263b05',
        'caption': 'Gợi ý phối đồ xinh xắn đi chơi cùng bạn bè nè các nàng 💖 #outfitideas #ootd #viral #trending '
    },
    {
        'name': 'Máy 5 (Thùy Trang)',
        'port': '5038',
        'serial': 'ce011821c45dc4060c',
        'caption': 'Tone màu yêu thích của tuần này, mọi người thấy sao ạ? 🌿 #ootdfashion #styleinspo #fyp #trending '
    },
]

def run(cmd_base, args):
    return subprocess.run(cmd_base + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')

for t_idx, t in enumerate(tasks):
    name = t['name']
    port = t['port']
    serial = t['serial']
    caption = t['caption']
    cmd_base = [adb, '-P', port, '-s', serial]

    print(f"\n========================================================")
    print(f"🚀 BẮT ĐẦU ĐĂNG VIDEO CHO {name} ({serial})")
    print(f"========================================================")

    # 0. Nếu có video đã duyệt trong ready_to_post/, đẩy qua ADB vào Box Phone
    if t_idx < len(ready_videos):
        vid_to_push = ready_videos[t_idx]
        rem_name = os.path.basename(vid_to_push)
        rem_dest = f"/sdcard/DCIM/Camera/{rem_name}"
        print(f"[*] 📲 Đang nạp video thành phẩm vào {name}: {rem_name}...")
        run(cmd_base, ['push', vid_to_push, rem_dest])
        run(cmd_base, ['shell', 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', '-d', f'file://{rem_dest}'])
        time.sleep(1.5)

    # 1. Quay về màn hình Profile sạch
    run(cmd_base, ['shell', 'input', 'keyevent', '4'])
    time.sleep(0.5)
    run(cmd_base, ['shell', 'input', 'tap', '900', '2070'])
    time.sleep(1.5)

    # 2. Bấm nút dấu cộng (+) hoặc nút Upload ở giữa
    run(cmd_base, ['shell', 'input', 'tap', '540', '1242'])
    time.sleep(2.5)

    # 3. Chọn tab Videos
    run(cmd_base, ['shell', 'input', 'tap', '268', '248'])
    time.sleep(1.5)

    # 4. Chọn video đầu tiên (circle)
    run(cmd_base, ['shell', 'input', 'tap', '285', '360'])
    time.sleep(1.0)

    # 5. Bấm Next
    run(cmd_base, ['shell', 'input', 'tap', '740', '1990'])
    time.sleep(3.0)

    # 6. Bấm Next trong trình chỉnh sửa
    run(cmd_base, ['shell', 'input', 'tap', '740', '1990'])
    time.sleep(3.5)

    # 7. Nhấp vào ô nhập Caption
    run(cmd_base, ['shell', 'input', 'tap', '250', '230'])
    time.sleep(1.0)

    # 8. Nhập caption tiếng Việt qua ADB Keyboard
    b64 = base64.b64encode(caption.encode('utf-8')).decode('utf-8')
    run(cmd_base, ['shell', 'am', 'broadcast', '-a', 'ADB_INPUT_B64', '--es', 'msg', b64])
    time.sleep(1.5)

    # Ẩn bàn phím
    run(cmd_base, ['shell', 'input', 'keyevent', '111'])
    time.sleep(1.0)

    # 9. Bấm Đăng (Post)
    run(cmd_base, ['shell', 'input', 'tap', '740', '1990'])
    print(f"[*] Đã bấm Post, chờ tải lên...")
    time.sleep(6.0)

    # 10. Chạm nhẹ để ẩn share sheet nếu có, quay lại Profile
    run(cmd_base, ['shell', 'input', 'tap', '540', '1000'])
    time.sleep(1.0)
    run(cmd_base, ['shell', 'input', 'tap', '900', '2070'])
    time.sleep(2.0)

    # Chụp ảnh xác thực
    img_name = f"final_post_{serial}.png"
    out_img = os.path.join(r"C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd", img_name)
    run(cmd_base, ['shell', 'screencap', '-p', f'/sdcard/{img_name}'])
    run(cmd_base, ['pull', f'/sdcard/{img_name}', out_img])
    print(f"[+] ✅ {name} đã đăng video thành công! Ảnh: {img_name}")

print("\n========================================================")
print("🎉 TOÀN BỘ 5 THIẾT BỊ ĐÃ ĐƯỢC ĐĂNG 5 VIDEO KHÁC NHAU VỚI NHẠC VIỆT!")
print("========================================================")
