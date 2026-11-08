import subprocess
import time
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

DEVICE = 'ce031713dba2c72101'

def adb_cmd(args):
    cmd = ['adb', '-s', DEVICE] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.stdout.decode('utf-8', errors='ignore')

def adb_shell(cmd_str):
    cmd = ['adb', '-s', DEVICE, 'shell', cmd_str]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.stdout.decode('utf-8', errors='ignore')

def tap(x, y):
    adb_shell(f'input tap {x} {y}')

def screenshot(filename):
    path = os.path.join(r'C:\Users\Admin\.gemini\antigravity\brain\c3f30c76-b4b0-4748-ad0f-a0b19be6dddd', filename)
    cmd = ['adb', '-s', DEVICE, 'exec-out', 'screencap', '-p']
    res = subprocess.run(cmd, stdout=subprocess.PIPE)
    with open(path, 'wb') as f:
        f.write(res.stdout)
    return path

def get_ui_dump():
    adb_shell('uiautomator dump /data/local/tmp/dump.xml')
    return adb_shell('cat /data/local/tmp/dump.xml')

def solve_captcha_if_needed():
    time.sleep(1)
    dump = get_ui_dump()
    if 'Vui lòng xác minh nhanh' in dump or 'Thông báo' in dump and 'OK' in dump:
        print('  [Captcha] Found notification popup -> tapping OK...')
        tap(539, 1354)
        time.sleep(2)
        dump = get_ui_dump()

    if 'Xác minh nhanh' in dump or 'Kéo khối vuông' in dump:
        print('  [Captcha] Found visual drag captcha -> executing Bezier swipe...')
        adb_shell('sh /data/local/tmp/captcha.sh')
        time.sleep(3.5)
        return True
    return False

def do_single_job():
    print('>>> 1. Checking screen state...')
    dump = get_ui_dump()
    
    # If not on job screen, bring GoLike
    if 'com.golike' not in adb_shell('dumpsys window | grep -E "mCurrentFocus"'):
        print('Bringing GoLike to front...')
        adb_shell('monkey -p com.golike -c android.intent.category.LAUNCHER 1')
        time.sleep(2)
        dump = get_ui_dump()

    # If "Nhận Job ngay" is visible, tap it
    if 'Nhận Job ngay' in dump:
        print('>>> 2. Tapping "Nhận Job ngay" at (507, 1166)...')
        tap(507, 1166)
        time.sleep(2)

    # Solve captcha if it pops up
    solve_captcha_if_needed()

    # Wait for job screen
    time.sleep(2)
    dump = get_ui_dump()

    # Check if job is loaded
    if 'Cách làm việc' not in dump and 'TikTok' not in dump:
        print('  Waiting an extra 2s for job...')
        time.sleep(2)
        dump = get_ui_dump()

    if 'Hết Job' in dump or 'Chưa có công việc' in dump:
        print('  [Notice] Hết job tạm thời.')
        return False

    # Determine job type
    is_follow = 'THEO DÕI' in dump or 'FOLLOW' in dump or 'tiktok-follow' in dump
    job_type = 'FOLLOW' if is_follow else 'LIKE'
    print(f'>>> 3. Job loaded! Type: {job_type}')

    # Tap TikTok button
    print('>>> 4. Tapping "TikTok" button at (540, 891)...')
    tap(540, 891)
    time.sleep(4.5)  # allow TikTok profile/video to load fully

    # Perform action on TikTok
    print(f'>>> 5. Performing {job_type} on TikTok...')
    if job_type == 'FOLLOW':
        # Tap Follow button (center around 254, 572)
        tap(254, 572)
        print('  Tapped Follow button.')
    else:
        # Double tap video center
        tap(540, 1000)
        time.sleep(0.15)
        tap(540, 1000)
        print('  Double-tapped Like.')

    time.sleep(2.5)  # anti-spam delay

    # Return to GoLike
    print('>>> 6. Returning to GoLike...')
    adb_shell('monkey -p com.golike -c android.intent.category.LAUNCHER 1')
    time.sleep(2)

    # Tap Hoàn thành
    print('>>> 7. Tapping "Hoàn thành" at (540, 1171)...')
    tap(540, 1171)
    time.sleep(4)

    # Check outcome
    dump_after = get_ui_dump()
    screenshot('after_job_1.png')

    if 'thành công' in dump_after.lower() or 'nhận job ngay' in dump_after.lower():
        print('>>> [SUCCESS] Job completed and submitted successfully!')
        return True
    else:
        print('>>> [Result] Dump snippet after submit:')
        for line in dump_after.split('\n')[:15]:
            if any(k in line for k in ['text=', 'desc=']):
                print('   ', line.strip())
        return True

if __name__ == '__main__':
    do_single_job()
