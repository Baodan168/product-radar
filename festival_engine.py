#!/usr/bin/env python3
"""
Festival Planner — 从 uk-festival-planner 提取数据，集成到选品平台
"""

import html as htmlmod
import json
import re
import subprocess
import tempfile
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

from scanner import is_forbidden


def _safe_slug(value, fallback='other'):
    """把外部字段收紧成只含 [A-Za-z0-9_-] 的 slug。

    用在会进入 HTML 属性 / JS 字符串的位置。这类值本来就该是标识符，
    与其去猜哪一层转义够用，不如直接限定字符集。
    """
    slug = re.sub(r'[^A-Za-z0-9_-]', '', str(value or ''))
    return slug[:40] or fallback

BASE = Path(__file__).parent

# 物流模式配置（对齐 uk-festival-planner 原项目）
# leadTime = production + transit；选品截止日 = 节日 - (leadTime + 14)
# 14天 = 到仓后入仓2天 + 缓冲12天
LOGISTICS_MODES = {
    "air":   {"label": "空运",     "icon": "✈️", "production": 3, "transit": 13, "leadTime": 16},
    "truck": {"label": "卡航/快铁", "icon": "🚆", "production": 3, "transit": 30, "leadTime": 33},
    "sea":   {"label": "海运",     "icon": "🚢", "production": 3, "transit": 60, "leadTime": 63},
}

# 海运作为雷达联动的触发基准（周期最长，提前最多）
SEA_LEAD_TIME = LOGISTICS_MODES["sea"]["leadTime"]  # 63天
ARRIVAL_BUFFER = 14  # 到仓后入仓+缓冲

# 品类映射
CATEGORY_MAP = {
    "decor": {"label": "装饰", "icon": "🎀", "color": "#8b5cf6"},
    "gift": {"label": "礼品", "icon": "🎁", "color": "#ec4899"},
    "apparel": {"label": "服饰", "icon": "👕", "color": "#3b82f6"},
    "home": {"label": "家居", "icon": "🏠", "color": "#10b981"},
}

# 2026-08-28 北半球季节映射
SEASONS = {
    "spring": {"label": "春季", "en": "Spring", "icon": "🌸", "months": (3, 4, 5), "color": "var(--oa-green)"},
    "summer": {"label": "夏季", "en": "Summer", "icon": "☀️", "months": (6, 7, 8), "color": "var(--oa-orange)"},
    "autumn": {"label": "秋季", "en": "Autumn", "icon": "🍂", "months": (9, 10, 11), "color": "#b45309"},
    "winter": {"label": "冬季", "en": "Winter", "icon": "❄️", "months": (12, 1, 2), "color": "var(--oa-blue)"},
}

def _season_of(month: int) -> str:
    for key, info in SEASONS.items():
        if month in info["months"]:
            return key
    return ""

def _current_season_key() -> str:
    return _season_of(datetime.now().month)


# 数据源，按优先级从高到低。
# 原本只有第一个 —— 一台机器上的绝对路径。那台机器上的目录一改名，
# load_festivals() 就静默返回 []，generate_platform.py 照样生成一个
# 节日 Tab 全空的页面，把上一份好数据覆盖掉。加两级仓库内的回退。
FESTIVAL_SOURCES = [
    Path('/home/lee/uk-festival-planner/index.html'),   # 原始项目（若在本机）
    BASE / 'data' / 'festivals_data.js',                # 仓库内副本
    BASE / 'output' / 'data' / 'festivals.js',          # 上次生成的产物（纯 JSON）
]


def _extract_js_array(content, marker):
    """从 JS 源码里按括号配对切出 marker 之后的数组字面量。"""
    start = content.find(marker)
    if start == -1:
        return None
    i = start + len(marker)
    depth = 0
    while i < len(content):
        if content[i] == '[':
            depth += 1
        elif content[i] == ']':
            depth -= 1
            if depth == 0:
                return content[start + len(marker):i + 1]
        i += 1
    return None


def _parse_js_array(js_array):
    """用 node 把 JS 对象字面量转成 JSON（键没引号，json 模块吃不下）。"""
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False,
                                         encoding='utf-8') as f:
            f.write(f'const FESTIVALS = {js_array};\n')
            f.write('console.log(JSON.stringify(FESTIVALS));\n')
            temp_file = f.name
        result = subprocess.run(['node', temp_file], capture_output=True,
                                text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        print(f"  ⚠️ node 解析节日数据失败: {result.stderr.strip()[:200]}")
    except Exception as e:
        print(f"  ⚠️ 节日数据解析异常: {e}")
    finally:
        if temp_file:
            Path(temp_file).unlink(missing_ok=True)
    return None


def load_festivals():
    """加载 Festival 数据，按 FESTIVAL_SOURCES 顺序回退。

    返回空列表代表「一个源都没读到」，调用方必须把它当异常处理，
    不能当成「今年没有节日」——那会覆盖掉好数据。
    """
    for src in FESTIVAL_SOURCES:
        if not src.exists():
            continue
        try:
            content = src.read_text(encoding='utf-8')
        except OSError:
            continue

        # output/data/festivals.js 是上次生成的产物，已经是合法 JSON
        if src.suffix == '.js' and content.lstrip().startswith('window.FESTIVALS'):
            try:
                data = json.loads(content.split('=', 1)[1].strip().rstrip(';'))
                if data:
                    return data
            except (json.JSONDecodeError, IndexError):
                pass
            continue

        js_array = _extract_js_array(content, 'const FESTIVALS = ')
        if not js_array:
            continue
        data = _parse_js_array(js_array)
        if data:
            print(f"  ℹ️ 节日数据来自 {src}")
            return data

    print("  ⚠️ 所有节日数据源都读不到，节日 Tab 将为空")
    return []


def get_deadlines(festival):
    """计算三种物流方式的选品截止日"""
    f_date = datetime.strptime(festival['date'], '%Y-%m-%d')
    result = {}
    for key, mode in LOGISTICS_MODES.items():
        deadline = f_date - timedelta(days=mode['leadTime'] + ARRIVAL_BUFFER)
        result[key] = {
            "date": deadline.strftime('%Y-%m-%d'),
            "label": mode['label'],
            "icon": mode['icon'],
            "days_from_today": (deadline - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).days,
        }
    return result


def get_urgency(festival, logistics="sea"):
    """计算节日紧急度（默认用海运，周期最长）"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    f_date = datetime.strptime(festival['date'], '%Y-%m-%d')
    
    if f_date < today:
        return "past"
    
    mode = LOGISTICS_MODES[logistics]
    deadline = f_date - timedelta(days=mode['leadTime'] + ARRIVAL_BUFFER)
    days = (deadline - today).days
    
    if days < 0:
        return "urgent"
    elif days <= 7:
        return "week"
    elif days <= 30:
        return "month"
    return "plan"


def get_urgency_label(urgency):
    """紧急度标签"""
    return {
        "urgent": "🔴紧急",
        "week": "🟠本周启动",
        "month": "🟡本月备货",
        "plan": "🟢规划中",
        "past": "⚫已过"
    }.get(urgency, urgency)


def get_urgency_icon(urgency):
    """紧急度图标"""
    return {
        "urgent": "⚠️",
        "week": "⏰",
        "month": "📅",
        "plan": "✅",
        "past": "⚫"
    }.get(urgency, "")


def generate_season_panel(festivals):
    """Generate season panel with buttons and recommendation cards."""
    from season_engine import MONTHLY_SEASONAL_KEYWORDS, get_seasonal_sourcing_alert, SEASON_REGION_TAGS

    event_month = {}
    for f in festivals:
        try:
            event_month[f.get('id', '')] = int(f['date'][5:7])
        except (ValueError, TypeError, IndexError):
            continue
    season_data = {}
    for key, info in SEASONS.items():
        kws, seen = [], set()
        for m in info["months"]:
            for kw in MONTHLY_SEASONAL_KEYWORDS.get(m, []):
                k = kw.lower().strip()
                if k not in seen:
                    seen.add(k)
                    kws.append(kw)
        cnt = sum(1 for mid, m in event_month.items() if m in info["months"])
        season_data[key] = {"kws": kws, "events": cnt}

    cur = _current_season_key()
    alert = get_seasonal_sourcing_alert()
    urgency_icon = {"OK": "\u2705", "PLAN": "\U0001f4cb", "AIR_ONLY": "\U0001f7e1", "URGENT": "\u26a0\ufe0f", "OVERDUE": "\U0001f534"}.get(alert["urgency"], "")
    next_season_label = SEASONS.get(alert["next_season"], {}).get("label", alert["next_season"])
    next_season_icon = SEASONS.get(alert["next_season"], {}).get("icon", "")
    deadline_text = ""
    if alert["days_to_deadline"] < 0:
        deadline_text = f'{next_season_icon} {next_season_label}\u7a7a\u8fd0\u622a\u6b62\u5df2\u8fc7\uff08{alert["air_deadline"]}\uff09\uff0c\u4ec5\u9650\u73b0\u8d27/\u5feb\u94c1'
    else:
        deadline_text = f'{next_season_icon} {next_season_label}\u7a7a\u8fd0\u622a\u6b62: {alert["air_deadline"]}\uff08\u8fd8\u5269 {alert["days_to_deadline"]} \u5929\uff09{urgency_icon}'

    btns = []
    for key, info in SEASONS.items():
        active = ' season-btn-active' if key == cur else ''
        btns.append(
            f'<button class="season-btn{active}" data-season="{key}" '
            f'onclick="setSeason(this, \'{key}\')">'
            f'{info["icon"]} {info["label"]}({info["months"][0]}-{info["months"][-1]}月)</button>'
        )
    season_nav = f'<div class="season-nav">{" ".join(btns)}</div>'

    panels = []
    panel_js = []
    for key, info in SEASONS.items():
        d = season_data[key]
        kws_html = "".join(f'<span class="season-kw">{htmlmod.escape(k)}</span>' for k in d["kws"])
        cur_mark = ' <span class="season-cur-tag">\u5f53\u524d</span>' if key == cur else ''
        region = SEASON_REGION_TAGS.get(key, {})
        region_n = region.get("north", "")
        display_style = "block" if key == cur else "none"
        deadline_div = ""
        if key == cur:
            deadline_div = f'<div class="season-deadline-bar">{deadline_text}</div>'
        region_div = f'<div class="season-region-tags"><span class="region-tag">\U0001f1ec\U0001f1e7 UK\u5168\u5883: {region_n}</span></div>'
        panel_html_str = (
            f'      <div class="season-panel" id="seasonPanel-{key}" data-season="{key}" style="display:{display_style}">'
            f'<div class="season-panel-head">'
            f'<span class="season-panel-title">{info["icon"]} {info["label"]}\u9009\u54c1\u63a8\u8350\uff08{info["months"][0]}-{info["months"][-1]}\u6708\uff09{cur_mark}</span>'
            f'<span class="season-panel-meta">\u8986\u76d6 {d["events"]} \u4e2a\u8282\u65e5\u4e8b\u4ef6 \u00b7 {len(d["kws"])} \u4e2a\u63a8\u8350\u65b9\u5411</span>'
            f'</div>'
            f'<div class="season-panel-note">\U0001f50e \u4ee5\u4e0b\u5173\u952e\u8bcd\u5df2\u81ea\u52a8\u6ce8\u5165\u6bcf\u65e5\u96f7\u8fbe\u626b\u63cf\uff08\u4e0e\u5b63\u8282\u540c\u6b65\u8f6e\u6362\uff09\uff0c\u70b9\u51fb\u6708\u4efd\u6309\u94ae\u67e5\u770b\u8be5\u5b63\u8282\u8282\u65e5</div>'
            f'{deadline_div}'
            f'{region_div}'
            f'<div class="season-kw-list">{kws_html}</div>'
            f'      </div>'
        )
        panels.append(panel_html_str)
        panel_js.append(
            f'seasonPanelData["{key}"]={json.dumps(d["kws"], ensure_ascii=False)};'
        )

    panel_html = ('<div id="seasonPanelWrap">' + "".join(panels) + '</div>')
    panel_data_js = "const seasonPanelData={};\n" + "\n".join(panel_js) + f"\nconst currentSeasonKey=\"{cur}\";"

    return season_nav + panel_html, panel_data_js


def generate_festival_html(festivals):
    """生成 Festival Planner 的 HTML"""
    if not festivals:
        return '<div class="empty">暂无节日数据</div>'
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 统计紧急度
    stats = {"urgent": 0, "week": 0, "month": 0, "plan": 0, "past": 0}
    for f in festivals:
        urgency = get_urgency(f)
        stats[urgency] += 1

    total_skus = sum(len(f.get('products', [])) for f in festivals)
    
    # 找到最近的备货节点（用海运，周期最长）
    upcoming = None
    for f in festivals:
        urgency = get_urgency(f, "sea")
        if urgency not in ("past", "urgent"):
            f_date = datetime.strptime(f['date'], '%Y-%m-%d')
            mode = LOGISTICS_MODES["sea"]
            deadline = f_date - timedelta(days=mode['leadTime'] + ARRIVAL_BUFFER)
            if upcoming is None or deadline < upcoming['deadline']:
                upcoming = {"festival": f, "deadline": deadline, "urgency": urgency}
    
    # 最近备货节点那段先单独拼好。
    # 原本是把这段 f-string 直接嵌在下面的外层 f'''...''' 里，同类三引号
    # 套同类三引号要 Python 3.12+（PEP 701）才能解析，3.11 及以下直接
    # SyntaxError。拆出来就没有版本门槛了。
    if upcoming:
        fest = upcoming['festival']
        countdown_html = (
            f"· 最近备货节点：<strong>{fest['icon']} {fest['name']}</strong>"
            f"（{fest['date']}）· 选品截止 "
            f"<strong>{upcoming['deadline'].strftime('%Y-%m-%d')}</strong> · "
            f"<span class=\"badge {upcoming['urgency']}\">"
            f"{get_urgency_label(upcoming['urgency'])}</span>"
        )
    else:
        countdown_html = ''

    # 2026-08-28 四季选品面板
    season_panel, season_panel_js = generate_season_panel(festivals)
    
    # 生成 HTML
    html = f'''
    <div class="festival-header">
      <h2>📅 Festival Planner 2026 Jul - 2027 Jun | {len(festivals)} Events | {total_skus} SKUs</h2>
      <div class="countdown">
        今日 <strong>{today}</strong>
        {countdown_html}
      </div>
    </div>
    
    <div class="stat-cards">
      <div class="stat-card urgent" onclick="filterByUrgency('urgent')">
        <div class="num">{stats['urgent']}</div>
        <div class="label">🔴 紧急（已过截止）</div>
      </div>
      <div class="stat-card week" onclick="filterByUrgency('week')">
        <div class="num">{stats['week']}</div>
        <div class="label">🟠 本周必须启动</div>
      </div>
      <div class="stat-card month" onclick="filterByUrgency('month')">
        <div class="num">{stats['month']}</div>
        <div class="label">🟡 本月需备货</div>
      </div>
      <div class="stat-card plan" onclick="filterByUrgency('plan')">
        <div class="num">{stats['plan']}</div>
        <div class="label">🟢 规划观察中</div>
      </div>
    </div>
    
    <!-- 2026-08-28 季节选品面板 -->
    {season_panel}

    <div class="month-nav">
      {"".join(f'<a href="#month-{m}" onclick="scrollToMonth({m})">{m}月</a>' for m in range(1, 13))}
    </div>
    
    <!-- 2026-08-28 季节选品面板 -->
    <div class="season-filter-bar">
    </div>
    
    <div class="filter-bar festival-filter-bar">
      <div class="filter-group">
        <label>品类</label>
        <select id="filterCategory" onchange="filterFestivals()">
          <option value="">全部</option>
          <option value="decor">🎀装饰</option>
          <option value="gift">🎁礼品</option>
          <option value="apparel">👕服饰</option>
          <option value="home">🏠家居</option>
        </select>
      </div>
      <div class="filter-group">
        <label>月份</label>
        <select id="filterMonth" onchange="filterFestivals()">
          <option value="">全部</option>
          {"".join(f'<option value="{m}">{m}月</option>' for m in range(1, 13))}
        </select>
      </div>
      <div class="filter-group">
        <label>紧急度</label>
        <select id="filterUrgency" onchange="filterFestivals()">
          <option value="">全部</option>
          <option value="urgent">🔴紧急</option>
          <option value="week">🟠本周</option>
          <option value="month">🟡本月</option>
          <option value="plan">🟢规划</option>
          <option value="past">⚫已过</option>
        </select>
      </div>
      <input type="text" id="filterSearch" placeholder="搜索节日/SKU/关键词..." oninput="filterFestivals()">
      <label class="filter-toggle">
        <input type="checkbox" id="filterHidePast" checked onchange="filterFestivals()">
        隐藏已过节日
      </label>
      <button id="resetFilter" onclick="resetFilters()">重置</button>
    </div>
    
    <div class="festival-list">
    '''
    
    # 按月份分组
    by_month = {}
    for f in festivals:
        month = f.get('month', 0)
        if month not in by_month:
            by_month[month] = []
        by_month[month].append(f)
    
    # 生成月份卡片
    for month in range(1, 13):
        if month not in by_month:
            continue
        fests = sorted(by_month[month], key=lambda x: x['date'])
        
        html += f'''
      <div class="month-section" id="month-{month}" data-month="{month}">
        <h2>{month}月 ({len(fests)})</h2>
        <div class="festival-cards">
        '''
        
        for f in fests:
            urgency = get_urgency(f)
            importance = f.get('importance', 'A')
            products = f.get('products', [])
            festival_id = f.get('id', '')
            
            # 按品类统计
            products_by_category = {}
            for p in products:
                cat = p.get('category', 'other')
                if cat not in products_by_category:
                    products_by_category[cat] = 0
                products_by_category[cat] += 1
            
            # 品类筛选按钮（放在标题后面）
            # cat 来自节日数据的 category 字段，属于外部数据。原本直接拼进
            # onclick 的 JS 字符串里，数据里一个单引号就能跳出字符串执行代码
            # （audit P0 描述的同一类问题）。品类是个 slug，用字符白名单收紧。
            cat_tabs_html = '<span class="cat-tabs-inline">'
            cat_tabs_html += f'<button class="cat-pill active" onclick="filterProductCat(this, \'\')">全部 ({len(products)})</button>'
            for cat, count in products_by_category.items():
                cat_info = CATEGORY_MAP.get(cat, {"label": cat, "icon": "📦", "color": "#6b7280"})
                cat_slug = _safe_slug(cat)
                label = htmlmod.escape(str(cat_info["label"]))
                icon = htmlmod.escape(str(cat_info["icon"]))
                cat_tabs_html += (f'<button class="cat-pill" onclick="filterProductCat(this, \'{cat_slug}\')">'
                                  f'{icon} {label} ({count})</button>')
            cat_tabs_html += '</span>'
            
            # 生成产品表格
            products_html = ""
            if products:
                products_html = f'''
      <div class="products-section">
        <div class="products-header">
          <h4>📦 选品建议</h4>
          {cat_tabs_html}
        </div>
        <div class="product-table-wrap">
          <table class="product-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>品类</th>
                <th>成本</th>
                <th>售价</th>
                <th>毛利率</th>
                <th>匹配度</th>
                <th>风险</th>
                <th>Amazon</th>
                <th>1688</th>
              </tr>
            </thead>
            <tbody>
                '''
                
                for p in products:
                    risk_cls = {
                        "低": "risk-low",
                        "中": "risk-mid",
                        "高": "risk-high"
                    }.get(p.get('riskLevel', ''), 'risk-mid')
                    
                    cat_info = CATEGORY_MAP.get(p.get('category', ''), {"label": p.get('category', ''), "icon": "📦", "color": "#6b7280"})
                    
                    # Amazon 关键词链接（显示全部，最多4个）
                    keywords_html = "".join(
                        f'<a class="kw-link amazon" href="https://www.amazon.co.uk/s?k={urllib.parse.quote(kw)}" target="_blank">🛒 {kw}</a>'
                        for kw in p.get('keywords', [])[:4]
                    )
                    
                    # 1688 搜索链接
                    sourcing = p.get('sourcing', '')
                    search_term = ''
                    if sourcing and '1688:' in sourcing:
                        search_term = sourcing.split('1688:')[1].strip()
                    else:
                        search_term = p.get('sku', '')
                    
                    ali_html = ''
                    if search_term:
                        encoded_term = urllib.parse.quote(search_term, encoding='gbk', safe='')
                        ali_html = (f'<a class="kw-link ali" rel="noopener noreferrer" '
                                    f'href="https://s.1688.com/selloffer/offer_search.htm?keywords={encoded_term}" '
                                    f'target="_blank">🏭 {htmlmod.escape(search_term)}</a>')
                    
                    # data-cat 必须和上面按钮传的 slug 一致，否则筛选点不中；
                    # 其余字段一律 HTML 转义，别裸拼进标签
                    row_cat = _safe_slug(p.get('category', ''))
                    e = lambda v: htmlmod.escape(str(v if v is not None else ''))
                    _score = p.get('matchScore', 0)
                    _score = _score if isinstance(_score, int) and 0 <= _score <= 5 else 0

                    # 合规徽章：riskLevel 是人工手填的，会和店铺实际的禁售规则脱节
                    # （审计发现过 44 条标"低风险"其实是 is_forbidden() 会拦的违禁品）。
                    # 这里现算，跟雷达扫描用的是同一套判定，标签不会撒谎。
                    _compliance_text = ' '.join([
                        str(p.get('sku', '')), str(p.get('skuEn', '')),
                        ' '.join(p.get('keywords', []) or []),
                    ])
                    _forbidden_result = is_forbidden(_compliance_text, p.get('category', ''))
                    _is_forbidden = _forbidden_result[0] if isinstance(_forbidden_result, tuple) else _forbidden_result
                    _needs_review = str(p.get('riskNote', '')).startswith('⚠️待复核')
                    compliance_badge = ''
                    # 先判"已标记待复核"——这些人已经看过一遍、判断大概率是过滤词
                    # 误伤，不该再跟真违禁品混在一起显示成同一种"🚫"警示。
                    if _needs_review:
                        compliance_badge = ('<span class="compliance-flag review" '
                                             'title="疑似被过滤词误伤，需人工复核合规性">⚠️ 待复核</span>')
                    elif _is_forbidden:
                        compliance_badge = ('<span class="compliance-flag forbidden" '
                                             'title="命中店铺禁售规则，不建议选品">🚫 违禁风险</span>')

                    products_html += f'''
              <tr data-cat="{row_cat}">
                <td>
                  <div class="sku-name">{e(p.get('sku', ''))}</div>
                  <div class="sku-en">{e(p.get('skuEn', ''))}</div>
                  {compliance_badge}
                </td>
                <td><span class="cat-tag" style="background:{e(cat_info['color'])}15;color:{e(cat_info['color'])}">{e(cat_info['icon'])} {e(cat_info['label'])}</span></td>
                <td class="cost">{e(p.get('costRange', ''))}</td>
                <td class="price">{e(p.get('priceRange', ''))}</td>
                <td class="margin">{e(p.get('margin', ''))}</td>
                <td class="match">{"★" * _score}{"☆" * (5 - _score)}</td>
                <td><span class="risk {e(risk_cls)}">{e(p.get('riskLevel', ''))}</span></td>
                <td class="links">{keywords_html}</td>
                <td class="links">{ali_html}</td>
              </tr>
                    '''
                
                products_html += '''
            </tbody>
          </table>
        </div>
      </div>
                '''
            
            # 计算三种物流方式的选品截止日期
            deadlines = get_deadlines(f)
            deadline_text = " · ".join(
                f'{d["icon"]} {d["label"]} 截止 {d["date"]}'
                for d in deadlines.values()
            )
            
            html += f'''
      <div class="festival-card" id="festival-{festival_id}" data-urgency="{urgency}" data-category="{f.get('category', '')}" data-month="{month}" style="border-left-color:{f.get('themeColor', '#e5e7eb')}">
        <div class="card-header" onclick="this.parentElement.classList.toggle('expanded')">
          <div class="card-left">
            <span class="festival-icon">{f.get('icon', '📅')}</span>
            <div class="card-info">
              <div class="card-title">
                <span class="name-cn">{f.get('name', '')}</span>
                <span class="name-en">{f.get('nameEn', '')}</span>
                {"<span class='importance-tag'>S级</span>" if importance == 'S' else ''}
              </div>
              <div class="card-meta">
                {f.get('date', '')} · {len(products)} SKUs · {deadline_text}
              </div>
            </div>
          </div>
          <span class="urgency-tag {urgency}">{get_urgency_icon(urgency)} {get_urgency_label(urgency)}</span>
        </div>
        <div class="card-body">
          {products_html}
        </div>
      </div>
            '''
        
        html += '''
        </div>
      </div>
        '''
    
    html += '''
    </div>
    
    <!-- Back to Top Button -->
    <button id="backToTop" class="back-to-top" onclick="scrollToTop()" title="回到顶部">↑</button>
    
    <script>
    // 筛选功能
    function filterFestivals() {
      const category = document.getElementById('filterCategory').value;
      const month = document.getElementById('filterMonth').value;
      const urgency = document.getElementById('filterUrgency').value;
      const search = document.getElementById('filterSearch').value.toLowerCase();
      const hidePast = document.getElementById('filterHidePast').checked;

      document.querySelectorAll('.festival-card').forEach(card => {
        const cardMonth = card.dataset.month;
        const cardUrgency = card.dataset.urgency;
        const cardCategory = card.dataset.category;
        const cardText = card.textContent.toLowerCase();

        let show = true;
        // 已过节日默认收起，除非用户主动在紧急度里选"已过"查看
        if (hidePast && cardUrgency === 'past' && urgency !== 'past') show = false;
        if (category && cardCategory !== category) show = false;
        if (month && cardMonth !== month) show = false;
        if (urgency && cardUrgency !== urgency) show = false;
        if (search && !cardText.includes(search)) show = false;

        card.style.display = show ? '' : 'none';
      });
      
      // 隐藏空月份
      document.querySelectorAll('.month-section').forEach(section => {
        const visibleCards = section.querySelectorAll('.festival-card:not([style*="display: none"])');
        section.style.display = visibleCards.length > 0 ? '' : 'none';
      });
    }
    
    // 按紧急度筛选
    function filterByUrgency(urgency) {
      document.getElementById('filterUrgency').value = urgency;
      filterFestivals();
      
      // 滚动到第一个匹配的节日
      const firstCard = document.querySelector('.festival-card[data-urgency="' + urgency + '"]');
      if (firstCard) {
        firstCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstCard.classList.add('expanded');
      }
    }
    
    // 重置筛选
    function resetFilters() {
      document.getElementById('filterCategory').value = '';
      document.getElementById('filterMonth').value = '';
      document.getElementById('filterUrgency').value = '';
      document.getElementById('filterSearch').value = '';
      document.getElementById('filterHidePast').checked = true;
      filterFestivals();
    }
    
    // 滚动到指定月份
    function scrollToMonth(month) {
      const section = document.getElementById('month-' + month);
      if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
    
    // 产品品类筛选
    function filterProductCat(btn, cat) {
      const section = btn.closest('.products-section');
      section.querySelectorAll('.cat-pill').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      
      section.querySelectorAll('.product-table tbody tr').forEach(row => {
        row.style.display = (!cat || row.dataset.cat === cat) ? '' : 'none';
      });
    }
    
    // 回到顶部
    function scrollToTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // 显示/隐藏回到顶部按钮
    window.addEventListener('scroll', function() {
      const btn = document.getElementById('backToTop');
      if (btn) {
        btn.classList.toggle('show', window.scrollY > 300);
      }
    });

    // 2026-08-28 季节选品面板数据
    ''' + season_panel_js + '''
    function setSeason(btn, key) {
      document.querySelectorAll('.season-btn').forEach(b => b.classList.remove('season-btn-active'));
      btn.classList.add('season-btn-active');
      document.querySelectorAll('.season-panel').forEach(p => {
        p.style.display = (p.dataset.season === key) ? 'block' : 'none';
      });
      const monthMap = {spring:[3,4,5], summer:[6,7,8], autumn:[9,10,11], winter:[12,1,2]};
      window._seasonMonths = monthMap[key] || [];
      document.getElementById('filterMonth').value = '';
      filterFestivals();
    }

    // 初始加载即收起已过节日（filterHidePast 默认勾选）
    filterFestivals();
    </script>
    '''
    
    return html


if __name__ == '__main__':
    festivals = load_festivals()
    print(f"✅ 加载了 {len(festivals)} 个节日")
    for f in festivals[:3]:
        print(f"   - {f['icon']} {f['name']} ({f['date']})")
