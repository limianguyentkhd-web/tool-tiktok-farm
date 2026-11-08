# -*- coding: utf-8 -*-
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Look for variable definitions xn=, Jh=, Bc=, lD=
for v in ['xn', 'Jh', 'Bc', 'lD', 'D1', 'Jf']:
    pattern = rf'\b{v}\s*=\s*[\'\"\`]([^\'\"\`]+)[\'\"\`]'
    m = re.search(pattern, js)
    if m:
        print(f"{v} = {m.group(1)}")
    else:
        # search for where it's defined
        idx = js.find(f"{v}=")
        if idx != -1:
            print(f"Def {v}:", js[max(0, idx-20):min(len(js), idx+60)])
