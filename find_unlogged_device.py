import subprocess
import time
import xml.etree.ElementTree as ET

# Devices with TikTok installed:
devices = [
    '9889da304447393259',
    '988a17344c564b5657',
    'ce01182188dbdcee0c',
    'ce011821c38b263b05',
    'ce031713ed1e10540d',
    'ce0328219b0be8f50d',
    'ce04171425efd0f10d',
    'ce0417146b840c3104',
    'ce041714a5547e3202',
    'ce0517150b75dcb80c',
    'ce051715eaf458370d',
    'ce0718274d93800c01'
]

print(f"Scanning {len(devices)} devices...")

for serial in devices:
    # Wake screen
    subprocess.run(['adb', '-s', serial, 'shell', 'input', 'keyevent', '224'], capture_output=True)
    
    # Launch TikTok
    subprocess.run(['adb', '-s', serial, 'shell', 'monkey', '-p', 'com.zhiliaoapp.musically', '-c', 'android.intent.category.LAUNCHER', '1'], capture_output=True)

time.sleep(4)

for serial in devices:
    # Tap Profile icon (approx bottom right: 980 2050 or similar)
    # First dump UI
    subprocess.run(['adb', '-s', serial, 'shell', 'uiautomator', 'dump', '/sdcard/check_ui.xml'], capture_output=True)
    res = subprocess.run(['adb', '-s', serial, 'shell', 'cat', '/sdcard/check_ui.xml'], capture_output=True, text=True, errors='ignore')
    xml_content = res.stdout
    
    is_logged_in = False
    has_login_button = False
    
    if 'Sign up' in xml_content or 'Log in' in xml_content or 'Đăng ký' in xml_content or 'Đăng nhập' in xml_content:
        has_login_button = True
    
    print(f"Device {serial}: has_login_button={has_login_button}, xml_len={len(xml_content)}")
