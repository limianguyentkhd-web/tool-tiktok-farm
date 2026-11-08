import re

with open(r'd:\TOOL TIKTOK\extracted_webview\index.js', 'r', encoding='utf-8', errors='ignore') as f:
    js = f.read()

# Search for where tiktok jobs are handled
for m in re.finditer(r'advertising/publishers/tiktok', js):
    start = max(0, m.start() - 300)
    end = min(len(js), m.end() + 1500)
    print("=== TIKTOK JOB HANDLER ===")
    print(js[start:end])
    print("="*40)
