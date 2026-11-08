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

print("1. Tapping Follow button at (500, 570)...")
tap(500, 570)
time.sleep(1.5)
capture('followed_gosen.png')

print("2. Returning to GoLike...")
subprocess.run(['adb', '-s', serial, 'shell', 'am', 'start', '-n', 'com.golike/.MainActivity'])
time.sleep(2)
capture('back_to_golike.png')
