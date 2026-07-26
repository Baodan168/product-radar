#!/usr/bin/env python3
"""OA 门户页生成器 — CLI 入口。

真正的逻辑在 oa/ 包里：
    oa/config.py     板块配置（⚠️ 加新板块改这里，不是本文件）
    oa/render.py     模板装配与分语境转义
    oa/dashboard.py  今日概览数据
    templates/portal.html + assets/portal.js

本文件只负责「读配置 → 渲染 → 写文件」，保持 main() 签名不变，
因为 cron_scan.sh 和 restock_pipeline.sh 都在调它。
"""
import shutil
from datetime import datetime
from pathlib import Path

from oa import config, render
from oa.dashboard import build_dashboard_html

BASE = Path(__file__).resolve().parent
OUTPUT_DIR = config.OUTPUT_DIR


def build_nav():
    """侧栏导航。

    导航项用真正的 <a href="#/key">，不是 <a href="#" onclick=...>：
    可以中键新开、可以复制链接、键盘和读屏器也认得。
    """
    parts = []
    for group in config.MODULES:
        if not group['items']:
            parts.append(
                f'<div class="oa-nav-group-label dim">{render.h(group["group"])}</div>'
                f'<div class="oa-nav-empty">暂无板块</div>'
            )
            continue
        parts.append(f'<div class="oa-nav-group-label">{render.h(group["group"])}</div>')
        for m in group['items']:
            health = '' if m.get('inline') else (
                f'<span class="oa-nav-health" data-health="unknown" '
                f'title="板块健康状态"></span>'
            )
            parts.append(
                f'<a class="oa-nav-item" data-key="{render.attr(m["key"])}" '
                f'href="#/{render.attr(m["key"])}" title="{render.attr(m["desc"])}">'
                f'<span class="oa-nav-icon" aria-hidden="true">{render.h(m["icon"])}</span>'
                f'<span class="oa-nav-label">{render.h(m["label"])}</span>'
                f'{health}</a>'
            )
    return ''.join(parts)


def portal_config(built_at):
    """注入给 assets/portal.js 的运行期配置。"""
    return {
        'systemName': config.SYSTEM_NAME,
        'siteOrigin': config.SITE_ORIGIN,
        'dashboardKey': config.DASHBOARD_KEY,
        'builtAt': built_at,
        'modules': [
            {
                'key': m['key'],
                'label': m['label'],
                'url': m['url'],
                'probe': m.get('probe', m['url']),
                'inline': bool(m.get('inline')),
                'cross_origin': bool(m.get('cross_origin')),
            }
            for m in config.iter_modules()
        ],
    }


def sync_assets():
    """把 assets/ 拷进 output/。

    GitHub Actions 的部署步骤只拷 output/ 和 shared/，
    assets/ 留在仓库根的话线上会 404。
    """
    src = config.ASSET_DIR
    dst = OUTPUT_DIR / 'assets'
    dst.mkdir(parents=True, exist_ok=True)
    copied = []
    for f in sorted(src.glob('*.js')) + sorted(src.glob('*.css')):
        shutil.copy2(f, dst / f.name)
        copied.append(f.name)
    return copied


def build_html():
    now = datetime.now()
    built_at = now.strftime('%Y-%m-%d %H:%M')
    first = next(iter(config.iter_modules()))

    return render.render(
        'portal.html',
        system_name=render.h(config.SYSTEM_NAME),
        system_sub=render.h(config.SYSTEM_SUB),
        portal_version=render.h(config.PORTAL_VERSION),
        build_date=now.strftime('%Y-%m-%d'),
        first_label=render.h(first['label']),
        nav_items=build_nav(),
        dashboard_html=build_dashboard_html(),
        portal_config=render.js(portal_config(built_at)),
        # 资源版本号用构建时间，改完样式/脚本不用手动 bump 也能穿透 CDN
        asset_version=now.strftime('%Y%m%d%H%M'),
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = build_html()
    out_path = OUTPUT_DIR / 'index.html'
    out_path.write_text(html, encoding='utf-8')
    assets = sync_assets()
    print(f'  ✅ OA门户页已生成: {out_path} ({out_path.stat().st_size / 1024:.1f}KB)')
    print(f'  ✅ 资源已同步: {", ".join(assets)}')
    return out_path


if __name__ == '__main__':
    main()
