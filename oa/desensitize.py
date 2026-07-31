"""补货跟进页的发布边界脱敏。

## 为什么在这里做

PROJECT-VISION §6 和 CLAUDE.md 都写着「毛利率/月销量/库存已脱敏」，但
`output/analysis/` 下 47 个文件实际都在公开页展示毛利率，详情页还有
7 天销量和日均。文档和现实对不上。

根因够不到：这些 HTML 由本机 `~/product-analysis/` 生成（`transform_analysis.py:5`
读的就是那个路径），源码不在任何 GitHub 仓库里。但**发布边界够得到**——
文件是 git 跟踪的，经 `update.yml` 的 `cp -r output/*` 进 Pages。

所以在这一层拦截。好处是不管上游生成器怎么变都拦得住，
和 `oa/restock.py`（容错解析上游产物）、`oa/safe_write.py`（防塌缩）
是同一条「不信上游」的思路。

## 脱敏什么

脱敏：毛利率、7 天销量、日均。
保留：售价、可售天数、建议补货量、库存状态标签、FBA 可售。
（保留项是补货决策的核心信号，删了这个板块就没用了。）

方式是换成档位标签而不是删列 —— PROJECT-VISION §6 的原话是
「保留板块入口和功能，仅隐藏数字」。

## 改 HTML 用正则很脆，所以

这里是**写**不是读，改错会毁页面。`scrub_html()` 结束前会重新扫一遍
产物，只要目标字段附近还留着数字就抛异常、拒绝写入。
宁可报错，也不要写出一份「看起来脱敏了其实没有」的页面。
"""
import json
import re
from pathlib import Path

from .config import BASE, OUTPUT_DIR

ANALYSIS_DIR = OUTPUT_DIR / 'analysis'

# 需要脱敏的字段。键是页面上的标签文字。
MARGIN = '毛利率'
WEEKLY = '7天销量'
DAILY = '日均'
DAILY_KPI = '日均销量'   # 详情页 KPI 卡用的是这个全称


def _min_margin_pct():
    """达标线取 config.json 的 min_profit_margin，不另立标准。"""
    try:
        cfg = json.loads((BASE / 'config.json').read_text(encoding='utf-8'))
        return float(cfg.get('min_profit_margin', 0.2)) * 100
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return 20.0


def bucket_margin(pct):
    """毛利率 → 档位。达标线锚定 config 的 min_profit_margin（默认 20%）。"""
    if pct is None:
        return '—'
    target = _min_margin_pct()
    if pct >= target * 1.75:      # ≥35%
        return '优秀'
    if pct >= target:             # ≥20%
        return '达标'
    if pct >= target / 2:         # ≥10%
        return '待优化'
    return '偏低'


def bucket_daily(v):
    """日均销量 → 档位。实际数据分布 0.6–18.3。"""
    if v is None:
        return '—'
    if v >= 5:
        return '高'
    if v >= 1:
        return '中'
    return '低'


def bucket_weekly(v):
    """7 天销量 → 档位。按日均等价折算，和 bucket_daily 口径一致。"""
    if v is None:
        return '—'
    return bucket_daily(v / 7.0)


def _num(text):
    """从单元格文本里抠出数字。抠不到返回 None（不当成 0）。"""
    if text is None:
        return None
    m = re.search(r'-?[\d.]+', str(text).replace(',', ''))
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def _strip_tags(html):
    return re.sub(r'<[^>]+>', '', html).strip()


def _already_bucketed(text):
    """这个值是不是已经脱敏过了。

    幂等性要靠它：脱敏后的值（达标/中/低/—）里没有数字，
    再跑一遍时 _num() 会返回 None、档位函数返回「—」，
    等于把好不容易换上的标签又抹成占位符。
    所以没有数字的一律跳过。
    """
    return not re.search(r'\d', _strip_tags(text) if '<' in str(text) else str(text))


# ── 形态 1：index.html 的表格 ──────────────────────────

def scrub_index_table(html):
    """按表头文字定位列，再改对应 <td>。

    不写死列下标 —— 上游加列删列时按下标改会改错列（把运输方式
    当成毛利率之类）。定位不到目标列就原样返回，交给自检去拦。
    """
    heads = [_strip_tags(h) for h in re.findall(r'<th[^>]*>(.*?)</th>', html, re.S)]
    if not heads:
        return html

    targets = {}
    for i, h in enumerate(heads):
        if h == MARGIN:
            targets[i] = bucket_margin
        elif h == WEEKLY:
            targets[i] = bucket_weekly
        elif h == DAILY:
            targets[i] = bucket_daily
    if not targets:
        return html

    def fix_row(row_match):
        row = row_match.group(0)
        cells = list(re.finditer(r'<td([^>]*)>(.*?)</td>', row, re.S))
        if not cells:
            return row
        out, last = [], 0
        for i, c in enumerate(cells):
            out.append(row[last:c.start()])
            if i in targets and not _already_bucketed(c.group(2)):
                label = targets[i](_num(_strip_tags(c.group(2))))
                out.append(f'<td{c.group(1)}>{label}</td>')
            else:
                out.append(c.group(0))
            last = c.end()
        out.append(row[last:])
        return ''.join(out)

    return re.sub(r'<tr[^>]*>.*?</tr>', fix_row, html, flags=re.S)


# ── 形态 2：详情页 KPI 卡 ──────────────────────────────

# 值在标签前面，所以用标签反向锚定它前面那个 value。
#
# ⚠️ 中间那段必须禁止跨卡片。用朴素的 (.*?) 会出事：正则从第一张卡
# （售价）的 oa-kpi-value 开始尝试，发现它的标签不是目标，就把 .*? 一路
# 撑到后面某张目标卡，把中间的售价、库存状态两张卡整个吞掉。
# 实测就是这么丢了 46 个详情页的两张 KPI 卡。
# tempered dot 保证匹配区间内不出现另一个 kpi-value/kpi-label。
_KPI_RE = re.compile(
    r'(<div class="oa-kpi-value"[^>]*>)'
    r'((?:(?!oa-kpi-label|oa-kpi-value).)*?)'
    r'(</div>\s*<div class="oa-kpi-label"[^>]*>)'
    r'(' + '|'.join(map(re.escape, (MARGIN, WEEKLY, DAILY_KPI))) + r')'
    r'(</div>)',
    re.S)

_KPI_BUCKETS = {MARGIN: bucket_margin, WEEKLY: bucket_weekly, DAILY_KPI: bucket_daily}


def scrub_detail_kpis(html):
    def fix(m):
        label = m.group(4)
        if _already_bucketed(m.group(2)):
            return m.group(0)          # 已脱敏，别再动（幂等）
        value = _KPI_BUCKETS[label](_num(_strip_tags(m.group(2))))
        return f'{m.group(1)}{value}{m.group(3)}{label}{m.group(5)}'
    return _KPI_RE.sub(fix, html)


# ── 形态 3：详情页正文散文（最容易漏的一处）──────────

def scrub_detail_prose(html):
    """数字嵌在中文句子里，逐条改写。

    实测 46 个详情页只有三种句式，全部覆盖：
      7天销量4件，日均0.6件。
      毛利率4.05%(1-10%)✓。   /   毛利率21.2%&gt;20%✓。
      按日均0.6件×30天=30件。
    """
    # 销量句
    def fix_sales(m):
        return (f'7天销量{bucket_weekly(_num(m.group(1)))}，'
                f'日均{bucket_daily(_num(m.group(2)))}。')
    html = re.sub(r'7天销量([\d.]+)件，日均([\d.]+)件。', fix_sales, html)

    # 毛利率句。后面跟的 (1-10%) / &gt;20% 本身就是区间，一并去掉，
    # 否则等于换个形式把数字说出来
    def fix_margin(m):
        return f'毛利率{bucket_margin(_num(m.group(1)))}。'
    html = re.sub(
        r'毛利率([\d.]+)%\s*(?:&gt;\s*[\d.]+%|>\s*[\d.]+%|\([\d.]+\s*-\s*[\d.]+%\))?\s*[✓✗]?。',
        fix_margin, html)

    # 补货算式。建议补货量按用户选择保留，但算式里的日均是乘数——
    # 留着算式等于把日均反推出来（30÷30=1），所以去掉乘法过程
    html = re.sub(r'按日均[\d.]+件×(\d+)天=(\d+)件。',
                  lambda m: f'按 {m.group(1)} 天用量估算，建议补 {m.group(2)} 件。', html)

    return html


# ── 自检 ───────────────────────────────────────────────

# 脱敏后这些都不该再匹配上。命中即说明有遗漏形态。
LEAK_PATTERNS = [
    (re.compile(r'毛利率[^<。，]{0,4}[\d.]+\s*%'), '毛利率仍带百分比'),
    (re.compile(r'7天销量[^<。，]{0,4}[\d.]+'), '7天销量仍带数字'),
    (re.compile(r'日均[销量]{0,2}[^<。，×]{0,4}[\d.]+'), '日均仍带数字'),
    (re.compile(r'<div class="oa-kpi-value"[^>]*>[^<]*[\d.]+[^<]*</div>\s*'
                r'<div class="oa-kpi-label"[^>]*>(?:毛利率|7天销量|日均销量)</div>'),
     'KPI 卡的值仍是数字'),
]


def _table_leaks(html):
    """表格里的泄露：表头叫毛利率/7天销量/日均，而该列单元格还是数字。

    这一条单独写，因为表格里的表头和单元格离得远，
    上面那些「标签紧挨着数字」的正则扫不到。
    """
    heads = [_strip_tags(h) for h in re.findall(r'<th[^>]*>(.*?)</th>', html, re.S)]
    watched = {i: h for i, h in enumerate(heads) if h in (MARGIN, WEEKLY, DAILY)}
    if not watched:
        return []

    leaks = []
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S):
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        for i, label in watched.items():
            if i >= len(cells):
                continue
            text = _strip_tags(cells[i])
            if re.search(r'\d', text):
                leaks.append((f'表格「{label}」列仍是数字', text[:40]))
    return leaks


def find_leaks(html):
    """返回 [(说明, 命中片段)]。空列表代表干净。"""
    leaks = []
    for pat, desc in LEAK_PATTERNS:
        for m in pat.finditer(html):
            leaks.append((desc, m.group(0)[:80]))
    leaks.extend(_table_leaks(html))
    return leaks


class DesensitizeError(RuntimeError):
    """脱敏没做干净、或者把不该动的删了。调用方必须放弃写入。"""


# 脱敏不该碰的东西。原文里有、脱敏后没了，就是误删。
#
# 这条检查是被真事逼出来的：KPI 正则一度跨卡片匹配，把 46 个详情页的
# 「售价」「库存状态」两张卡整个吞了。而 find_leaks() 完全看不出来——
# 被删的卡里没有敏感数字，体积也只掉了 4%，两道网都漏了。
# 只查「敏感数据还在不在」是不够的，还得查「该在的还在不在」。
PRESERVED_MARKERS = [
    '售价', '库存状态', 'FBA可售', '可售天数', '建议补货', '运输方式',
    'oa-kpi-label', 'back-link', '</html>',
]


def check_preserved(before, after, name='<html>'):
    """返回被误删的标记列表。"""
    lost = []
    for marker in PRESERVED_MARKERS:
        n_before = before.count(marker)
        if n_before == 0:
            continue
        n_after = after.count(marker)
        if n_after < n_before:
            lost.append(f'{marker}（{n_before} → {n_after}）')
    return lost


def scrub_html(html, name='<html>'):
    """脱敏一份 HTML。做不干净或者误删了东西，都抛异常，绝不返回半成品。"""
    out = scrub_index_table(html)
    out = scrub_detail_kpis(out)
    out = scrub_detail_prose(out)

    leaks = find_leaks(out)
    if leaks:
        detail = '; '.join(f'{d}: {s}' for d, s in leaks[:3])
        raise DesensitizeError(
            f'{name} 脱敏后仍有敏感数据（共 {len(leaks)} 处）：{detail}。'
            f'上游模板可能变了，需要更新 oa/desensitize.py 的匹配规则。')

    lost = check_preserved(html, out, name)
    if lost:
        raise DesensitizeError(
            f'{name} 脱敏时误删了内容：{"、".join(lost)}。'
            f'很可能是某条正则跨越了元素边界，拒绝写入。')

    # 和 oa/safe_write.py 同一条原则：产物明显变短说明正则吃掉了整段
    if len(out) < len(html) * 0.9:
        raise DesensitizeError(
            f'{name} 脱敏后体积从 {len(html)} 掉到 {len(out)}，疑似误删，拒绝写入。')

    return out


# ── 目录级操作 ─────────────────────────────────────────

def scan_dir(directory=None):
    """只读扫描：返回 {文件名: [泄露项]}，不改文件。"""
    directory = Path(directory or ANALYSIS_DIR)
    result = {}
    if not directory.is_dir():
        return result
    for f in sorted(directory.glob('*.html')):
        leaks = find_leaks(f.read_text(encoding='utf-8'))
        if leaks:
            result[f.name] = leaks
    return result


def scrub_dir(directory=None, dry_run=False):
    """脱敏整个目录。返回 (已改文件名列表, 跳过的)。

    任何一个文件脱敏失败都直接抛出 —— 不做「改一半」。
    """
    directory = Path(directory or ANALYSIS_DIR)
    changed, untouched = [], []
    if not directory.is_dir():
        return changed, untouched

    for f in sorted(directory.glob('*.html')):
        original = f.read_text(encoding='utf-8')
        scrubbed = scrub_html(original, f.name)
        if scrubbed == original:
            untouched.append(f.name)
            continue
        if not dry_run:
            f.write_text(scrubbed, encoding='utf-8')
        changed.append(f.name)
    return changed, untouched
