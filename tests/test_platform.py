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
from scanner import is_forbidden  # noqa: E402


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


# ── 节日选品：SKU 计数 / 过期节日收起 / 看板联动 ──────────

def _make_festival(id_, date, products=None):
    return {
        'id': id_, 'name': id_, 'nameEn': id_, 'icon': '📅',
        'date': date, 'month': int(date.split('-')[1]), 'importance': 'A',
        'category': 'festival', 'themeColor': '#000000',
        'products': products or [],
    }


def test_festival_header_sku_count_is_dynamic():
    """头部曾经写死 '300+ SKUs'，数据涨了文案不会跟着涨；改成实时统计。"""
    from datetime import datetime, timedelta
    from festival_engine import generate_festival_html

    future = (datetime.now() + timedelta(days=100)).strftime('%Y-%m-%d')
    festivals = [_make_festival('f1', future, products=[{'sku': 'a'}, {'sku': 'b'}, {'sku': 'c'}])]
    html = generate_festival_html(festivals)
    assert '300+ SKUs' not in html, '还在用写死的文案'
    assert '3 SKUs' in html


def test_past_festivals_hidden_by_default_but_reachable():
    """已过节日不该无限堆积在列表里；默认收起，但紧急度筛选里选"已过"还能看到。"""
    from datetime import datetime, timedelta
    from festival_engine import generate_festival_html, get_urgency

    past_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    fest = _make_festival('old1', past_date)
    assert get_urgency(fest) == 'past'

    html = generate_festival_html([fest])
    assert 'id="filterHidePast"' in html and 'checked' in html, '缺"隐藏已过节日"开关'
    assert "hidePast && cardUrgency === 'past' && urgency !== 'past'" in html, \
        '过滤逻辑没有把 hidePast 和显式选"已过"区分开'
    assert '<option value="past">⚫已过</option>' in html, '紧急度筛选里应该还能选"已过"查看'
    assert 'filterFestivals();\n    </script>' in html, '页面加载时没有立即收起已过节日'


def test_kanban_festival_items_link_back_to_festival_card(platform_js):
    """看板收件箱里的节日 SKU 要能跳回节日 Tab 对应的详情卡片。"""
    assert 'festivalId: f.id' in platform_js, '注入看板的节日项没带 festival id'
    assert "data-festival-id=\"${escAttr(item.festivalId)}\"" in platform_js, \
        'festival id 写进 data-* 属性没走 escAttr'
    assert 'function goToFestival(' in platform_js, '缺少跳转函数'
    i = platform_js.find('function goToFestival(')
    body = platform_js[i:i + 900]
    assert "getElementById('sec-festival')" in body, '没有切换到节日 Tab'
    assert 'scrollIntoView' in body and "classList.add('expanded')" in body, \
        '没有滚动定位并展开目标卡片'


# ── 节日选品：合规性（不能推荐店铺自己都上不了架的品类）───

def test_festival_data_file_has_no_unflagged_compliance_violations():
    """审计发现过 73/423 条节日 SKU 建议其实会被雷达扫描自己的
    is_forbidden() 拦下（儿童/电子/美妆/食品等），其中 44 条还标着
    "riskLevel: 低"。这里直接读仓库内的 data/festivals_data.js（不走
    festival_engine.load_festivals() 的多源回退——本机会优先读
    ~/uk-festival-planner/index.html，测试要认仓库里提交的这份，不能
    跟着本机环境漂移），跑一遍真实的 is_forbidden()，确保没有漏网的。

    riskNote 标了"⚠️待复核"前缀的（过滤词表过宽导致的疑似误伤，比如
    "figurine"/"seat"）豁免——这些是已知的、留给人工复核的，不是自动
    门禁能替人下判断的。
    """
    from festival_engine import _extract_js_array, _parse_js_array, BASE as FESTIVAL_BASE

    content = (FESTIVAL_BASE / 'data' / 'festivals_data.js').read_text(encoding='utf-8')
    js_array = _extract_js_array(content, 'const FESTIVALS = ')
    assert js_array, 'data/festivals_data.js 里没找到 FESTIVALS 数组'
    data = _parse_js_array(js_array)
    assert data, 'data/festivals_data.js 解析失败或为空'

    violations = []
    for f in data:
        for p in f.get('products', []):
            if str(p.get('riskNote', '')).startswith('⚠️待复核'):
                continue
            text = ' '.join([
                str(p.get('sku', '')), str(p.get('skuEn', '')),
                ' '.join(p.get('keywords', []) or []),
            ])
            result = is_forbidden(text, p.get('category', ''))
            forbidden = result[0] if isinstance(result, tuple) else result
            if forbidden:
                reason = result[1] if isinstance(result, tuple) else ''
                violations.append(f"[{f.get('name')}] {p.get('sku')} <- {reason}")

    assert not violations, '节日数据里有未标记的违禁 SKU 建议：\n' + '\n'.join(violations)
