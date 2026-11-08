# -*- coding: utf-8 -*-
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Search for /api/ or login
for kw in ['/api/login', '/login', 'api-gateway', 'gateway']:
    idx = 0
    while True:
        idx = js.find(kw, idx)
        if idx == -1:
            break
        print(f"[{kw}] at {idx}: {js[max(0, idx-40):min(len(js), idx+80)]}")
        idx += len(kw) + 100
        if idx > 300000:
            break
