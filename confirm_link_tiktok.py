import subprocess, time, sys, base64
sys.stdout.reconfigure(encoding='utf-8')

serial = '9889da304447393259'

def tap(x, y):
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', str(x), str(y)])
    time.sleep(1)

def input_b64(text):
    b64 = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    subprocess.run(['adb', '-s', serial, 'shell', 'am', 'broadcast', '-a', 'ADB_INPUT_B64', '--es', 'msg', b64])
    time.sleep(1)

def capture(name):
    subprocess.run(['adb', '-s', serial, 'exec-out', 'screencap', '-p'], 
                   stdout=open(rf'C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\{name}', 'wb'))

print("1. Focusing TikTok ID input field at (450, 1480)...")
tap(450, 1480)

print("2. Entering TikTok ID hieunh.daily26...")
input_b64('hieunh.daily26')

print("3. Dismissing keyboard...")
tap(500, 200)
time.sleep(1)

capture('tiktok_id_entered.png')

print("4. Tapping Xác nhận thêm tài khoản at (500, 1815)...")
tap(500, 1815)
print("Waiting 6 seconds for GoLike backend check...")
time.sleep(6)

capture('link_confirm_result.png')
print("Done!")
