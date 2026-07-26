#!/usr/bin/env python3
"""
Product Selection Platform — Unified HTML Generator V5
Discovery = keyword/demand-centric with Amazon/1688 search links
Radar = product-centric with simple cards
Kanban = pipeline board with metrics + search
Both sections support date filtering.
"""

import json
import urllib.parse, sys, html as htmlmod, glob
from datetime import datetime
from pathlib import Path

from season_engine import get_upcoming_events
from success_tracker import calculate_metrics
from platform_search import build_search_index
from festival_engine import load_festivals, generate_festival_html
from oa import render

BASE = Path(__file__).parent

# 第二项是 CSS 类名，不是色值 —— 配色统一由 shared/oa-theme.css 的令牌决定，
# 生成器不再持有颜色（CLAUDE.md：改样式不走内联 CSS）。
STATUS_CONFIG = {
    "pending":   ("待评估",   "st-pending"),
    "supplier":  ("找供应商", "st-supplier"),
    "sample":    ("已采样",   "st-sample"),
    "listed":    ("已上架",   "st-listed"),
    "rejected":  ("不考虑",   "st-rejected"),
}

KANBAN_COLUMNS = [
    ("inbox",     "📥 收件箱",   "kc-inbox"),
    ("starred",   "⭐ 值得做",   "kc-starred"),
    ("verified",  "✅ 已验证",   "kc-verified"),
]


def _consolidate_past_months(data_dict):
    """Merge dates from past months (e.g. 2026-06-*) into monthly keys (e.g. 2026-06)."""
    current_month = datetime.now().strftime('%Y-%m')
    monthly = {}  # month_key -> merged data
    to_remove = []

    for date_key in list(data_dict.keys()):
        # Only process full date keys (YYYY-MM-DD)
        if not (len(date_key) == 10 and date_key[4] == '-' and date_key[7] == '-'):
            continue
        month_key = date_key[:7]
        if month_key >= current_month:
            continue  # current/future month, keep daily
        if month_key not in monthly:
            monthly[month_key] = {
                'products': [],
                'scan_date': month_key,
                'scan_time': '',
            }

        src = data_dict[date_key]
        # Merge products (dedup by ASIN)
        existing_asins = {p.get('asin') for p in monthly[month_key].get('products', []) if p.get('asin')}
        for p in src.get('products', []):
            if p.get('asin') and p['asin'] not in existing_asins:
                monthly[month_key].setdefault('products', []).append(p)
                existing_asins.add(p['asin'])
        # Merge insights (dedup by keyword)
        existing_kws = {i.get('keyword') for i in monthly[month_key].get('insights', []) if i.get('keyword')}
        for i in src.get('insights', []):
            if i.get('keyword') and i['keyword'] not in existing_kws:
                monthly[month_key].setdefault('insights', []).append(i)
                existing_kws.add(i['keyword'])
        # Carry over trend_forecast if any
        if src.get('trend_forecast') and not monthly[month_key].get('trend_forecast'):
            monthly[month_key]['trend_forecast'] = src['trend_forecast']

        to_remove.append(date_key)

    for d in to_remove:
        del data_dict[d]
    data_dict.update(monthly)
    return data_dict


def load_all_radar():
    """Load all radar scans, return dict keyed by date. Only include dates with new products. Merge same-day scans."""
    data_dir = BASE / 'data' / 'channels'
    result = {}
    for f in sorted(data_dir.glob('*.json')):
        if '-rejected' in f.name or '-trends' in f.name or '-raw' in f.name:
            continue
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            if 'products' in data and data.get('scan_date'):
                date = data['scan_date']
                if date in result:
                    # 同一天的多个文件，合并产品（去重）
                    existing_asins = {p.get('asin') for p in result[date]['products'] if p.get('asin')}
                    for p in data['products']:
                        if p.get('asin') and p['asin'] not in existing_asins:
                            result[date]['products'].append(p)
                            existing_asins.add(p['asin'])
                else:
                    result[date] = data
        except (json.JSONDecodeError, KeyError):
            continue

    # 合并过去月份（如6月）到月度 key
    result = _consolidate_past_months(result)

    # 过滤：只保留有新品的日期/月份
    filtered = {}
    for date, data in result.items():
        products = data.get('products', [])
        new_products = [p for p in products if p.get('is_new') == True]
        if new_products:
            filtered[date] = data

    return filtered


def load_all_discovery():
    """Load all discovery data, return dict keyed by date."""
    disc_dir = BASE / 'data' / 'discovery'
    if not disc_dir.exists():
        return {}
    result = {}
    for f in sorted(disc_dir.glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            if data.get('scan_date'):
                result[data['scan_date']] = data
        except (json.JSONDecodeError, KeyError):
            continue
    # 合并过去月份到月度 key
    result = _consolidate_past_months(result)
    return result


def generate_platform_html(radar_all=None, discovery_all=None, output_path=None):
    now = datetime.now()
    scan_date = now.strftime('%Y-%m-%d')
    scan_time = now.strftime('%H:%M')

    radar_all = radar_all or {}
    discovery_all = discovery_all or {}

    # Separate dates for radar and discovery
    radar_dates = sorted(radar_all.keys(), reverse=True)
    discovery_dates = sorted(discovery_all.keys(), reverse=True)
    # Keep all_dates for backward compatibility
    all_dates = sorted(set(radar_dates + discovery_dates), reverse=True)

    # Build radar JS data (minimal subset for client)
    radar_js = {}
    for date, data in radar_all.items():
        radar_js[date] = {
            'products': data.get('products', []),
            'stats': data.get('stats', {}),
            'scan_time': data.get('scan_time', ''),
        }

    # Build discovery JS data, converting products to insights format if needed
    discovery_js = {}
    for date, data in discovery_all.items():
        insights = data.get('insights', [])

        # If discovery file has products but no insights, convert them
        if not insights and 'products' in data:
            for p in data['products']:
                insights.append({
                    'keyword': p.get('name', '')[:40],
                    'keyword_cn': '',
                    'demand_signals': p.get('sources', []),
                    'trend_score': p.get('score', 0),
                    'trend_direction': 'stable',
                    'reason': p.get('reason', ''),
                    'action': '',
                    'amazon_keyword': p.get('name', '').split(',')[0].strip(),
                    'amazon_search_url': p.get('amazon_url', ''),
                    'search_1688': '',
                    'competition': '',
                })

        # Pre-encode 1688 search URLs in GBK
        for ins in insights:
            kw = ins.get('search_1688') or ins.get('keyword_cn') or ins.get('keyword') or ''
            if kw:
                gbk_kw = urllib.parse.quote(kw, encoding='gbk', safe='')
                ins['search_1688_url'] = f'https://s.1688.com/selloffer/offer_search.htm?keywords={gbk_kw}'
            else:
                ins['search_1688_url'] = ''

        discovery_js[date] = {
            'insights': insights,
            'trend_forecast': data.get('trend_forecast', ''),
            'scan_time': data.get('scan_time', ''),
        }

    # Serialize to JSON for embedding
    radar_json = json.dumps(radar_js, ensure_ascii=False)

    # Write RADAR_ALL to separate JS file (reduce HTML from 1.45MB to ~630KB)
    radar_js_path = BASE / 'output' / 'data' / 'radar-all.js'
    radar_js_path.parent.mkdir(parents=True, exist_ok=True)
    radar_js_path.write_text(f'window.RADAR_ALL = {radar_json};', encoding='utf-8')

    discovery_json = json.dumps(discovery_js, ensure_ascii=False)
    dates_json = json.dumps(all_dates, ensure_ascii=False)
    radar_dates_json = json.dumps(radar_dates, ensure_ascii=False)
    discovery_dates_json = json.dumps(discovery_dates, ensure_ascii=False)
    status_json = json.dumps(STATUS_CONFIG)

    # Load product status from status.json (GitHub-synced)
    prod_status = {}
    status_path = BASE / 'status.json'
    if status_path.exists():
        try:
            prod_status = json.loads(status_path.read_text())
        except Exception as e:
            print(f"⚠️ status.json load failed: {e}", file=sys.stderr)
    prod_status_json = json.dumps(prod_status, ensure_ascii=False)

    # Phase 2.3: 错误可观测化 — 收集加载失败信息供 debug 区展示
    _load_errors = []
    try:
        season_events = get_upcoming_events(90)
    except Exception as e:
        season_events = []
        _load_errors.append(f"season_events: {e}")
        print(f"⚠️ season_events load failed: {e}", file=sys.stderr)
    try:
        metrics = calculate_metrics()
    except Exception as e:
        metrics = {}
        _load_errors.append(f"metrics: {e}")
        print(f"⚠️ metrics load failed: {e}", file=sys.stderr)
    try:
        search_index = build_search_index()
    except Exception as e:
        search_index = {"generated": "", "total": 0, "entries": []}
        _load_errors.append(f"search_index: {e}")
        print(f"⚠️ search_index load failed: {e}", file=sys.stderr)

    season_json = json.dumps(season_events, ensure_ascii=False)
    metrics_json = json.dumps(metrics, ensure_ascii=False)
    search_json = json.dumps(search_index.get('entries', []), ensure_ascii=False)
    kanban_json = json.dumps(KANBAN_COLUMNS, ensure_ascii=False)
    
    # Load Festival Planner data
    try:
        festivals = load_festivals()
        festival_html = generate_festival_html(festivals)
        festival_count = len(festivals)
        # Serialize festivals for frontend kanban (minimal fields only)
        # Pre-encode 1688 URLs in GBK to avoid garbled text
        festivals_payload = [
            {"id": f.get("id",""), "name": f.get("name",""), "icon": f.get("icon",""),
             "date": f.get("date",""), "importance": f.get("importance",""),
             "products": [{"sku": p.get("sku",""), "keywords": p.get("keywords",[]),
                           "category": p.get("category",""), "margin": p.get("margin",""),
                           "sourcing": p.get("sourcing",""), "matchScore": p.get("matchScore",0),
                           "aliUrl": "https://s.1688.com/selloffer/offer_search.htm?keywords=" + urllib.parse.quote(
                               (p.get("sourcing","").split("1688:")[1].strip() if "1688:" in p.get("sourcing","") else p.get("sku","")),
                               encoding='gbk', safe='')}
                          for p in f.get("products",[])]}
            for f in festivals
        ]
        festivals_json = json.dumps(festivals_payload, ensure_ascii=False)
    except Exception as e:
        festivals = []
        festivals_payload = []
        festivals_json = '[]'
        festival_html = '<div class="empty">节日数据加载失败</div>'
        festival_count = 0
        _load_errors.append(f"festivals: {e}")
        print(f"⚠️ festivals load failed: {e}", file=sys.stderr)

    _load_errors_json = json.dumps(_load_errors, ensure_ascii=False)

    # Write DISC_ALL and FESTIVALS to separate JS files (reduce HTML size).
    # 走 write_data_js 而不是裸 write_text：数据源挂掉时会返回空列表，
    # 裸写会把好数据覆盖成 []，页面照常生成、只是 Tab 空了，很难发现。
    from oa.safe_write import write_data_js
    write_data_js(BASE / 'output' / 'data' / 'disc-all.js', 'DISC_ALL', discovery_js)
    ok, note = write_data_js(BASE / 'output' / 'data' / 'festivals.js', 'FESTIVALS', festivals_payload)
    if not ok:
        _load_errors.append(note)
        _load_errors_json = json.dumps(_load_errors, ensure_ascii=False)

    # Phase 2.4: 读取看板注入配置（从 config.json）
    _default_inject = {"enabled": True, "festival": {"max_per_event": 3, "days_ahead": 30, "sea_deadline_days": 77}, "discovery": {"max_keywords": 5}, "radar": {"max_products": 10, "new_only": True}}
    kanban_inject = _default_inject
    _cfg_path = BASE / 'config.json'
    if _cfg_path.exists():
        try:
            _cfg = json.loads(_cfg_path.read_text())
            kanban_inject = _cfg.get('kanban_injection', _default_inject)
        except Exception as e:
            print(f"⚠️ kanban_injection config load failed: {e}", file=sys.stderr)
    inject_json = json.dumps(kanban_inject, ensure_ascii=False)

    _kanban_sync_endpoint = ''
    if _cfg_path.exists():
        try:
            _kanban_sync_endpoint = (json.loads(_cfg_path.read_text())
                                     .get('kanban_sync', {}).get('endpoint', '')) or ''
        except Exception:
            pass
    # 端点必须是 https，否则同步请求会明文出网
    if _kanban_sync_endpoint and not _kanban_sync_endpoint.startswith('https://'):
        print(f"⚠️ kanban_sync.endpoint 不是 https，已忽略: {_kanban_sync_endpoint}", file=sys.stderr)
        _kanban_sync_endpoint = ''

    # 页面装配交给模板 + 外部 JS。
    # 原来这里是一段 840 行的 f-string，HTML/CSS/JS 全混在里面，每个花括号
    # 都要写成双份，四种输出语境共用一个 esc() —— audit P0/P3 的直接成因。
    platform_data = {
        'DATES': all_dates,
        'RADAR_DATES': radar_dates,
        'DISC_DATES': discovery_dates,
        'STATUS': STATUS_CONFIG,
        'PROD_STATUS': prod_status,
        'SEASON_EVENTS': season_events,
        'METRICS': metrics,
        'SEARCH_INDEX': search_index,
        'KANBAN_COLS': KANBAN_COLUMNS,
        'INJECT_CFG': kanban_inject,
        'LOAD_ERRORS': _load_errors,
        # 同步端点从 config.json 读。留空时前端只存本地并显示「同步未配置」，
        # 浏览器不再持有任何 GitHub 凭据（audit P0）
        'SYNC_ENDPOINT': _kanban_sync_endpoint,
    }

    html = render.render(
        'platform.html',
        scan_date=render.h(scan_date),
        festival_count=festival_count,
        festival_html=festival_html,
        platform_data=render.js(platform_data),
        asset_version=now.strftime('%Y%m%d%H%M'),
    )

    if not output_path:
        output_path = str(BASE / 'output' / 'platform.html')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding='utf-8')

    # assets/ 要随产物一起部署，否则线上页面没有 JS
    import shutil
    asset_dst = BASE / 'output' / 'assets'
    asset_dst.mkdir(parents=True, exist_ok=True)
    for f in (BASE / 'assets').glob('*.js'):
        shutil.copy2(f, asset_dst / f.name)

    return output_path


if __name__ == '__main__':
    radar_all = load_all_radar()
    discovery_all = load_all_discovery()
    out = generate_platform_html(radar_all, discovery_all)
    r_dates = len(radar_all)
    d_dates = len(discovery_all)
    print(f'✅ {out}', file=sys.stderr)
    print(f'   Radar: {r_dates} dates | Discovery: {d_dates} dates', file=sys.stderr)
    print(json.dumps({'output': out, 'radar_dates': r_dates, 'discovery_dates': d_dates}))
