"""门户导航与站点常量 —— 单一事实源。

⚠️ 加新板块只改这里的 MODULES，别改 generate_portal.py。
（原本 MODULES 在 generate_portal.py 里，见 DESIGN-DECISIONS D8：
门户壳拆成模板+资源后生成器只剩 CLI 入口，而首页的「板块健康」卡
也要读同一份板块清单，留在生成器里会形成循环依赖。）

每个板块的字段：
    key       路由标识，出现在 URL hash（#/platform）和 localStorage
    label     导航与顶栏显示名
    icon      导航图标（emoji）
    url       iframe src；同源用相对路径，跨仓库用绝对 URL
    desc      一句话说明
    probe     健康探针地址；省略则回退到 url
    cross_origin  跨域标记。跨域 iframe 拿不到内部状态，探针也只能
                  探到网络层，健康度显示「未知」而不是伪装成「正常」
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE / 'output'
TEMPLATE_DIR = BASE / 'templates'
ASSET_DIR = BASE / 'assets'

SYSTEM_NAME = 'Amazon项目运营OA'
SYSTEM_SUB = ''
PORTAL_VERSION = 'v4.0'

# GitHub Pages 站点根，postMessage 校验和探针都用它
SITE_ORIGIN = 'https://Baodan168.github.io'
SITE_BASE = f'{SITE_ORIGIN}/product-radar'

# 首页 key：不是 iframe 板块，由生成器直接渲染进主区（DESIGN-DECISIONS D6）
DASHBOARD_KEY = 'dashboard'

MODULES = [
    {
        'group': '核心业务',
        'items': [
            {
                'key': DASHBOARD_KEY,
                'label': '今日概览',
                'icon': '📊',
                'url': '',            # 内嵌渲染，无 iframe
                'desc': '现在该选什么、补什么、关注什么',
                'inline': True,
            },
            {
                'key': 'radar',
                'label': '跨境雷达',
                'icon': '📡',
                'url': 'https://Baodan168.github.io/kj-news-radar/',
                'desc': '24h跨境电商情报聚合',
                'cross_origin': True,
            },
            {
                'key': 'platform',
                'label': '选品平台',
                'icon': '🎯',
                'url': 'platform.html',
                'desc': '产品发现、扫描、看板管理',
            },
            {
                'key': 'analysis',
                'label': '补货跟进',
                'icon': '📦',
                'url': 'analysis/',
                'probe': 'analysis/index.html',
                'desc': '运营数据与补货分析',
            },
        ],
    },
    {
        'group': '扩展板块（待添加）',
        'items': [],
    },
]


def iter_modules():
    """按导航顺序展开所有板块。"""
    for group in MODULES:
        for item in group['items']:
            yield item


def get_module(key):
    for item in iter_modules():
        if item['key'] == key:
            return item
    return None


def iframe_modules():
    """走 iframe 的板块（排除内嵌渲染的今日概览）。"""
    return [m for m in iter_modules() if not m.get('inline')]
