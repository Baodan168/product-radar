import re, pathlib
out = pathlib.Path('/home/lee/product-radar/output')
idx = (out/'index.html').read_text(encoding='utf-8', errors='ignore')
pjs = (out/'assets'/'portal.js').read_text(encoding='utf-8', errors='ignore')
disc = (out/'data'/'disc-all.js').read_text(encoding='utf-8', errors='ignore')

print('disc-all.js has 2026-10-05:', '2026-10-05' in disc)
print('disc-all.js has peeler keyword:', '多功能削皮器 三合一' in disc)
print('disc-all.js has forecast ① text:', '10月第1-2周' in disc)
print('portal.js loads disc-all.js:', 'disc-all' in pjs)
print('portal.js forecast hooks:', sorted(set(re.findall(r'forecast\w*', pjs)))[:8])
print('index.html forecast container:', re.findall(r'id="[^"]*forecast[^"]*"', idx)[:3])
print('index.html loads portal.js:', 'portal.js' in idx)
