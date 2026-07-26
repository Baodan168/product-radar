#!/usr/bin/env python3
"""
Festival Planner — 从 uk-festival-planner 提取数据，集成到选品平台
"""

import json
import subprocess
import tempfile
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

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


def load_festivals():
    """加载 Festival 数据"""
    html_file = Path('/home/lee/uk-festival-planner/index.html')
    if not html_file.exists():
        return []
    
    content = html_file.read_text(encoding='utf-8')
    start = content.find('const FESTIVALS = [')
    if start == -1:
        return []
    
    bracket_count = 0
    i = start + len('const FESTIVALS = ')
    end = None
    while i < len(content):
        if content[i] == '[':
            bracket_count += 1
        elif content[i] == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end = i + 1
                break
        i += 1
    
    if not end:
        return []
    
    js_array = content[start + len('const FESTIVALS = '):end]
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(f'const FESTIVALS = {js_array};\n')
            f.write('console.log(JSON.stringify(FESTIVALS));\n')
            temp_file = f.name
        
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True, text=True, timeout=30
        )
        
        import os
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Node.js 解析失败: {e}")
    
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

    # 生成 HTML
    html = f'''
    <div class="festival-header">
      <h2>📅 Festival Planner 2026 Jul - 2027 Jun | {len(festivals)} Events | 300+ SKUs</h2>
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
    
    <div class="month-nav">
      {"".join(f'<a href="#month-{m}" onclick="scrollToMonth({m})">{m}月</a>' for m in range(1, 13))}
    </div>
    
    <div class="filter-bar">
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
            cat_tabs_html = '<span class="cat-tabs-inline">'
            cat_tabs_html += f'<button class="cat-pill active" onclick="filterProductCat(this, \'\')">全部 ({len(products)})</button>'
            for cat, count in products_by_category.items():
                cat_info = CATEGORY_MAP.get(cat, {"label": cat, "icon": "📦", "color": "#6b7280"})
                cat_tabs_html += f'<button class="cat-pill" onclick="filterProductCat(this, \'{cat}\')">{cat_info["icon"]} {cat_info["label"]} ({count})</button>'
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
                        ali_html = f'<a class="kw-link ali" href="https://s.1688.com/selloffer/offer_search.htm?keywords={encoded_term}" target="_blank">🏭 {search_term}</a>'
                    
                    products_html += f'''
              <tr data-cat="{p.get('category', '')}">
                <td>
                  <div class="sku-name">{p.get('sku', '')}</div>
                  <div class="sku-en">{p.get('skuEn', '')}</div>
                </td>
                <td><span class="cat-tag" style="background:{cat_info['color']}15;color:{cat_info['color']}">{cat_info['icon']} {cat_info['label']}</span></td>
                <td class="cost">{p.get('costRange', '')}</td>
                <td class="price">{p.get('priceRange', '')}</td>
                <td class="margin">{p.get('margin', '')}</td>
                <td class="match">{"★" * p.get('matchScore', 0)}{"☆" * (5 - p.get('matchScore', 0))}</td>
                <td><span class="risk {risk_cls}">{p.get('riskLevel', '')}</span></td>
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
      
      document.querySelectorAll('.festival-card').forEach(card => {
        const cardMonth = card.dataset.month;
        const cardUrgency = card.dataset.urgency;
        const cardCategory = card.dataset.category;
        const cardText = card.textContent.toLowerCase();
        
        let show = true;
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
    </script>
    '''
    
    return html


if __name__ == '__main__':
    festivals = load_festivals()
    print(f"✅ 加载了 {len(festivals)} 个节日")
    for f in festivals[:3]:
        print(f"   - {f['icon']} {f['name']} ({f['date']})")
