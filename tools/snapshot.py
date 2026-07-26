#!/usr/bin/env python3
"""
页面截图工具 — 重构期间的视觉回归基线

用预装的 Chromium headless 直接截图，不依赖 playwright（本机未安装 Python 包）。
先起一个临时 http server，因为页面用相对路径引 shared/oa-theme.css，file:// 下加载不到。

用法:
    python3 tools/snapshot.py --out .screenshots/before
    python3 tools/snapshot.py --out .screenshots/after --theme dark
"""
import argparse
import http.server
import functools
import io
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


def serve(root: Path, force_theme=None):
    """在后台起一个静态服务器，返回 (port, shutdown_fn)。

    复刻 GitHub Pages 的部署布局：output/ 是站点根，shared/ 被拷到根下的 /shared/。
    直接把 output/ 当根会让 shared/oa-theme.css 404，截出来的图全是无样式的。
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        force_theme = None  # 由 serve() 设置

        def translate_path(self, path):
            clean = path.split('?', 1)[0].split('#', 1)[0]
            if clean.startswith('/shared/'):
                return str(BASE / clean.lstrip('/'))
            return super().translate_path(path)

        def send_head(self):
            """暗色截图：在 HTML 响应里注入 data-oa-theme。

            Chrome 的 --force-dark-mode 是自动反色，走的不是我们的令牌，
            截出来的图没有参考价值。这里直接打真实的主题属性，
            测的就是主题切换按钮实际走的那条路径。
            """
            if self.force_theme is None:
                return super().send_head()
            path = self.translate_path(self.path)
            if not path.endswith('.html'):
                return super().send_head()
            try:
                raw = open(path, 'rb').read()
            except OSError:
                self.send_error(404)
                return None
            marker = b'<html'
            i = raw.find(marker)
            if i != -1:
                j = raw.find(b'>', i)
                attr = f' data-oa-theme="{self.force_theme}"'.encode()
                raw = raw[:j] + attr + raw[j:]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            return io.BytesIO(raw)

        def log_message(self, *args):
            pass

    Handler.force_theme = force_theme
    handler = functools.partial(Handler, directory=str(root))

    class Quiet(socketserver.TCPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            pass  # 浏览器提前断连是常态，别刷屏

    httpd = Quiet(('127.0.0.1', 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return port, httpd.shutdown


def shoot(chrome: Path, url: str, dest: Path, width: int, height: int, theme: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(chrome),
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--hide-scrollbars',
        f'--window-size={width},{height}',
        f'--screenshot={dest}',
        '--virtual-time-budget=6000',
    ]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, timeout=90)
    if not dest.exists():
        tail = r.stderr.decode('utf-8', 'replace').strip().splitlines()[-3:]
        print(f'  ⚠️ {dest.name} 截图失败: {" / ".join(tail)}')
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='.screenshots/before', help='输出目录')
    ap.add_argument('--theme', default='light', choices=['light', 'dark'])
    ap.add_argument('--only', help='只截某一页（按名字前缀匹配）')
    args = ap.parse_args()

    chrome = find_chrome()
    out_dir = BASE / args.out
    root = BASE / 'output'
    if not root.is_dir():
        raise SystemExit(f'{root} 不存在，先跑一次生成器')

    port, shutdown = serve(root, force_theme=args.theme if args.theme == 'dark' else None)
    time.sleep(0.3)
    print(f'📸 Chromium: {chrome.name} | 服务端口 {port} | 主题 {args.theme}')

    ok = 0
    try:
        for name, rel, w, h in PAGES:
            if args.only and not name.startswith(args.only):
                continue
            if not (root / rel).exists():
                print(f'  ⏭️  跳过 {name}（{rel} 不存在）')
                continue
            suffix = '' if args.theme == 'light' else '-dark'
            dest = out_dir / f'{name}{suffix}.png'
            if shoot(chrome, f'http://127.0.0.1:{port}/{rel}', dest, w, h, args.theme):
                print(f'  ✅ {dest.relative_to(BASE)} ({dest.stat().st_size // 1024}KB)')
                ok += 1
    finally:
        shutdown()

    print(f'完成：{ok} 张 → {out_dir.relative_to(BASE)}')


if __name__ == '__main__':
    main()
