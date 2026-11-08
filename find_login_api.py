# -*- coding: utf-8 -*-
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Find strings starting with /api/
apis = set(re.findall(r'[\'\"\`](/api/[^\'\"\`]+)[\'\"\`]', js))
print("--- ALL /api/ ENDPOINTS ---")
for a in sorted(apis):
    print(a)

# Find advertising endpoints
advs = set(re.findall(r'[\'\"\`](/advertising/[^\'\"\`]+)[\'\"\`]', js))
print("\n--- ALL /advertising/ ENDPOINTS ---")
for a in sorted(advs):
    print(a)
