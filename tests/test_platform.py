#!/usr/bin/env python3
"""选品平台的回归测试。

重点是 audit-report P0 那条：外部数据进 HTML 属性 / 内联事件 / URL，
而 esc() 只够 HTML 文本用。拆分之后这些边界最容易被改回去。
"""
import json
import re
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from oa import urls  # noqa: E402
from oa.safe_write import write_data_js  # noqa: E402


@pytest.fixture(scope='module')
def platform_js():
    return (BASE / 'assets' / 'platform.js').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def platform_tpl():
    return (BASE / 'templates' / 'platform.html').read_text(encoding='utf-8')


# ── 内联事件（audit P0）────────────────────────────────

def test_no_inline_handlers_in_platform_js(platform_js):
    """产品 ASIN、看板 id 原本直接拼进 onclick 的 JS 字符串里，
    数据里一个单引号就能跳出字符串。全部改成 data-* + 事件委托。"""
    found = re.findall(r'\son(?:click|change|error|load)\s*=', platform_js)
    assert not found, f'platform.js 里还有内联事件：{found}'


def test_no_inline_handlers_in_platform_template(platform_tpl):
    found = re.findall(r'\son(?:click|change|error|load)\s*=', platform_tpl)
    assert not found, f'模板里还有内联事件：{found}'


def test_delegation_covers_every_data_act(platform_js):
    """每个 data-act 都要有对应的 case，否则按钮变哑巴。"""
    emitted = set(re.findall(r'data-act="([a-z-]+)"', platform_js))
    handled = set(re.findall(r"case '([a-z-]+)':", platform_js))
    missing = emitted - handled
    assert not missing, f'这些 data-act 没有对应处理分支：{missing}'


def test_template_data_acts_are_handled(platform_tpl, platform_js):
    emitted = set(re.findall(r'data-act="([a-z-]+)"', platform_tpl))
    handled = set(re.findall(r"case '([a-z-]+)':", platform_js))
    missing = emitted - handled
    assert not missing, f'模板里这些 data-act 没人处理：{missing}'


# ── 分语境转义 ──────────────────────────────────────────

def test_escattr_exists_and_escapes_quotes(platform_js):
    """esc() 走 textContent→innerHTML，不转义引号，放进属性会被撑破。
    必须有独立的 escAttr()。"""
    assert 'function escAttr(' in platform_js, '缺少属性专用转义函数'
    i = platform_js.find('function escAttr(')
    body = platform_js[i:i + 400]
    assert '&quot;' in body, 'escAttr 没有转义双引号'
    assert '&#39;' in body, 'escAttr 没有转义单引号'
    assert '&amp;' in body, 'escAttr 没有转义 &'


def test_data_attributes_use_escattr_not_esc(platform_js):
    """写进 data-* 的外部值必须走 escAttr，不能用 esc。"""
    for m in re.finditer(r'data-(?:asin|status|kanban-id|nav-type|nav-date)="\$\{([^}]+)\}"',
                         platform_js):
        expr = m.group(1)
        assert expr.startswith('escAttr('), f'属性值没走 escAttr：{expr}'


def test_all_href_and_src_go_through_safeurl(platform_js):
    """href/src 的插值必须过白名单，挡 javascript:/data:/任意第三方域。"""
    for m in re.finditer(r'(?:href|src)="\$\{([^}]+)\}"', platform_js):
        expr = m.group(1)
        assert expr.startswith('safeUrl('), f'URL 没过白名单：{expr}'


def test_external_links_have_noopener(platform_js):
    for tag in re.findall(r'<a[^>]*target="_blank"[^>]*>', platform_js):
        assert 'noopener' in tag and 'noreferrer' in tag, f'外链缺 rel：{tag[:120]}'


# ── URL 白名单（Python 侧，与 JS 侧同一套规则）──────────

@pytest.mark.parametrize('bad', [
    'javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'http://www.amazon.co.uk/dp/X',          # 非 https
    'https://evilamazon.co.uk/dp/X',         # 后缀匹配能骗过，点号边界不能
    'https://amazon.co.uk.evil.com/x',
    'https://user:pass@amazon.co.uk/x',      # 内嵌凭据
    'https://amazon.co.uk:8080/x',           # 非默认端口
    'https://evil.com/x',
    '',
    None,
])
def test_url_allowlist_rejects(bad):
    assert not urls.is_safe(bad), f'不该放行：{bad!r}'


@pytest.mark.parametrize('good', [
    'https://www.amazon.co.uk/dp/B0DKBV52GF',
    'https://amazon.co.uk/s?k=test',
    'https://m.media-amazon.com/images/I/x.jpg',
    'https://images-eu.ssl-images-amazon.com/images/I/x.jpg',
    'https://s.1688.com/selloffer/offer_search.htm?keywords=x',
])
def test_url_allowlist_accepts(good):
    assert urls.is_safe(good), f'不该拦：{good}'


def test_subdomain_boundary_not_suffix_match():
    """audit P1 的核心：endsWith 会把 evilamazon.co.uk 当成 amazon.co.uk。"""
    assert urls.host_allowed('www.amazon.co.uk')
    assert not urls.host_allowed('evilamazon.co.uk')
    assert not urls.host_allowed('notamazon.co.uk')


# ── 数据塌缩防护 ────────────────────────────────────────

def test_empty_payload_never_overwrites_good_data(tmp_path):
    """真实事故：节日数据源读不到时返回 []，把 133KB 好数据覆盖成空，
    页面照常生成、只是 Tab 空了，很难发现。"""
    f = tmp_path / 'd.js'
    assert write_data_js(f, 'X', [{'i': i} for i in range(60)])[0]
    assert not write_data_js(f, 'X', [])[0], '空数据不该被写入'
    kept = json.loads(f.read_text().split('=', 1)[1].strip().rstrip(';'))
    assert len(kept) == 60, '好数据被覆盖了'


def test_collapsed_payload_is_rejected(tmp_path):
    f = tmp_path / 'd.js'
    write_data_js(f, 'X', [{'i': i} for i in range(60)])
    assert not write_data_js(f, 'X', [{'i': 1}])[0], '数据砍到 1/60 还允许写入'


def test_normal_churn_is_allowed(tmp_path):
    """正常增删不该被拦。"""
    f = tmp_path / 'd.js'
    write_data_js(f, 'X', [{'i': i} for i in range(60)])
    assert write_data_js(f, 'X', [{'i': i} for i in range(55)])[0]
    assert write_data_js(f, 'X', [{'i': i} for i in range(80)])[0]


# ── 节日数据源回退 ──────────────────────────────────────

def test_festival_sources_include_repo_local_fallback():
    """原本只认一台机器上的绝对路径，那台机器目录一改名就静默返回 []。"""
    import festival_engine
    paths = [str(p) for p in festival_engine.FESTIVAL_SOURCES]
    assert any('data/festivals_data.js' in p for p in paths), '缺仓库内回退源'
    assert len(paths) >= 2


def test_festival_slug_blocks_injection():
    from festival_engine import _safe_slug
    assert _safe_slug("'); alert(1); //") == 'alert1'
    assert _safe_slug('<img src=x>') == 'imgsrcx'
    assert _safe_slug('') == 'other'
    assert _safe_slug('gift') == 'gift'


def test_generator_is_no_longer_a_monolith():
    """generate_platform.py 原本 1146 行，HTML/CSS/JS 全混在一个 f-string 里。"""
    n = len((BASE / 'generate_platform.py').read_text(encoding='utf-8').split('\n'))
    assert n < 400, f'generate_platform.py 又长回 {n} 行了'
