"""补货告警摘要。

数据源是 output/analysis/index.html —— 一个**仓库外**项目
(~/product-analysis/generate_html.py) 生成的 HTML 产物，没有配套的
JSON。所以只能解析 HTML，而解析别人的产物是脆的：对方调一次模板
这里就可能失效。

因此整个模块的原则是：**宁可说不知道，也不要猜。**
解析不出来就返回 CardData.fail(原因)，让页面显示「数据不可用」，
绝不返回「紧急 0 个」——那会让人以为库存很健康。
（audit P3 / DESIGN-DECISIONS D7）
"""
import html as htmlmod
import re

from .config import OUTPUT_DIR
from .field import CardData

ANALYSIS_INDEX = OUTPUT_DIR / 'analysis' / 'index.html'

# 行级紧急度：product-analysis 用 class 标在 <tr> 上
LEVEL_BY_CLASS = {
    'urgent-row': 'urgent',
    'watch-row': 'watch',
    'steady-row': 'steady',
}

LEVEL_LABEL = {
    'urgent': '紧急',
    'watch': '观察',
    'steady': '正常',
}


def _text(fragment: str) -> str:
    """扒掉标签取纯文本。"""
    return htmlmod.unescape(re.sub(r'<[^>]+>', '', fragment)).strip()


def parse_analysis(path=None) -> CardData:
    """解析补货页，返回各紧急度的计数和最紧急的几条。

    脱敏：只取 SKU、店铺、可售天数、紧急度。
    售价/毛利率/7天销量/日均一律不取 —— PROJECT-VISION §6 要求
    毛利率、月销量、库存这类字段不上公开页。
    """
    path = path or ANALYSIS_INDEX
    if not path.exists():
        return CardData.absent(f'{path.name} 不存在，补货管线可能还没跑过')

    try:
        raw = path.read_text(encoding='utf-8')
    except OSError as e:
        return CardData.fail(f'读取补货页失败: {e}')

    rows = re.findall(r'<tr([^>]*)>(.*?)</tr>', raw, re.S)
    if not rows:
        return CardData.fail('补货页里没找到表格行，上游模板可能变了')

    counts = {'urgent': 0, 'watch': 0, 'steady': 0}
    items = []

    for attrs, body in rows:
        level = None
        for cls, name in LEVEL_BY_CLASS.items():
            if cls in attrs:
                level = name
                break
        if level is None:
            continue  # 表头或其它行

        counts[level] += 1

        cells = re.findall(r'<td[^>]*>(.*?)</td>', body, re.S)
        if len(cells) < 6:
            continue
        store_m = re.search(r'data-store="([^"]*)"', attrs)
        items.append({
            'level': level,
            'level_label': LEVEL_LABEL[level],
            'store': store_m.group(1) if store_m else '',
            'sku': _text(cells[2]),
            'name': _text(cells[3]),
            'days_left': _text(cells[5]),
        })

    if not any(counts.values()):
        return CardData.fail('补货页有表格但没有带紧急度标记的行，上游模板可能变了')

    # 紧急的排前面，同级按可售天数升序（数字扒不出来的排后面）
    order = {'urgent': 0, 'watch': 1, 'steady': 2}

    def sort_key(it):
        m = re.search(r'\d+', it['days_left'])
        return (order[it['level']], int(m.group()) if m else 9999)

    items.sort(key=sort_key)

    return CardData(payload={
        'counts': counts,
        'total': sum(counts.values()),
        'top': items[:8],
    })
