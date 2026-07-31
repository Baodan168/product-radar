#!/usr/bin/env python3
"""补货页脱敏的回归测试。

两类断言，缺一不可：
  1. 敏感数据没了       —— 防泄露
  2. 该留的还在         —— 防误删

第 2 类是被真事逼出来的：KPI 正则一度跨卡片匹配，把 46 个详情页的
「售价」「库存状态」两张卡整个吞掉。只查第 1 类完全看不出来，
因为被删的卡里本来就没有敏感数字。
"""
import re
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from oa import desensitize as D  # noqa: E402

ANALYSIS = BASE / 'output' / 'analysis'


# ── 档位换算 ────────────────────────────────────────────

@pytest.mark.parametrize('pct,expect', [
    (46.9, '优秀'), (35.0, '优秀'),
    (28.9, '达标'), (20.0, '达标'),
    (17.7, '待优化'), (10.0, '待优化'),
    (9.7, '偏低'), (1.6, '偏低'), (0, '偏低'),
    (None, '—'),
])
def test_bucket_margin(pct, expect):
    assert D.bucket_margin(pct) == expect


def test_margin_target_follows_config():
    """达标线取 config.json 的 min_profit_margin，不另立标准。"""
    import json
    target = json.loads((BASE / 'config.json').read_text(encoding='utf-8'))['min_profit_margin'] * 100
    assert D.bucket_margin(target) == '达标'
    assert D.bucket_margin(target - 0.1) != '达标'


@pytest.mark.parametrize('v,expect', [
    (18.3, '高'), (5.0, '高'), (4.9, '中'), (1.0, '中'), (0.6, '低'), (None, '—'),
])
def test_bucket_daily(v, expect):
    assert D.bucket_daily(v) == expect


def test_weekly_and_daily_use_same_scale():
    """7 天销量按日均折算，两者口径一致。"""
    assert D.bucket_weekly(35) == D.bucket_daily(5)
    assert D.bucket_weekly(7) == D.bucket_daily(1)


def test_no_number_is_not_zero():
    """抠不到数字返回 —，不能当成 0（0 会被判成「偏低」）。"""
    assert D._num('') is None
    assert D._num('N/A') is None
    assert D.bucket_margin(D._num('—')) == '—'


# ── 防泄露 ──────────────────────────────────────────────

def test_index_table_columns_are_bucketed():
    html = '''<table><tr><th>SKU</th><th>售价</th><th>7天销量</th><th>日均</th><th>毛利率</th></tr>
    <tr class="urgent-row"><td>ABC</td><td>£7.99</td><td>41</td><td>5.9</td><td>21.2%</td></tr></table>'''
    out = D.scrub_index_table(html)
    assert '21.2%' not in out and '5.9' not in out and '>41<' not in out
    assert '达标' in out and '高' in out
    assert '£7.99' in out, '售价不该被动'


def test_index_table_uses_header_names_not_fixed_indices():
    """上游调换列序时必须跟着走，不能按下标改错列。"""
    html = '''<table><tr><th>毛利率</th><th>售价</th></tr>
    <tr><td>21.2%</td><td>£7.99</td></tr></table>'''
    out = D.scrub_index_table(html)
    assert '<td>达标</td>' in out
    assert '£7.99' in out, '列序变了就改错了列'


def test_kpi_card_value_is_bucketed():
    html = ('<div class="oa-kpi"><div class="oa-kpi-value">4.0%</div>'
            '<div class="oa-kpi-label">毛利率</div></div>')
    out = D.scrub_detail_kpis(html)
    assert '4.0%' not in out and '偏低' in out


def test_prose_numbers_are_replaced():
    html = '7天销量4件，日均0.6件。毛利率4.05%(1-10%)✓。可售21.0天。'
    out = D.scrub_detail_prose(html)
    assert not re.search(r'7天销量[\d.]', out)
    assert not re.search(r'日均[\d.]', out)
    assert not re.search(r'毛利率[\d.]', out)
    assert '可售21.0天' in out, '可售天数按选择保留'


def test_margin_band_is_also_removed():
    """(1-10%) 和 &gt;20% 本身就是区间，留着等于换个形式说数字。"""
    for band in ['毛利率4.05%(1-10%)✓。', '毛利率21.2%&gt;20%✓。', '毛利率21.2%。']:
        out = D.scrub_detail_prose(band)
        assert not re.search(r'\d', out), f'{band} → {out} 仍含数字'


def test_restock_formula_does_not_leak_daily_average():
    """留着「按日均0.6件×30天=30件」等于把日均反推出来。"""
    out = D.scrub_detail_prose('按日均0.6件×30天=30件。')
    assert '0.6' not in out
    assert '30' in out, '建议补货量按选择保留'
    assert '×' not in out, '乘法过程会泄露乘数'


# ── 防误删（第二类断言）────────────────────────────────

def test_scrub_refuses_when_content_is_destroyed(monkeypatch):
    """用会跨卡片匹配的坏正则，必须被拦住而不是写出去。"""
    bad = re.compile(
        r'(<div class="oa-kpi-value"[^>]*>)(.*?)(</div>\s*<div class="oa-kpi-label"[^>]*>)'
        r'(毛利率|7天销量|日均销量)(</div>)', re.S)
    html = ('<div class="oa-kpi"><div class="oa-kpi-value">£5.99</div>'
            '<div class="oa-kpi-label">售价</div></div>'
            '<div class="oa-kpi"><div class="oa-kpi-value">4.0%</div>'
            '<div class="oa-kpi-label">毛利率</div></div>')
    monkeypatch.setattr(D, '_KPI_RE', bad)
    with pytest.raises(D.DesensitizeError, match='误删'):
        D.scrub_html(html, 'test')


def test_kpi_regex_does_not_cross_cards():
    """修好的正则只动目标卡，前面的卡原封不动。"""
    html = ('<div class="oa-kpi"><div class="oa-kpi-value">£5.99</div>'
            '<div class="oa-kpi-label">售价</div></div>'
            '<div class="oa-kpi"><div class="oa-kpi-value"><span>30天内需补货</span></div>'
            '<div class="oa-kpi-label">库存状态</div></div>'
            '<div class="oa-kpi"><div class="oa-kpi-value">4.0%</div>'
            '<div class="oa-kpi-label">毛利率</div></div>')
    out = D.scrub_detail_kpis(html)
    assert '£5.99' in out and '售价' in out
    assert '30天内需补货' in out and '库存状态' in out
    assert '4.0%' not in out and '偏低' in out


def test_scrub_refuses_when_leaks_remain(monkeypatch):
    """脱敏规则失效时必须报错，不能写出「看着脱敏了其实没有」的页面。"""
    monkeypatch.setattr(D, 'scrub_detail_prose', lambda h: h)
    with pytest.raises(D.DesensitizeError, match='仍有敏感数据'):
        D.scrub_html('<p>毛利率4.05%(1-10%)✓。</p>', 'test')


def test_scrub_refuses_on_size_collapse(monkeypatch):
    monkeypatch.setattr(D, 'scrub_detail_prose', lambda h: h[:10])
    with pytest.raises(D.DesensitizeError):
        D.scrub_html('<p>' + 'x' * 500 + '毛利率</p>', 'test')


# ── 真实产物 ────────────────────────────────────────────

@pytest.mark.skipif(not ANALYSIS.is_dir(), reason='本地没有补货产物')
def test_shipped_analysis_files_have_no_sensitive_data():
    """这条是防复发的主力：产物里出现敏感数字就红。"""
    leaks = D.scan_dir(ANALYSIS)
    assert not leaks, (
        f'{len(leaks)} 个文件含敏感数据，先跑 '
        f'`python3 desensitize_analysis.py`：{list(leaks)[:5]}')


@pytest.mark.skipif(not ANALYSIS.is_dir(), reason='本地没有补货产物')
def test_shipped_analysis_files_keep_decision_fields():
    """脱敏不能把补货决策需要的字段一起带走。"""
    index = ANALYSIS / 'index.html'
    if index.exists():
        text = index.read_text(encoding='utf-8')
        for keep in ('售价', '可售天数', '建议补货', '运输方式'):
            assert keep in text, f'index.html 丢了 {keep}'

    details = [f for f in ANALYSIS.glob('*.html') if f.name != 'index.html']
    for f in details[:5]:
        text = f.read_text(encoding='utf-8')
        for keep in ('售价', '库存状态', 'FBA可售'):
            assert keep in text, f'{f.name} 丢了 {keep}'


@pytest.mark.skipif(not ANALYSIS.is_dir(), reason='本地没有补货产物')
def test_scrub_is_idempotent():
    """已脱敏的文件再跑一次不该有变化。"""
    changed, untouched = D.scrub_dir(ANALYSIS, dry_run=True)
    assert not changed, f'重复脱敏仍在改动：{changed[:3]}'
