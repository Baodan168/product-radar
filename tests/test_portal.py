#!/usr/bin/env python3
"""门户壳的回归测试。

盯的是 audit-report 点名的那几处，以及重构时最容易悄悄退回去的写法
（内联 onclick、postMessage 用 '*'、把 load 事件当成功）。
"""
import json
import re
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import generate_portal  # noqa: E402
from oa import config, render  # noqa: E402


@pytest.fixture(scope='module')
def html():
    return generate_portal.build_html()


@pytest.fixture(scope='module')
def portal_js():
    return (BASE / 'assets' / 'portal.js').read_text(encoding='utf-8')


# ── 模板装配 ────────────────────────────────────────────

def test_renders_without_unsubstituted_placeholders(html):
    """模板占位符必须全部替换掉。

    用 Template.substitute 而不是 safe_substitute 就是为了拼错时直接抛，
    这里再兜一道，防止有人改回 safe_substitute。
    """
    leftovers = re.findall(r'\$\{[a-z_]+\}', html)
    assert not leftovers, f'模板有未替换的占位符：{set(leftovers)}'


def test_every_module_has_nav_link(html):
    for m in config.iter_modules():
        assert f'href="#/{m["key"]}"' in html, f'导航缺少 {m["key"]} 的链接'


def test_nav_items_are_real_links(html):
    """导航必须是带 href 的真链接，不是 href="#" + onclick。

    真链接才能中键新开、复制地址，读屏器也才认得。
    """
    nav = re.search(r'<nav[^>]*>(.*?)</nav>', html, re.S)
    assert nav, '找不到 <nav>'
    for anchor in re.findall(r'<a class="oa-nav-item"[^>]*>', nav.group(1)):
        assert 'href="#/' in anchor, f'导航项不是真链接：{anchor}'


def test_portal_config_is_valid_json(html):
    m = re.search(r'window\.OA_PORTAL = (.*?);</script>', html, re.S)
    assert m, '找不到 window.OA_PORTAL'
    cfg = json.loads(m.group(1))
    assert cfg['dashboardKey'] == config.DASHBOARD_KEY
    assert len(cfg['modules']) == len(list(config.iter_modules()))


def test_dashboard_is_default_landing(html):
    """今日概览必须是第一个板块，且标记为内嵌渲染。"""
    first = next(iter(config.iter_modules()))
    assert first['key'] == config.DASHBOARD_KEY
    assert first.get('inline') is True


# ── audit-report 点名的问题 ─────────────────────────────

def test_no_inline_event_handlers(html):
    """audit P0：内联事件属性一律不许出现在门户产物里。"""
    found = re.findall(r'\son(?:click|change|load|error|submit|input)\s*=', html)
    assert not found, f'门户 HTML 里还有内联事件属性：{found}'


def test_postmessage_never_uses_wildcard_origin(portal_js):
    """audit P2：发送端不许用 '*' 作为 targetOrigin。"""
    sends = re.findall(r'postMessage\([^;]*?\)', portal_js, re.S)
    assert sends, '没找到 postMessage 调用'
    for call in sends:
        assert "'*'" not in call and '"*"' not in call, f'postMessage 用了通配 origin：{call}'


def test_message_listener_validates_origin_source_and_range(portal_js):
    """audit P2：接收端必须校验 origin / source / 类型 / 数值范围。"""
    m = re.search(r"addEventListener\('message',(.*?)\n  \}\);", portal_js, re.S)
    assert m, '找不到 message 监听器'
    body = m.group(1)
    assert 'e.origin' in body, '没校验 event.origin'
    assert 'e.source' in body, '没校验 event.source'
    assert 'isFinite' in body, '没校验高度是有限数'
    assert 'MAX_FRAME_HEIGHT' in body, '没设高度上限'


def test_load_event_alone_is_not_treated_as_success(portal_js):
    """audit P2 的核心：不能把 iframe 触发 load 直接当成加载成功。

    服务器返回 404/500 页面时浏览器照样触发 load，v3 就因此把空白页
    显示成「已加载」。所以必须有独立探针拿 HTTP 状态码。
    """
    assert 'function probe(' in portal_js, '没有健康探针'
    assert "'http-error'" in portal_js, '没有区分 HTTP 错误态'
    assert "'timeout'" in portal_js, '没有加载超时态'
    assert "'network-error'" in portal_js, '没有网络失败态'


def test_cross_origin_health_is_reported_as_unknown(portal_js):
    """跨域板块读不到内部状态，必须如实标「未知」，不能给绿灯。"""
    assert re.search(r"cross_origin\s*\?\s*'unknown'\s*:\s*'ok'", portal_js), \
        '跨域板块的健康状态没有降级为 unknown'


# ── 转义 ────────────────────────────────────────────────

@pytest.mark.parametrize('payload', [
    '</script><script>alert(1)</script>',
    '"><img src=x onerror=alert(1)>',
    "'; alert(1); //",
    'javascript:alert(1)',
    '\\"; alert(1); //',
])
def test_js_escaping_survives_hostile_strings(payload):
    """注入 <script> 的 JSON 必须扛得住闭合标签和引号。"""
    out = render.js({'v': payload})
    assert '</script' not in out.lower(), f'JSON 里漏出了闭合标签：{out}'
    assert '<' not in out and '>' not in out, f'尖括号没转义：{out}'
    # \\u003c 本身就是合法 JSON 转义，所以产物应当仍能解析回原值
    assert json.loads(out)['v'] == payload, '转义后解不回原值'


def test_attr_escaping_closes_no_attribute():
    out = render.attr('" onmouseover="alert(1)')
    assert '"' not in out, f'属性值里漏出了裸引号：{out}'
