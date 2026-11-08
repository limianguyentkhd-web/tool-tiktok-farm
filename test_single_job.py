import sys
import time
import subprocess
import re
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

GOLIKE_DEV = "9889da304447393259"
TIKTOK_DEV = "ce031713dba2c72101"
PORT = "5037"

def adb(dev, *args):
    cmd = ["adb", "-P", PORT, "-s", dev] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return res.stdout.strip()

def tap(dev, x, y):
    adb(dev, "shell", "input", "tap", str(x), str(y))

def dump_ui(dev):
    out = adb(dev, "exec-out", "uiautomator", "dump", "/dev/tty")
    if "<?xml" in out:
        out = out[out.find("<?xml"):]
        if "</hierarchy>" in out:
            out = out[:out.find("</hierarchy>") + 12]
        try:
            return ET.fromstring(out)
        except Exception as e:
            pass
    return None

def find_nodes(root, text_regex=None, desc_regex=None, class_regex=None):
    res = []
    if root is None:
        return res
    for node in root.iter('node'):
        txt = node.attrib.get('text', '')
        desc = node.attrib.get('content-desc', '')
        cls = node.attrib.get('class', '')
        bounds = node.attrib.get('bounds', '')
        
        if text_regex and not re.search(text_regex, txt, re.IGNORECASE):
            continue
        if desc_regex and not re.search(desc_regex, desc, re.IGNORECASE):
            continue
        if class_regex and not re.search(class_regex, cls, re.IGNORECASE):
            continue
            
        m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            res.append({
                'text': txt,
                'desc': desc,
                'class': cls,
                'bounds': (x1, y1, x2, y2),
                'center': ((x1+x2)//2, (y1+y2)//2)
            })
    return res

def run_one_job():
    print("=== [1] Bringing GoLike to foreground on", GOLIKE_DEV)
    adb(GOLIKE_DEV, "shell", "am", "start", "-n", "com.golike/.MainActivity")
    time.sleep(2)
    
    # Check if we need to tap 'Nhận Job ngay'
    root = dump_ui(GOLIKE_DEV)
    job_btn = find_nodes(root, text_regex=r'Nhận Job ngay')
    if job_btn:
        print("Tapping 'Nhận Job ngay' at", job_btn[0]['center'])
        tap(GOLIKE_DEV, job_btn[0]['center'][0], job_btn[0]['center'][1])
        time.sleep(2.5)
        
        # Check for confirmation modal 'Đã hiểu' / 'Đồng ý'
        root = dump_ui(GOLIKE_DEV)
        agree = find_nodes(root, text_regex=r'^Đồng ý$')
        if agree:
            print("Modal appeared, confirming...")
            tap(GOLIKE_DEV, 85, 1374)
            time.sleep(0.3)
            tap(GOLIKE_DEV, agree[0]['center'][0], agree[0]['center'][1])
            time.sleep(2.5)
    
    # Now we should be on the job detail screen
    root = dump_ui(GOLIKE_DEV)
    job_info = find_nodes(root, text_regex=r'TĂNG LƯỢT|TĂNG LIKE|TĂNG BÌNH LUẬN|Job Id')
    print("Job Screen Elements:")
    for n in job_info:
        print("  -", n['text'])
        
    tiktok_btn = find_nodes(root, desc_regex=r'^TikTok$')
    if not tiktok_btn:
        tiktok_btn = find_nodes(root, text_regex=r'^TikTok$')
        
    if not tiktok_btn:
        print("ERROR: Could not find TikTok button on GoLike screen!")
        return False
        
    print("Tapping TikTok button at", tiktok_btn[0]['center'])
    tap(GOLIKE_DEV, tiktok_btn[0]['center'][0], tiktok_btn[0]['center'][1])
    time.sleep(3)
    
    # Check what opened on GOLIKE_DEV TikTok
    tt_root = dump_ui(GOLIKE_DEV)
    user_nodes = find_nodes(tt_root, text_regex=r'^@[a-zA-Z0-9_\.]+')
    target_user = None
    if user_nodes:
        target_user = user_nodes[0]['text'].replace('@', '').strip()
        print(f"Target TikTok User: @{target_user}")
    else:
        print("Could not find @username node directly, inspecting all text...")
        for n in find_nodes(tt_root):
            if n['text']:
                print("   txt:", n['text'])
                
    if not target_user:
        print("Attempting to get intent from logcat...")
        # fallback
        return False
        
    # Now on TIKTOK_DEV (ce031713dba2c72101), open this user's profile
    print(f"=== [2] Dispatching to TikTok worker {TIKTOK_DEV}: @{target_user}")
    target_url = f"https://www.tiktok.com/@{target_user}"
    adb(TIKTOK_DEV, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", target_url, "-p", "com.zhiliaoapp.musically")
    time.sleep(4)
    
    # Find and tap Follow on TIKTOK_DEV
    w_root = dump_ui(TIKTOK_DEV)
    follow_btn = find_nodes(w_root, text_regex=r'^Follow$')
    if follow_btn:
        print("Tapping 'Follow' on worker at", follow_btn[0]['center'])
        tap(TIKTOK_DEV, follow_btn[0]['center'][0], follow_btn[0]['center'][1])
        time.sleep(2.5)
    else:
        following_btn = find_nodes(w_root, text_regex=r'^Following')
        if following_btn:
            print("Already following @", target_user)
        else:
            print("WARNING: Could not find Follow button, dumping buttons:")
            for b in find_nodes(w_root, class_regex=r'Button|TextView'):
                if b['text']:
                    print("   btn:", b['text'])
                    
    # Switch back to GoLike on GOLIKE_DEV
    print("=== [3] Switching back to GoLike on", GOLIKE_DEV)
    adb(GOLIKE_DEV, "shell", "am", "start", "-n", "com.golike/.MainActivity")
    time.sleep(1.5)
    
    # Tap 'Hoàn thành'
    gl_root = dump_ui(GOLIKE_DEV)
    complete_btn = find_nodes(gl_root, text_regex=r'Hoàn thành')
    if complete_btn:
        print("Tapping 'Hoàn thành' at", complete_btn[0]['center'])
        tap(GOLIKE_DEV, complete_btn[0]['center'][0], complete_btn[0]['center'][1])
        time.sleep(3)
    else:
        print("ERROR: Could not find 'Hoàn thành' button!")
        return False
        
    # Check confirmation result
    final_root = dump_ui(GOLIKE_DEV)
    res_nodes = find_nodes(final_root)
    print("Screen status after completion:")
    for n in res_nodes:
        if any(w in n['text'].lower() for w in ['thành công', 'lỗi', 'điểm', 'nhận được', 'hoàn thành', 'chúc mừng']):
            print("  ==>", n['text'])
            
    return True

if __name__ == '__main__':
    run_one_job()
