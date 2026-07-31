#!/usr/bin/env python3
"""今日概览的回归测试。

重点盯两件事：
1. 缺数据时显示「不可用 + 原因」，不是 0（audit P3 / D7）
2. 脱敏字段不出现在产物里（PROJECT-VISION §6）
"""
import re
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from oa import dashboard, health, restock  # noqa: E402
from oa.field import CardData  # noqa: E402


# ── 缺数据的表达 ────────────────────────────────────────

@pytest.mark.parametrize('renderer', [
    dashboard.render_radar_card,
    dashboard.render_restock_card,
    dashboard.render_festival_card,
    dashboard.render_health_card,
])
def test_failed_card_shows_reason_not_zero(renderer):
    """卡失败时必须说明原因，且不能渲染出指标数字。

    「紧急 0 个」和「补货数据读不到」对补货决策是相反的结论，
    用 0 兜底会让人以为库存健康。
    """
    html = renderer(CardData.fail('数据源炸了'))
    assert 'oa-dash-nodata' in html, '没有走「数据不可用」分支'
    assert '数据源炸了' in html, '没有显示失败原因'
    assert 'oa-dash-metric-value' not in html, '失败的卡不该渲染指标数字'


def test_missing_and_failed_look_different():
    """「还没有数据」和「读取失败」是两回事，图标要能区分。"""
    missing = dashboard.render_radar_card(CardData.absent('还没跑过'))
    failed = dashboard.render_radar_card(CardData.fail('读取失败'))
    assert 'ℹ️' in missing and '⚠️' in failed


def test_restock_missing_file_is_not_ok(tmp_path):
    """补货页不存在时必须报缺失，不能返回一堆 0。"""
    card = restock.parse_analysis(tmp_path / 'nope.html')
    assert not card.is_ok
    assert card.error


def test_restock_bad_html_is_not_ok(tmp_path):
    """上游模板变了（解析不出带紧急度的行）也必须报错。"""
    p = tmp_path / 'index.html'
    p.write_text('<table><tr><td>完全不一样的结构</td></tr></table>', encoding='utf-8')
    card = restock.parse_analysis(p)
    assert not card.is_ok, '解析不出内容却报告成功'


def test_restock_parses_real_page():
    card = restock.parse_analysis()
    if not card.is_ok:
        pytest.skip(f'本地没有补货产物: {card.error}')
    assert card.payload['total'] == sum(card.payload['counts'].values())
    assert card.payload['top'], '有计数却没有明细'


# ── 脱敏（PROJECT-VISION §6）────────────────────────────

def test_restock_card_omits_sensitive_columns():
    """补货卡不带毛利率/销量 —— 这些字段不上公开页。"""
    card = restock.parse_analysis()
    if not card.is_ok:
        pytest.skip('本地没有补货产物')
    for item in card.payload['top']:
        assert set(item) <= {'level', 'level_label', 'store', 'sku', 'name', 'days_left'}, \
            f'补货明细带了多余字段：{set(item)}'


def test_dashboard_html_has_no_margin_or_volume_labels():
    """整页产物里不该出现毛利率/月销量/库存这类标签。"""
    html = dashboard.build_dashboard_html()
    for banned in ('毛利率', '月销量', '库存', '7天销量'):
        assert banned not in html, f'今日概览泄露了脱敏字段：{banned}'


# ── 新鲜度 ──────────────────────────────────────────────

def test_freshness_does_not_use_file_mtime():
    """新鲜度必须从内容取日期，不能用 mtime。

    git clone/checkout 会把所有文件 mtime 刷成当前时间，
    用 mtime 的话 CI 和新机器上永远显示「刚刚」，这张卡就白做了。
    """
    src = (BASE / 'oa' / 'health.py').read_text(encoding='utf-8')
    body = re.sub(r'#.*', '', re.sub(r'""".*?"""', '', src, flags=re.S))
    assert 'st_mtime' not in body, 'health.py 又用回文件 mtime 了'


def test_freshness_reports_real_ages():
    card = health.collect_freshness()
    assert card.is_ok
    rows = card.payload['rows']
    assert rows, '没有任何新鲜度行'
    for r in rows:
        assert r['health'] in ('ok', 'warn', 'error', 'unknown')
        assert r['detail'], f'{r["label"]} 没有说明文字'


def test_cross_origin_module_reports_unknown_freshness():
    """跨境雷达在独立仓库，本地拿不到它的更新时间，必须标未知。"""
    card = health.collect_freshness()
    radar = [r for r in card.payload['rows'] if r['module'] == 'radar']
    assert radar and radar[0]['health'] == 'unknown'


# ── 渲染安全 ────────────────────────────────────────────

def test_pick_without_safe_url_is_not_a_link():
    """URL 过不了白名单时退化成非链接，不渲染指向不可信地址的 <a>。"""
    card = CardData(payload={
        'date': '2026-07-25', 'is_today': True, 'passed': 1,
        'new_count': 1, 'scanned': 10,
        'picks': [{
            'name': 'x', 'asin': 'A1', 'price': 9.99, 'margin_pct': 30,
            'signal': '', 'image': '', 'url': '',   # 已被 safe_url 滤空
        }],
    })
    html = dashboard.render_radar_card(card)
    assert '<a class="oa-pick"' not in html
    assert '<div class="oa-pick">' in html


def test_dashboard_html_has_no_inline_event_handlers():
    html = dashboard.build_dashboard_html()
    assert not re.findall(r'\son(?:click|error|load)\s*=', html)


def test_external_links_carry_noopener():
    """target=_blank 一律带 rel=noopener noreferrer（audit P4）。"""
    html = dashboard.build_dashboard_html()
    for tag in re.findall(r'<a[^>]*target="_blank"[^>]*>', html):
        assert 'noopener' in tag and 'noreferrer' in tag, f'外链缺 rel：{tag}'
