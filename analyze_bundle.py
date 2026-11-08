# -*- coding: utf-8 -*-
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

print("Length of JS:", len(js))

# 1. Base URL
print("\n--- BASE URLS ---")
urls = set(re.findall(r'https?://[a-zA-Z0-9\.\-_/]+', js))
for u in urls:
    if 'golike' in u or 'gateway' in u:
        print(u)

# 2. _gx_
print("\n--- _gx_ STORAGE KEYS ---")
gx_matches = set(re.findall(r'_gx_[a-zA-Z0-9]+', js))
for g in gx_matches:
    print(g)

# 3. Find where _gx_ is used
for g in gx_matches:
    idx = js.find(g)
    print(f"\nContext around {g}:")
    print(js[max(0, idx-100):min(len(js), idx+200)])

# 4. TikTok API routes
print("\n--- TIKTOK ROUTES ---")
tt_routes = set(re.findall(r'/[a-zA-Z0-9\-_/]*tiktok[a-zA-Z0-9\-_/]*', js))
for r in tt_routes:
    print(r)


# Check axios / fetch baseURL
print("\n--- API BASE URL SEARCH ---")
for kw in ['baseURL', 'gateway', 'Authorization', 'Bearer', 'token']:
    idx = 0
    while True:
        idx = js.find(kw, idx)
        if idx == -1:
            break
        print(f"[{kw}] at {idx}: {js[max(0, idx-50):min(len(js), idx+100)]}")
        idx += len(kw) + 200
        if idx > 500000: # just sample first few
            break
