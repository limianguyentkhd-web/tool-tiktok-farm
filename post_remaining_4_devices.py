import base64
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

TASKS = [
    {
        "id": 2,
        "name": "Máy 2",
        "port": "5038",
        "serial": "988a17344c564b5657",
        "new_user": "thuyhuyen.ootd",
        "video": r"D:\TOOL TIKTOK\videos\ootd_douyin\ready_may2_ootd.mp4",
        "caption": "Đơn giản mà vẫn cực kỳ cuốn hút 🌿 Mọi người thấy set này thế nào? #outfit #xuhuongtiktok #douyin #viral"
    },
    {
        "id": 3,
        "name": "Máy 3",
        "port": "5037",
        "serial": "ce01182188dbdcee0c",
        "new_user": "minhtuan.vibes",
        "video": r"D:\TOOL TIKTOK\videos\ootd_douyin\ready_may3_ootd.mp4",
        "caption": "Một chút năng lượng tích cực cho ngày mới nè các bác ơi 💕 #ootdfashion #trending #viral #fyp"
    },
    {
        "id": 4,
        "name": "Máy 4",
        "port": "5037",
        "serial": "ce011821c38b263b05",
        "new_user": "habarbie.style",
        "video": r"D:\TOOL TIKTOK\videos\ootd_douyin\ready_may4_ootd.mp4",
        "caption": "Set đồ basic nhưng lên dáng cực kỳ tôn da nha 🌸 #reviewthoitrang #xuhuong #ootdvietnam #douyin"
    },
    {
        "id": 5,
        "name": "Máy 5",
        "port": "5038",
        "serial": "ce011821c45dc4060c",
        "new_user": "thuytrang.daily",
        "video": r"D:\TOOL TIKTOK\videos\ootd_douyin\ready_may5_ootd.mp4",
        "caption": "Outfit đi cafe chụp ảnh sống ảo siêu xinh nè các nàng ✨ #outfitoftheday #phoidoxinh #trending #douyin"
    }
]

def adb(port, serial, cmd_list):
    full = [ADB, "-P", port, "-s", serial] + cmd_list
    res = subprocess.run(full, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()

def send_vietnamese(port, serial, text):
    adb(port, serial, ["shell", "ime", "enable", "com.android.adbkeyboard/.AdbIME"])
    adb(port, serial, ["shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"])
    b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    adb(port, serial, ["shell", "am", "broadcast", "-a", "ADB_INPUT_B64", "--es", "msg", b64])

def process_device(t):
    port = t["port"]
    serial = t["serial"]
    name = t["name"]
    new_user = t["new_user"]
    video_path = t["video"]
    caption = t["caption"]

    print(f"\n=======================================================")
    print(f"🚀 XỬ LÝ {name} [{serial}] (Port: {port})")
    print(f"Username mới: @{new_user}")
    print(f"Video: {os.path.basename(video_path)}")
    print(f"=======================================================")

    # 1. Đẩy video vào thư mục DCIM/Camera và quét MediaStore
    remote_path = f"/sdcard/DCIM/Camera/vid_ootd_may{t['id']}.mp4"
    adb(port, serial, ["push", video_path, remote_path])
    adb(port, serial, ["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote_path}"])
    adb(port, serial, ["shell", "content", "call", "--uri", "content://media/external/file", "--method", "scan_file", "--arg", remote_path])
    print(f"[{name}] ✅ Đã nạp video vào Camera và kích hoạt MediaScanner.")

    # 2. Mở TikTok từ đầu
    adb(port, serial, ["shell", "am", "force-stop", "com.zhiliaoapp.musically"])
    time.sleep(1.0)
    adb(port, serial, ["shell", "monkey", "-p", "com.zhiliaoapp.musically", "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(4.0)

    # Đóng popups nếu có
    adb(port, serial, ["shell", "input", "tap", "980", "150"]) # dismiss potential popups
    time.sleep(1.0)

    # 3. Đổi username nếu cần:
    print(f"[{name}] ⚙️  Đang đổi Username sang: @{new_user}...")
    # Bấm Profile tab (980, 2030)
    adb(port, serial, ["shell", "input", "tap", "980", "2030"])
    time.sleep(2.0)
    # Bấm Edit profile (bút chì góc trên trái: 70, 130)
    adb(port, serial, ["shell", "input", "tap", "70", "130"])
    time.sleep(2.0)
    # Bấm ô Username (540, 830)
    adb(port, serial, ["shell", "input", "tap", "540", "830"])
    time.sleep(2.0)

    # Xóa username cũ: Ctrl+A rồi DEL
    adb(port, serial, ["shell", "input", "keycombination", "113", "29"])
    time.sleep(0.5)
    adb(port, serial, ["shell", "input", "keyevent", "67"])
    time.sleep(0.5)
    # Gõ username mới
    adb(port, serial, ["shell", "input", "text", new_user])
    time.sleep(1.0)
    # Bấm Save ở góc trên bên phải (920, 95)
    adb(port, serial, ["shell", "input", "tap", "920", "95"])
    time.sleep(2.0)
    # Bấm Confirm trên dialog (670, 1220)
    adb(port, serial, ["shell", "input", "tap", "670", "1220"])
    time.sleep(2.0)
    # Bấm Back về Profile
    adb(port, serial, ["shell", "input", "keyevent", "4"])
    time.sleep(1.0)

    # 4. Đăng video
    print(f"[{name}] 🎬 Đang tiến hành đăng video...")
    # Bấm nút Tạo (+) ở giữa (540, 2030)
    adb(port, serial, ["shell", "input", "tap", "540", "2030"])
    time.sleep(3.0)
    # Bấm Album/Upload (90, 1980)
    adb(port, serial, ["shell", "input", "tap", "90", "1980"])
    time.sleep(2.5)
    # Bấm tab Videos (370, 248)
    adb(port, serial, ["shell", "input", "tap", "370", "248"])
    time.sleep(1.5)
    # Chọn vòng tròn tick video đầu tiên (290, 380)
    adb(port, serial, ["shell", "input", "tap", "290", "380"])
    time.sleep(1.0)
    # Bấm Tiếp (Next (1)) ở góc dưới phải (740, 1990)
    adb(port, serial, ["shell", "input", "tap", "740", "1990"])
    time.sleep(4.0)
    # Màn hình Editor: bấm Tiếp (Next) (740, 1990)
    adb(port, serial, ["shell", "input", "tap", "740", "1990"])
    time.sleep(3.5)

    # Màn hình Đăng: Chạm ô Add description (350, 150)
    print(f"[{name}] ✍️  Nhập caption: {caption}")
    adb(port, serial, ["shell", "input", "tap", "350", "150"])
    time.sleep(1.0)
    send_vietnamese(port, serial, caption + " ")
    time.sleep(1.5)
    # Ẩn bàn phím (ESC)
    adb(port, serial, ["shell", "input", "keyevent", "111"])
    time.sleep(1.0)
    # Bấm ĐĂNG (Post) (740, 1990)
    print(f"[{name}] 🚀 Bấm nút ĐĂNG (Post)...")
    adb(port, serial, ["shell", "input", "tap", "740", "1990"])
    time.sleep(5.0)

    # Dismiss popups nếu có (Cancel / Don't allow / X)
    adb(port, serial, ["shell", "input", "tap", "300", "880"])
    time.sleep(1.0)
    adb(port, serial, ["shell", "input", "tap", "330", "1280"])
    time.sleep(1.0)

    # Chụp ảnh xác thực
    sc_remote = f"/sdcard/result_{name}.png"
    adb(port, serial, ["shell", "screencap", "-p", sc_remote])
    adb(port, serial, ["pull", sc_remote, f"d:\\TOOL TIKTOK\\result_{name}.png"])
    print(f"[{name}] 🎉 Hoàn tất đăng video và đổi username thành công!")

if __name__ == '__main__':
    for task in TASKS:
        try:
            process_device(task)
            time.sleep(3)
        except Exception as e:
            print(f"[-] Lỗi xử lý {task['name']}: {e}")
