# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Search for AES or Decrypt or Encrypt
for kw in ['AES.decrypt', 'CryptoJS', 'AES', 'localStorage.getItem']:
    idx = 0
    while True:
        idx = js.find(kw, idx)
        if idx == -1:
            break
        print(f"[{kw}] at {idx}: {js[max(0, idx-40):min(len(js), idx+100)]}")
        idx += len(kw) + 100
        if idx > 200000:
            break
