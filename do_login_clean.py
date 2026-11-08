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

print("1. Focusing password...")
tap(500, 466)
input_b64('Golike@1026A')

print("2. Hiding keyboard via chevron down...")
tap(780, 966)
time.sleep(1)

print("3. Tapping Cloudflare...")
tap(158, 616)
print("Waiting 6 seconds for Cloudflare...")
time.sleep(6)

capture('login_ready.png')

print("4. Tapping Dang Nhap...")
tap(500, 780)
print("Waiting 6 seconds for login response...")
time.sleep(6)

capture('after_login.png')
print("Complete!")
