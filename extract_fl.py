# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('He=uo;')
idx_fl = js.rfind('function Fl()', 0, idx)
print("Function Fl to He:")
print(js[idx_fl:idx+400])
