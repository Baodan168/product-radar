"""今日概览 —— 门户首页。

PROJECT-VISION §5.1.2：「每个页面只回答一个问题——现在该选什么、
补什么、关注什么？」重构前的门户根页一个都没回答，打开就落到某个
板块。这四张卡就是那三个问题的答案：

    今日选品战情   今天该选什么
    补货告警       今天该补什么
    节日倒计时     接下来该关注什么
    数据新鲜度     以上三个还能不能信

脱敏（PROJECT-VISION §6）：毛利率、月销量、库存不出数字。
价格和利润区间是选品决策必需的，保留；紧急度只出计数和标签。

缺数据一律走 CardData 的 failed/missing 分支显示「数据不可用 + 原因」，
不用 0 兜底（audit P3 / DESIGN-DECISIONS D7）。
"""
import json
import re
from datetime import datetime

from . import render
from .config import BASE, OUTPUT_DIR
from .field import CardData
from .health import collect_freshness
from .restock import parse_analysis
from .urls import safe_url


# ── 数据装配 ────────────────────────────────────────────

def collect_radar_today(now=None) -> CardData:
    """今日选品战情：今天扫到多少、Top 3 是什么。"""
    now = now or datetime.now()
    try:
        from .platform_data import load_all_radar
        # only_with_new=False：今天可能一个新品都没有，但「扫了 200 个
        # 通过 0 个」和「今天根本没扫」是两回事，必须能区分
        radar = load_all_radar(only_with_new=False)
    except Exception as e:
        return CardData.fail(f'读取雷达数据失败: {e}')

    if not radar:
        return CardData.absent('还没有雷达扫描数据')

    today = now.strftime('%Y-%m-%d')
    date_key = today if today in radar else max(radar)
    data = radar[date_key] or {}
    products = data.get('products') or []

    new_products = [p for p in products if p.get('is_new') is True]
    # is_new 缺失时不能当成新品，也不能当成非新品——按「总数」口径展示
    picks = (new_products or products)[:5]

    return CardData(payload={
        'date': date_key,
        'is_today': date_key == today,
        'passed': len(products),
        'new_count': len(new_products),
        'scanned': (data.get('stats') or {}).get('total_scanned'),
        'picks': [_pick(p) for p in picks],
    })


def _pick(p: dict) -> dict:
    """一条 Top 推荐。只取做判断需要的字段，其余不带出来。"""
    margin = p.get('profit_margin')
    return {
        'name': p.get('name') or '(无标题)',
        'asin': p.get('asin') or '',
        'price': p.get('price'),
        'margin_pct': round(margin * 100) if isinstance(margin, (int, float)) else None,
        'signal': p.get('signal_label') or '',
        'image': safe_url(p.get('image_url')),
        'url': safe_url(p.get('amazon_url')),
    }


def collect_festivals(now=None, window_days=47) -> CardData:
    """节日倒计时。

    窗口取 47 天 —— PROJECT-VISION §2.1 写的「提前 30-47 天预警」，
    对应海运备货周期。
    """
    try:
        from season_engine import get_upcoming_events
        events = get_upcoming_events(days_ahead=window_days)
    except Exception as e:
        return CardData.fail(f'季节引擎不可用: {e}')

    if not events:
        return CardData.absent(f'未来 {window_days} 天没有节点')

    rows = []
    for ev in events[:6]:
        cats = ev.get('recommended_categories') or []
        rows.append({
            'name': ev.get('event_name') or '',
            'date': ev.get('date') or '',
            'days': ev.get('days_until'),
            'cats': '、'.join(cats[:4]),
            'deadline_air': ev.get('sourcing_deadline_air') or '',
        })
    return CardData(payload={'rows': rows, 'window': window_days})


def _festival_icon(name: str) -> str:
    """给节点配个图标。season_engine 不带 icon，按关键词兜一下。"""
    n = (name or '').lower()
    table = [
        ('school', '🎒'), ('christmas', '🎄'), ('halloween', '🎃'),
        ('valentine', '💝'), ('easter', '🐣'), ('mother', '💐'),
        ('father', '👔'), ('black friday', '🛒'), ('summer', '☀️'),
        ('autumn', '🍂'), ('winter', '❄️'), ('spring', '🌱'),
        ('bank holiday', '🏖️'), ('new year', '🎆'),
    ]
    for kw, icon in table:
        if kw in n:
            return icon
    return '📅'


def build_dashboard() -> dict:
    """装配四张卡。任何一张出问题都不影响其它三张。"""
    now = datetime.now()
    return {
        'now': now,
        'radar': collect_radar_today(now),
        'restock': parse_analysis(),
        'festivals': collect_festivals(now),
        'health': collect_freshness(now),
    }


# ── 渲染 ────────────────────────────────────────────────

def _nodata(card: CardData, fallback: str = '数据不可用') -> str:
    """缺数据/出错的统一占位。

    显示的是「为什么没有」，不是一个假的 0。
    """
    icon = '⚠️' if card.status == 'failed' else 'ℹ️'
    reason = card.error or fallback
    return (
        f'<div class="oa-dash-nodata">'
        f'<span class="nd-icon" aria-hidden="true">{icon}</span>'
        f'<span>{render.h(fallback)}'
        f'<span class="nd-reason"> · {render.h(reason)}</span></span>'
        f'</div>'
    )


def _card(icon: str, title: str, body: str, link=None, link_text='查看', span='') -> str:
    """span 走 CSS 类（oa-dash-wide / oa-dash-narrow），控制在 12 栏网格里占几栏。"""
    link_html = (
        f'<a class="oa-dash-card-link" href="{render.attr(link)}">{render.h(link_text)} →</a>'
        if link else ''
    )
    cls = 'oa-dash-card' + (f' {span}' if span else '')
    return (
        f'<section class="{cls}">'
        f'<div class="oa-dash-card-head">'
        f'<span class="oa-dash-card-icon" aria-hidden="true">{render.h(icon)}</span>'
        f'<h2 class="oa-dash-card-title">{render.h(title)}</h2>'
        f'{link_html}</div>'
        f'{body}</section>'
    )


def _metric(value, label, tone='') -> str:
    cls = f'oa-dash-metric-value{" " + tone if tone else ""}'
    shown = '—' if value is None else value
    return (
        f'<div class="oa-dash-metric">'
        f'<div class="{cls}">{render.h(shown)}</div>'
        f'<div class="oa-dash-metric-label">{render.h(label)}</div>'
        f'</div>'
    )


# ── 顶部指标条 ──────────────────────────────────────────
#
# 六个数字原本埋在两张卡的卡头里，字号和卡内正文差不多，扫一眼看不出
# 哪个是「今天的状态」。抽到页面顶部单独成条之后，概览页的阅读顺序变成
# 「先看六个数 → 再看下面四张卡的明细」，卡片本身也因为只剩列表而变紧。
#
# 数据源挂了不补 0（D7）：整组换成一块「不可用 + 原因」的占位，
# 而不是显示六个 0 让人以为今天真的什么都没有。

def _tile(value, label, tone='') -> str:
    cls = 'oa-dash-tile-value' + (f' {tone}' if tone else '')
    shown = '—' if value is None else value
    return (
        f'<div class="oa-dash-tile">'
        f'<div class="{cls}">{render.h(shown)}</div>'
        f'<div class="oa-dash-tile-label">{render.h(label)}</div>'
        f'</div>'
    )


def _tile_nodata(card: CardData, label: str) -> str:
    icon = '⚠️' if card.status == 'failed' else 'ℹ️'
    return (
        f'<div class="oa-dash-tile is-nodata">'
        f'<div class="oa-dash-tile-value">{icon}</div>'
        f'<div class="oa-dash-tile-label">{render.h(label)}</div>'
        f'</div>'
    )


def render_metric_strip(data: dict) -> str:
    radar, restock = data['radar'], data['restock']
    tiles = []

    if radar.is_ok:
        p = radar.payload
        tiles += [_tile(p['new_count'], '新品'),
                  _tile(p['passed'], '通过筛选'),
                  _tile(p['scanned'], '扫描总量')]
    else:
        tiles.append(_tile_nodata(radar, '选品数据不可用'))

    if restock.is_ok:
        c = restock.payload['counts']
        tiles += [_tile(c['urgent'], '紧急补货', 'is-alert' if c['urgent'] else ''),
                  _tile(c['watch'], '观察', 'is-warn' if c['watch'] else ''),
                  _tile(restock.payload['total'], '需补货 SKU')]
    else:
        tiles.append(_tile_nodata(restock, '补货数据不可用'))

    return f'<div class="oa-dash-strip">{"".join(tiles)}</div>'


def render_radar_card(card: CardData) -> str:
    if not card.is_ok:
        return _card('🎯', '今日选品战情', _nodata(card, '今日战情不可用'), '#/platform', '选品平台')

    p = card.payload
    # 三个数字已经上了顶部指标条，卡里不再重复
    stale = '' if p['is_today'] else f'<div class="oa-dash-note">最新数据为 {render.h(p["date"])}，今天还没扫</div>'

    picks = []
    for i, pick in enumerate(p['picks'], 1):
        img = (
            f'<img class="oa-pick-img" src="{render.attr(pick["image"])}" alt="" loading="lazy">'
            if pick['image'] else '<div class="oa-pick-img"></div>'
        )
        meta = []
        if pick['price'] is not None:
            meta.append(f'<span class="oa-pick-price">£{render.h(pick["price"])}</span>')
        if pick['margin_pct'] is not None:
            meta.append(f'<span>利润 {render.h(pick["margin_pct"])}%</span>')
        if pick['signal']:
            meta.append(f'<span>{render.h(pick["signal"])}</span>')

        # 链接过不了白名单就退化成非链接，不渲染一个指向不可信地址的 <a>
        tag_open = (f'<a class="oa-pick" href="{render.attr(pick["url"])}" '
                    f'target="_blank" rel="noopener noreferrer">') if pick['url'] else '<div class="oa-pick">'
        tag_close = '</a>' if pick['url'] else '</div>'

        picks.append(
            f'{tag_open}'
            f'<span class="oa-pick-rank">{i}</span>{img}'
            f'<span class="oa-pick-body">'
            f'<span class="oa-pick-name">{render.h(pick["name"])}</span>'
            f'<span class="oa-pick-meta">{"".join(meta)}</span>'
            f'</span>{tag_close}'
        )

    picks_html = (
        f'<div class="oa-dash-picks">{"".join(picks)}</div>' if picks
        else '<div class="oa-dash-nodata"><span class="nd-icon">ℹ️</span>'
             '<span>该日期没有通过筛选的产品</span></div>'
    )
    return _card('🎯', '今日选品战情', stale + picks_html,
                 '#/platform', '选品平台', span='oa-dash-wide')


def render_restock_card(card: CardData) -> str:
    if not card.is_ok:
        return _card('📦', '补货告警', _nodata(card, '补货数据不可用'),
                     '#/analysis', '补货跟进', span='oa-dash-narrow')

    p = card.payload
    # 三个计数已经上了顶部指标条，卡里只留最紧急的几条 SKU
    rows = ''.join(
        f'<div class="oa-alert-row" data-level="{render.attr(it["level"])}">'
        f'<span class="oa-alert-sku" title="{render.attr(it["name"])}">{render.h(it["sku"])}</span>'
        f'<span class="oa-alert-tag">{render.h(it["store"])} · 可售 {render.h(it["days_left"])}</span>'
        f'</div>'
        for it in p['top']
    )
    return _card('📦', '补货告警', f'<div class="oa-dash-alerts">{rows}</div>',
                 '#/analysis', '补货跟进', span='oa-dash-narrow')


def render_festival_card(card: CardData) -> str:
    if not card.is_ok:
        return _card('📅', '节日倒计时', _nodata(card, '节日数据不可用'), '#/platform', '节日选品')

    rows = []
    for r in card.payload['rows']:
        days = r['days']
        soon = ' is-soon' if isinstance(days, int) and days <= 14 else ''
        deadline = f'空运截止 {r["deadline_air"]}' if r['deadline_air'] else ''
        sub = ' · '.join(x for x in (r['cats'], deadline) if x)
        rows.append(
            f'<div class="oa-fest-row">'
            f'<span class="oa-fest-icon" aria-hidden="true">{render.h(_festival_icon(r["name"]))}</span>'
            f'<span class="oa-fest-body">'
            f'<span class="oa-fest-name">{render.h(r["name"])}</span>'
            f'<span class="oa-fest-cats" title="{render.attr(sub)}">{render.h(sub)}</span>'
            f'</span>'
            f'<span class="oa-fest-days{soon}">{render.h(days)}<small>天后</small></span>'
            f'</div>'
        )
    return _card('📅', '节日倒计时', f'<div class="oa-dash-festivals">{"".join(rows)}</div>',
                 '#/platform', '节日选品', span='oa-dash-wide')


def render_health_card(card: CardData) -> str:
    if not card.is_ok:
        return _card('🩺', '数据新鲜度', _nodata(card, '新鲜度不可用'), span='oa-dash-narrow')

    rows = ''.join(
        f'<div class="oa-health-row">'
        f'<span class="oa-health-dot" data-health="{render.attr(r["health"])}"></span>'
        f'<span class="oa-health-name">{render.h(r["label"])}</span>'
        f'<span class="oa-health-detail">{render.h(r["detail"])}</span>'
        f'</div>'
        for r in card.payload['rows']
    )
    note = ('<div class="oa-dash-note">'
            '新鲜度按数据文件更新时间算；板块能否打开由侧栏的探针实时判断。</div>')
    return _card('🩺', '数据新鲜度', f'<div class="oa-dash-health">{rows}</div>{note}',
                 span='oa-dash-narrow')


def build_dashboard_html() -> str:
    """渲染今日概览主体，供 templates/portal.html 内嵌。"""
    data = build_dashboard()
    now = data['now']

    cards = (
        render_radar_card(data['radar'])
        + render_restock_card(data['restock'])
        + render_festival_card(data['festivals'])
        + render_health_card(data['health'])
    )

    return (
        '<div class="oa-dash-head">'
        '<div class="oa-dash-eyebrow">TODAY</div>'
        f'<h1 class="oa-dash-title">今日概览</h1>'
        '<div class="oa-dash-sub">现在该选什么、补什么、关注什么 · '
        f'生成于 {render.h(now.strftime("%Y-%m-%d %H:%M"))}</div>'
        '</div>'
        f'{render_metric_strip(data)}'
        f'<div class="oa-dash-grid">{cards}</div>'
    )
