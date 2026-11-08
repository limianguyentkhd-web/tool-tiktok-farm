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

print("1. Focusing password field at (500, 1039)...")
tap(500, 1039)
time.sleep(0.5)

print("2. Entering password Golike@1026A...")
input_b64('Golike@1026A')
time.sleep(1)

print("3. Dismissing keyboard...")
tap(500, 200)
time.sleep(1)

capture('login_filled.png')

print("4. Tapping Đăng nhập at (500, 1735)...")
tap(500, 1735)
print("Waiting 5 seconds...")
time.sleep(5)

capture('login_success_check.png')
print("Finished!")
