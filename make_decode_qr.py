with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx_co = js.rfind('function co(', 0, 160486)
part = js[idx_co:161400]

script = part + """
const Qr = co;
for (let i = 300; i <= 340; i++) {
    try {
        console.log(`Qr(${i}) = ${Qr(i)}`);
    } catch(e) {}
}
console.log("sv =", sv);
console.log("sD =", sD);
console.log("Qr(329) =", Qr(329));
"""
with open('decode_qr.js', 'w', encoding='utf-8') as f:
    f.write(script)
print("Wrote decode_qr.js")
