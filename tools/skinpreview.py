#!/usr/bin/env python3
"""视觉方向对比工具 — 在不改 shared/oa-theme.css 的前提下预览换肤效果。

原理：起一个静态服务器（布局同 tools/snapshot.py），把 skins/<name>.css
在 </head> 前注入到页面里。因为排在主题表和补货页内联 <style> 之后，
同特异度下能覆盖二者 —— 正好模拟「令牌层改值 + 少量组件层覆盖」的真实换肤。

skins/ 是临时目录，不入库 —— 方向定稿后要把选中的那份合并进
shared/oa-theme.css 再删掉，绝不能留成第二个样式层（见 D3：
--oa-* 是唯一令牌命名空间）。v5 就是这么落地的。

用法:
    mkdir -p skins && vi skins/a.css                 # 只写 :root 覆盖
    python3 tools/skinpreview.py --skin a            # 单个方向全页
    python3 tools/skinpreview.py --skin a,b,c        # 多个方向并排
    python3 tools/skinpreview.py --skin a --only portal
"""
import argparse
import functools
import http.server
import socketserver
import threading
import time
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot import find_chrome, shoot  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
SKINS = BASE / 'skins'

PAGES = [
    ('portal',   'index.html',          1440, 1250),
    ('platform', 'platform.html',       1440, 1700),
    ('analysis', 'analysis/index.html', 1440, 1250),
]


def serve(root: Path, skin_css: str):
    """静态服务器 + 注入 skin。html 请求走内存改写，其余原样落盘。"""

    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            clean = path.split('?', 1)[0].split('#', 1)[0]
            if clean.startswith('/shared/'):
                return str(BASE / clean.lstrip('/'))
            return super().translate_path(path)

        def do_GET(self):
            local = Path(self.translate_path(self.path))
            if local.is_dir():
                local = local / 'index.html'
            if local.suffix == '.html' and local.exists() and skin_css:
                html = local.read_text(encoding='utf-8')
                tag = f'<style data-skin>\n{skin_css}\n</style>'
                html = (html.replace('</head>', tag + '\n</head>', 1)
                        if '</head>' in html else html + tag)
                body = html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            return super().do_GET()

        def log_message(self, *args):
            pass

    handler = functools.partial(Handler, directory=str(root))

    class Quiet(socketserver.TCPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            pass

    httpd = Quiet(('127.0.0.1', 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd.server_address[1], httpd.shutdown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skin', required=True, help='skins/ 下的方向名，逗号分隔')
    ap.add_argument('--out', default='.screenshots/skins')
    ap.add_argument('--only', help='只截某一页')
    args = ap.parse_args()

    chrome = find_chrome()
    root = BASE / 'output'
    if not root.is_dir():
        raise SystemExit(f'{root} 不存在，先跑一次生成器')

    for name in [s.strip() for s in args.skin.split(',') if s.strip()]:
        css_file = SKINS / f'{name}.css'
        if not css_file.exists():
            print(f'  ⏭️  跳过 {name}（{css_file} 不存在）')
            continue
        port, shutdown = serve(root, css_file.read_text(encoding='utf-8'))
        time.sleep(0.3)
        print(f'🎨 skin {name} | 端口 {port}')
        try:
            for page, rel, w, h in PAGES:
                if args.only and not page.startswith(args.only):
                    continue
                if not (root / rel).exists():
                    continue
                dest = BASE / args.out / f'{page}-{name}.png'
                if shoot(chrome, f'http://127.0.0.1:{port}/{rel}', dest, w, h, root):
                    print(f'  ✅ {dest.relative_to(BASE)} ({dest.stat().st_size // 1024}KB)')
        finally:
            shutdown()


if __name__ == '__main__':
    main()
