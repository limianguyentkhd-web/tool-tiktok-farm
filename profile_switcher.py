"""
Mô-đun Quản lý & Chuyển đổi Tài khoản Siêu Tốc (Account Profile Switcher) cho TikTok Farm.
Cơ chế:
1. Đăng nhập 1 lần -> Lưu lại Profile dữ liệu (/sdcard/TikTokProfiles/{tên_profile}.tar.gz).
2. Khi cần đổi nick: Xóa data hiện tại -> Nạp Profile nick mới chỉ mất 1 giây!
3. Hoàn toàn không bao giờ bị hỏi mật khẩu hay Captcha.
4. Mỗi máy có thể lưu 5 - 10 profile nick độc lập, không bị liên đới tài khoản.
"""

import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PKG = "com.zhiliaoapp.musically"
PROFILE_DIR = "/sdcard/TikTokProfiles"


def _get_adb_base(serial: Optional[str], port: str = "5037") -> list:
    cmd = ["adb"]
    if port != "5037":
        cmd.extend(["-P", port])
    if serial:
        cmd.extend(["-s", serial])
    return cmd


def backup_account_profile(serial: str, profile_name: str, port: str = "5037") -> bool:
    """
    Sao lưu tài khoản TikTok đang đăng nhập trên máy thành file profile nén.
    """
    safe_name = profile_name.strip().replace(" ", "_")
    base = _get_adb_base(serial, port)

    # Đóng app để đảm bảo dữ liệu ghi trọn vẹn vào ổ cứng
    subprocess.run(base + ["shell", "am", "force-stop", PKG], capture_output=True)

    # Tạo thư mục lưu trữ và nén data đăng nhập (shared_prefs, databases, files)
    script = f"""
    mkdir -p {PROFILE_DIR}
    cd /data/data/{PKG}
    tar -czf {PROFILE_DIR}/{safe_name}.tar.gz shared_prefs databases files
    ls -lh {PROFILE_DIR}/{safe_name}.tar.gz
    """

    p = subprocess.Popen(base + ["shell", "su"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(input=script)

    if f"{safe_name}.tar.gz" in out:
        print(f"[+] [{serial}] ĐÃ BACKUP THÀNH CÔNG PROFILE '{safe_name}'! ✅")
        return True
    else:
        print(f"[-] [{serial}] Backup thất bại: {err or out} ❌")
        return False


def switch_to_profile(serial: str, profile_name: str, port: str = "5037") -> bool:
    """
    Chuyển đổi sang tài khoản khác trong vòng 1 giây:
    - Xóa trắng data cũ.
    - Bung profile tương ứng.
    - Phục hồi quyền sở hữu (chown).
    - Khởi động TikTok lên thẳng nick đã chọn (không pass, không captcha).
    """
    safe_name = profile_name.strip().replace(" ", "_")
    base = _get_adb_base(serial, port)

    # Kịch bản khôi phục phiên đăng nhập bằng quyền root
    script = f"""
    am force-stop {PKG}
    if [ ! -f "{PROFILE_DIR}/{safe_name}.tar.gz" ]; then
        echo "NOT_FOUND"
        exit 1
    fi

    APP_UID=$(stat -c %u /data/data/{PKG})
    APP_GID=$(stat -c %g /data/data/{PKG})

    # Xóa sạch data hiện tại
    rm -rf /data/data/{PKG}/shared_prefs
    rm -rf /data/data/{PKG}/databases
    rm -rf /data/data/{PKG}/files

    # Bung dữ liệu profile mới
    tar -xzf {PROFILE_DIR}/{safe_name}.tar.gz -C /data/data/{PKG}/

    # Cấp lại quyền cho app TikTok
    chown -R $APP_UID:$APP_GID /data/data/{PKG}/shared_prefs /data/data/{PKG}/databases /data/data/{PKG}/files
    chmod -R 771 /data/data/{PKG}/shared_prefs /data/data/{PKG}/databases /data/data/{PKG}/files

    echo "SWITCH_SUCCESS"
    """

    p = subprocess.Popen(base + ["shell", "su"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(input=script)

    if "SWITCH_SUCCESS" in out:
        print(f"[+] [{serial}] ĐÃ CHUYỂN THÀNH CÔNG SANG NICK '{safe_name}'! 🚀")
        # Khởi động TikTok lên thẳng giao diện
        subprocess.run(base + ["shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True)
        return True
    elif "NOT_FOUND" in out:
        print(f"[-] [{serial}] Không tìm thấy file profile '{safe_name}' trên máy này! ❌")
        return False
    else:
        print(f"[-] [{serial}] Lỗi khi chuyển nick: {err or out} ❌")
        return False


def new_blank_session(serial: str, port: str = "5037") -> None:
    """
    Xóa trắng dữ liệu TikTok và tạo mã Android ID mới ngẫu nhiên.
    Sẵn sàng cho việc đăng nhập 1 nick hoàn toàn mới mà không dính dấu vết cũ.
    """
    import random
    new_id = "".join(random.choices("0123456789abcdef", k=16))
    base = _get_adb_base(serial, port)

    subprocess.run(base + ["shell", "am", "force-stop", PKG], capture_output=True)
    subprocess.run(base + ["shell", "pm", "clear", PKG], capture_output=True)
    subprocess.run(base + ["shell", "su", "-c", f"settings put secure android_id {new_id}"], capture_output=True)
    subprocess.run(base + ["shell", "settings", "put", "secure", "immersive_mode_confirmations", "confirmed"], capture_output=True)

    print(f"[+] [{serial}] Đã làm sạch TikTok & cấp Android ID mới ({new_id}). Sẵn sàng nạp nick mới!")


def list_device_profiles(serial: str, port: str = "5037") -> List[str]:
    """Xem danh sách các profile nick đang lưu trữ trên máy."""
    base = _get_adb_base(serial, port)
    res = subprocess.run(base + ["shell", "su", "-c", f"ls -1 {PROFILE_DIR}/*.tar.gz 2>/dev/null"], capture_output=True, text=True)
    lines = res.stdout.strip().split("\n")
    profiles = []
    for line in lines:
        line = line.strip()
        if line and line.endswith(".tar.gz"):
            fname = os.path.basename(line).replace(".tar.gz", "")
            profiles.append(fname)
    return profiles


def switch_all_devices_to_profile(profile_name: str, devices: List[Tuple[str, str]]):
    """Chuyển đồng loạt toàn bộ 17 máy sang cùng 1 bộ Profile (ví dụ ca sáng chuyển Nick_Ca_1, ca tối chuyển Nick_Ca_2)."""
    print(f"[*] Đang chuyển đồng loạt {len(devices)} máy sang Profile: '{profile_name}'...")
    with ThreadPoolExecutor(max_workers=min(len(devices), 17)) as executor:
        futures = [executor.submit(switch_to_profile, dev, profile_name, port) for dev, port in devices]
        for f in futures:
            f.result()
    print(f"[+] Hoàn tất chuyển đổi tài khoản cho toàn bộ dàn máy!")


if __name__ == "__main__":
    print("[*] Test Profile Switcher...")
