with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx_qr = js.find('function Qr(t,e){')
idx_end = js.find('const sv=Qr(323)', idx_qr)

script = js[idx_qr:idx_end] + """
const Qr = qr_fn || Qr;
"""
print("Found Qr at:", idx_qr)
print(js[idx_qr:idx_qr+300])
