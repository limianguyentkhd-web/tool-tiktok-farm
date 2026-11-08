import subprocess, time, sys
sys.stdout.reconfigure(encoding='utf-8')

serial = '9889da304447393259'

def swipe():
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'swipe', '500', '1400', '500', '400', '300'])
    time.sleep(1)

def tap(x, y):
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'tap', str(x), str(y)])
    time.sleep(1)

def capture(name):
    subprocess.run(['adb', '-s', serial, 'exec-out', 'screencap', '-p'], 
                   stdout=open(rf'C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd\{name}', 'wb'))

print("Swiping down...")
swipe()
swipe()
swipe()

capture('policy_scrolled.png')
print("Captured policy_scrolled.png")
