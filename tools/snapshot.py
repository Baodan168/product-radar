#!/usr/bin/env python3
"""
页面截图工具 — 重构期间的视觉回归基线

用预装的 Chromium headless 直接截图，不依赖 playwright（本机未安装 Python 包）。
先起一个临时 http server，因为页面用相对路径引 shared/oa-theme.css，file:// 下加载不到。

用法:
    python3 tools/snapshot.py --out .screenshots/before
    python3 tools/snapshot.py --out .screenshots/after --only portal
"""
import argparse
import http.server
import functools
import shutil
import socketserver
import subprocess
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CHROME_CANDIDATES = [
    Path('/opt/pw-browsers/chromium-1194/chrome-linux/chrome'),
    Path('/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'),
]

# (输出名, 相对 output/ 的路径, 视口宽, 视口高)
PAGES = [
    ('portal',          'index.html',          1440, 1200),
    ('portal-mobile',   'index.html',           375, 1400),
    ('platform',        'platform.html',       1440, 2400),
    ('platform-mobile', 'platform.html',        375, 2400),
    ('analysis',        'analysis/index.html', 1440, 2000),
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if p.exists():
            return p
    found = shutil.which('chromium') or shutil.which('google-chrome')
    if found:
        return Path(found)
    raise SystemExit('找不到 Chromium 可执行文件，检查 /opt/pw-browsers/')


def serve(root: Path):
    """在后台起一个静态服务器，返回 (port, shutdown_fn)。

    复刻 GitHub Pages 的部署布局：output/ 是站点根，shared/ 被拷到根下的 /shared/。
    直接把 output/ 当根会让 shared/oa-theme.css 404，截出来的图全是无样式的。
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            clean = path.split('?', 1)[0].split('#', 1)[0]
            if clean.startswith('/shared/'):
                return str(BASE / clean.lstrip('/'))
            return super().translate_path(path)

        def log_message(self, *args):
            pass

    handler = functools.partial(Handler, directory=str(root))

    class Quiet(socketserver.TCPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            pass  # 浏览器提前断连是常态，别刷屏

    httpd = Quiet(('127.0.0.1', 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return port, httpd.shutdown


# Chrome --headless=new 的窗口宽度有 ~500px 下限，直接传 --window-size=375
# 会渲染成 500 宽再裁到 375，看起来像页面横向溢出，实际是工具在骗人。
# 窄于这个值就套一层精确宽度的 iframe，拿到真实的窄屏布局。
MIN_WINDOW_WIDTH = 500


def shoot(chrome: Path, url: str, dest: Path, width: int, height: int,
          root: Path = None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    wrapper = None
    target = url
    win_w, win_h = width, height

    if width < MIN_WINDOW_WIDTH and root is not None:
        wrapper = root / f'_snap_{dest.stem}.html'
        wrapper.write_text(
            '<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;padding:0;overflow:hidden}'
            f'iframe{{width:{width}px;height:{height}px;border:0;display:block}}</style>'
            f'<iframe src="{url}"></iframe>',
            encoding='utf-8')
        target = url.rsplit('/', 1)[0] + '/' + wrapper.name
        win_w, win_h = MIN_WINDOW_WIDTH, height

    cmd = [
        str(chrome),
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--hide-scrollbars',
        f'--window-size={win_w},{win_h}',
        f'--screenshot={dest}',
        '--virtual-time-budget=6000',
    ]
    cmd.append(target)
    r = subprocess.run(cmd, capture_output=True, timeout=90)
    if wrapper is not None:
        wrapper.unlink(missing_ok=True)
    if not dest.exists():
        tail = r.stderr.decode('utf-8', 'replace').strip().splitlines()[-3:]
        print(f'  ⚠️ {dest.name} 截图失败: {" / ".join(tail)}')
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='.screenshots/before', help='输出目录')
    ap.add_argument('--only', help='只截某一页（按名字前缀匹配）')
    args = ap.parse_args()

    chrome = find_chrome()
    out_dir = BASE / args.out
    root = BASE / 'output'
    if not root.is_dir():
        raise SystemExit(f'{root} 不存在，先跑一次生成器')

    port, shutdown = serve(root)
    time.sleep(0.3)
    print(f'📸 Chromium: {chrome.name} | 服务端口 {port}')

    ok = 0
    try:
        for name, rel, w, h in PAGES:
            if args.only and not name.startswith(args.only):
                continue
            if not (root / rel).exists():
                print(f'  ⏭️  跳过 {name}（{rel} 不存在）')
                continue
            dest = out_dir / f'{name}.png'
            if shoot(chrome, f'http://127.0.0.1:{port}/{rel}', dest, w, h, root):
                print(f'  ✅ {dest.relative_to(BASE)} ({dest.stat().st_size // 1024}KB)')
                ok += 1
    finally:
        shutdown()

    print(f'完成：{ok} 张 → {out_dir.relative_to(BASE)}')


if __name__ == '__main__':
    main()
