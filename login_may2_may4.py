import urllib.request
import ssl
import json
import time
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
ADB = r"C:\Program Files (x86)\xiaowei_android\tools\adb.exe"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def adb(port, serial, cmd_list):
    full = [ADB, "-P", str(port), "-s", serial] + cmd_list
    res = subprocess.run(full, capture_output=True, text=True, errors="replace")
    return res.stdout.strip()

def get_otp(email, email_pwd, max_wait=60):
    print(f"[*] Đang chờ mã OTP gửi tới {email}...")
    start = time.time()
    seen = set()
    # first fetch to establish baseline
    try:
        url = f"https://megacloudx.com/api/messages?inbox={email}&password={email_pwd}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        for item in data.get('results', []):
            seen.add(item.get('id'))
    except Exception as e:
        print(f"[-] Init fetch err: {e}")

    while time.time() - start < max_wait:
        time.sleep(4)
        try:
            url = f"https://megacloudx.com/api/messages?inbox={email}&password={email_pwd}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, context=ctx, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            for item in data.get('results', []):
                mid = item.get('id')
                subj = item.get('subject', '')
                if mid not in seen:
                    m = re.search(r'\b(\d{6})\b', subj)
                    if m:
                        code = m.group(1)
                        print(f"[+] Tìm thấy OTP MỚI: {code} (Tiêu đề: {subj})")
                        return code
                    else:
                        print(f"[*] Tin nhắn mới nhận: {subj}")
        except Exception as e:
            print(f"[-] Fetch retry: {e}")

    # Fallback: check most recent message
    try:
        url = f"https://megacloudx.com/api/messages?inbox={email}&password={email_pwd}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        for item in data.get('results', []):
            subj = item.get('subject', '')
            m = re.search(r'\b(\d{6})\b', subj)
            if m:
                print(f"[+] Fallback OTP từ tin nhắn gần nhất: {m.group(1)}")
                return m.group(1)
    except:
        pass
    return None

def login_device(port, serial, username, password, email, email_pwd):
    print(f"\n=======================================================")
    print(f"🚀 ĐĂNG NHẬP CHO MÁY {serial} (Port: {port})")
    print(f"Username: {username} | Email: {email}")
    print(f"=======================================================")

    # Ensure TikTok is open and on login dialog
    adb(port, serial, ["shell", "input", "tap", "540", "1070"]) # Tap 'Continue with email / username'
    time.sleep(3)

    # Tap tab 'Email / Username' at top right
    adb(port, serial, ["shell", "input", "tap", "750", "280"])
    time.sleep(2)

    # Tap Username field (middle)
    adb(port, serial, ["shell", "input", "tap", "400", "420"])
    time.sleep(1)
    adb(port, serial, ["shell", "input", "text", username])
    time.sleep(1)

    # Tap Password field
    adb(port, serial, ["shell", "input", "tap", "400", "550"])
    time.sleep(1)
    # Escaping special characters for adb text
    clean_pwd = password.replace('@', r'\@')
    adb(port, serial, ["shell", "input", "text", clean_pwd])
    time.sleep(1)

    # Tap Log In button
    adb(port, serial, ["shell", "input", "tap", "540", "750"])
    time.sleep(5)

    # Check if OTP screen appeared
    print("[*] Đang kiểm tra OTP...")
    otp = get_otp(email, email_pwd, max_wait=30)
    if otp:
        print(f"[+] Điền OTP {otp} vào máy {serial}...")
        adb(port, serial, ["shell", "input", "text", otp])
        time.sleep(5)
    
    # Check screen
    adb(port, serial, ["shell", "screencap", "-p", f"/sdcard/login_result.png"])
    adb(port, serial, ["pull", f"/sdcard/login_result.png", f"d:\\TOOL TIKTOK\\login_{serial}.png"])
    print(f"[+] Đã hoàn tất xử lý cho máy {serial}!")

if __name__ == '__main__':
    # May 2
    login_device(5038, "988a17344c564b5657", "user84009697968164", "@L88jTPasitdUg", "dluvzhltaf7199@megacloudx.com", "QcfAqqhXI")
    time.sleep(3)
    # May 4
    login_device(5037, "ce011821c38b263b05", "user5878212175691", "@L206ThnU0ortn", "lcqskhcot3161@primehubcloud.com", "wQMUXKm4I")
