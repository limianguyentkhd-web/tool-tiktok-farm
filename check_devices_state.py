import subprocess
import sys

devices = [
    '9889da304447393259', '988a17344c564b5657', 'ce01182188dbdcee0c',
    'ce011821c38b263b05', 'ce031713ed1e10540d', 'ce0328219b0be8f50d',
    'ce04171425efd0f10d', 'ce0417146b840c3104', 'ce041714a5547e3202',
    'ce0517150b75dcb80c', 'ce051715eaf458370d', 'ce0718274d93800c01'
]

print("Checking accounts and tiktok state on devices:")
for d in devices:
    # Check if logged in by looking for user id in shared_prefs or checking profile
    # Or check if musically has accounts
    res = subprocess.run(['adb', '-s', d, 'shell', 'dumpsys window windows'], capture_output=True, text=True, errors='ignore')
    focus = "Unknown"
    for line in res.stdout.splitlines():
        if 'mCurrentFocus' in line or 'mFocusedApp' in line:
            focus = line.strip()
            break
    print(f"{d} -> Focus: {focus}")
