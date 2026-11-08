with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = 161573
print(js[max(0, idx-400):min(len(js), idx+600)])
