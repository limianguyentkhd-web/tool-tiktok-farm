with open('golike_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Grab from 162700 to 164300
part = js[162700:164300]
script = part + """
console.log("Bc =", Bc);
console.log("Jh =", Jh);
console.log("lD =", lD);
console.log("xn =", xn);
console.log("He(143) =", He(143));
"""
with open('test_urls.js', 'w', encoding='utf-8') as out:
    out.write(script)
print("Wrote test_urls.js")
