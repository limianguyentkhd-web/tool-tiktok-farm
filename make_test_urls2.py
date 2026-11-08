with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx_uo = js.find('function uo(t,e){')
idx_end = js.find('const e1=!!window', idx_uo)

script = js[idx_uo:idx_end] + """
console.log("Bc =", Bc);
console.log("Jh =", Jh);
console.log("lD =", lD);
console.log("xn =", xn);
"""
with open('test_urls.js', 'w', encoding='utf-8') as out:
    out.write(script)
