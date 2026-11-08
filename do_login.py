import subprocess, time, sys
sys.stdout.reconfigure(encoding='utf-8')

serial = '9889da304447393259'

def tap(x, y):
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', str(x), str(y)])
    time.sleep(1)

def input_text(text):
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'text', text])
    time.sleep(1)

def capture(name):
    subprocess.run(['adb', '-s', serial, 'exec-out', 'screencap', '-p'], 
                   stdout=open(rf'C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\{name}', 'wb'))

print("1. Focusing username...")
tap(500, 368)
input_text('glk_ntbi12803')

print("2. Focusing password...")
tap(500, 466)
input_text('Golike@1026A')

print("3. Hiding keyboard...")
tap(500, 200)
time.sleep(1)

print("4. Tapping Cloudflare...")
tap(158, 616)
print("Waiting 6 seconds for Cloudflare...")
time.sleep(6)

capture('login_cf_ready.png')

print("5. Tapping Dang Nhap...")
tap(500, 780)
print("Waiting 5 seconds for login response...")
time.sleep(5)

capture('login_result.png')
print("Done!")
