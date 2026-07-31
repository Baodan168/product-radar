"""各板块的数据新鲜度。

回答的是「扫描是不是断了」——PROJECT-VISION 里用户「不看盘不盯屏，
依赖自动化推送做决策」，那自动化本身停了就必须一眼能看出来，
否则会拿着三天前的数据当今天的用。

⚠️ 不要用文件 mtime 判新鲜度。git clone / checkout 会把所有文件的
mtime 刷成当前时间，CI 和新机器上一律显示「刚刚」，等于没有这张卡。
所以一律从**内容**里取日期：JSON 读 scan_date，文件名兜底，
补货页从「分析日期: ...」正则里取。

另外区分两件事：
    新鲜度   数据本身有多旧（本模块，生成期算）
    可达性   页面现在能不能打开（assets/portal.js 的探针，运行期算）
两者会单独出问题：扫描挂了但页面还在（旧数据），
或者数据是新的但 Pages 部署失败（页面 404）。
"""
import json
import re
from datetime import datetime

from .config import BASE, OUTPUT_DIR
from .field import CardData

# 各源的预期更新节奏（小时）。超过 stale 记警告，超过 dead 记故障。
# 阈值按 ARCHITECTURE.md §9 的调度表定：
#   雷达扫描每天 09:10 / 14:00（周一到六）→ 隔夜 + 周日空窗，给 48h
#   趋势发现每天 08:40 → 同上
#   补货每周一/四 08:00 → 最长间隔 4 天，给 120h
SOURCES = [
    {'key': 'platform', 'label': '雷达扫描', 'kind': 'scan',
     'dir': 'data/channels', 'pattern': '*.json', 'stale_h': 48, 'dead_h': 96},
    {'key': 'platform', 'label': '趋势发现', 'kind': 'scan',
     'dir': 'data/discovery', 'pattern': '*.json', 'stale_h': 48, 'dead_h': 96},
    {'key': 'analysis', 'label': '补货跟进', 'kind': 'restock',
     'stale_h': 120, 'dead_h': 240},
]

DATE_IN_NAME = re.compile(r'(\d{4}-\d{2}-\d{2})')
RESTOCK_DATE = re.compile(r'分析日期[:：]\s*(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?')


def _parse(date_str, time_str=None):
    if not date_str:
        return None
    try:
        if time_str:
            return datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


def _latest_scan_date(subdir: str, pattern: str):
    """扫描数据的最新日期。优先读 JSON 里的 scan_date，读不到退回文件名。"""
    d = BASE / subdir
    if not d.is_dir():
        return None
    newest = None
    for f in sorted(d.glob(pattern)):
        if '-rejected' in f.name or '-trends' in f.name or '-raw' in f.name:
            continue
        stamp = None
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            stamp = _parse(data.get('scan_date'), (data.get('scan_time') or '')[:5] or None)
        except (json.JSONDecodeError, OSError, TypeError):
            pass
        if stamp is None:
            m = DATE_IN_NAME.search(f.name)
            stamp = _parse(m.group(1)) if m else None
        if stamp and (newest is None or stamp > newest):
            newest = stamp
    return newest


def _restock_date():
    """补货页的分析日期，从页面文案里取。"""
    path = OUTPUT_DIR / 'analysis' / 'index.html'
    if not path.exists():
        return None
    try:
        m = RESTOCK_DATE.search(path.read_text(encoding='utf-8'))
    except OSError:
        return None
    return _parse(m.group(1), m.group(2)) if m else None


def _humanize(hours: float) -> str:
    if hours < 1:
        return '刚刚'
    if hours < 24:
        return f'{int(hours)} 小时前'
    return f'{int(hours / 24)} 天前'


def collect_freshness(now=None) -> CardData:
    now = now or datetime.now()
    rows = []
    worst = 'ok'
    rank = {'ok': 0, 'warn': 1, 'unknown': 1, 'error': 2}

    for src in SOURCES:
        if src['kind'] == 'restock':
            stamp = _restock_date()
        else:
            stamp = _latest_scan_date(src['dir'], src['pattern'])

        if stamp is None:
            rows.append({'label': src['label'], 'module': src['key'],
                         'health': 'unknown', 'detail': '取不到日期'})
            if rank['unknown'] > rank[worst]:
                worst = 'unknown'
            continue

        age_h = (now - stamp).total_seconds() / 3600
        if age_h >= src['dead_h']:
            health = 'error'
        elif age_h >= src['stale_h']:
            health = 'warn'
        else:
            health = 'ok'
        if rank[health] > rank[worst]:
            worst = health

        rows.append({
            'label': src['label'],
            'module': src['key'],
            'health': health,
            'detail': _humanize(age_h),
            'updated': stamp.strftime('%m-%d %H:%M'),
        })

    # 跨境雷达在独立仓库，本地拿不到它的更新时间。
    # 只能由运行期探针判可达性，且跨域连状态码都读不到 —— 如实标未知。
    rows.append({'label': '跨境雷达', 'module': 'radar',
                 'health': 'unknown', 'detail': '独立仓库，见板块内'})

    return CardData(payload={'rows': rows, 'worst': worst})
