# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('const Bc=He(142)')
print("Context around He(142):")
print(js[max(0, idx-400):min(len(js), idx+300)])
