#!/usr/bin/env python3
"""UK 抓取封禁观察器：快速探测 captcha 是否解除，输出一行结论。"""
import sys, time
sys.path.insert(0, '/home/lee/product-radar')

def check():
    from curl_cffi import requests as c
    url = 'https://www.amazon.co.uk/gp/bestsellers/kitchen/'
    hdrs = {'Accept-Language': 'en-GB,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    try:
        r = c.get(url, impersonate='chrome', headers=hdrs, timeout=25)
        html = r.text
        is_captcha = 'validateCaptcha' in html or 'api-services-support@amazon' in html
        ok = len(html) > 50000 and not is_captcha
        return ok, len(html), r.status_code, is_captcha
    except Exception as e:
        return False, 0, 'ERR', str(e)[:40]

if __name__ == '__main__':
    ok, size, code, extra = check()
    ts = time.strftime('%Y-%m-%d %H:%M')
    if ok:
        print(f'[{ts}] ✅ 封禁已解除 — {size}B HTTP{code}')
        sys.exit(0)   # 解除
    print(f'[{ts}] 🚨 仍被封 — {size}B HTTP{code} captcha={extra}')
    sys.exit(1)
