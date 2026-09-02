"""选品雷达 / 趋势发现的数据加载。

从 generate_platform.py 平移过来，逻辑保持不变 —— 这里只是搬家，
不是改行为。搬的原因是今日概览也要读同一份数据，而
generate_platform.py 里这几个函数和 1000 行 HTML 拼接混在一起，
从别处 import 它会把整个页面生成的依赖一起拖进来。
"""
import json
from datetime import datetime

from .config import BASE

CHANNELS_DIR = BASE / 'data' / 'channels'
DISCOVERY_DIR = BASE / 'data' / 'discovery'


def consolidate_past_months(data_dict):
    """把过去月份的日期键（2026-06-21）并成月度键（2026-06）。

    当月和未来保持按天，历史按月合并，否则日期选择器会越来越长。
    """
    current_month = datetime.now().strftime('%Y-%m')
    monthly = {}
    to_remove = []

    for date_key in list(data_dict.keys()):
        if not (len(date_key) == 10 and date_key[4] == '-' and date_key[7] == '-'):
            continue
        month_key = date_key[:7]
        if month_key >= current_month:
            continue
        if month_key not in monthly:
            monthly[month_key] = {
                'products': [],
                'scan_date': month_key,
                'scan_time': '',
            }

        src = data_dict[date_key]
        existing_asins = {p.get('asin') for p in monthly[month_key].get('products', []) if p.get('asin')}
        for p in src.get('products', []):
            if p.get('asin') and p['asin'] not in existing_asins:
                monthly[month_key].setdefault('products', []).append(p)
                existing_asins.add(p['asin'])

        existing_kws = {i.get('keyword') for i in monthly[month_key].get('insights', []) if i.get('keyword')}
        for i in src.get('insights', []):
            if i.get('keyword') and i['keyword'] not in existing_kws:
                monthly[month_key].setdefault('insights', []).append(i)
                existing_kws.add(i['keyword'])

        if src.get('trend_forecast'):
            tf = src['trend_forecast']
            # 归一化：LLM cron 可能输出 dict {'forecast_text': '...'}，
            # 统一为 string 透传（见 generate_platform.py._extract_forecast_text）
            if isinstance(tf, dict):
                tf = tf.get('forecast_text', '')
            if not monthly[month_key].get('trend_forecast'):
                monthly[month_key]['trend_forecast'] = tf

        to_remove.append(date_key)

    for d in to_remove:
        del data_dict[d]
    data_dict.update(monthly)
    return data_dict


def load_all_radar(only_with_new=True):
    """按日期加载雷达扫描结果，同一天的多次扫描按 ASIN 去重合并。

    only_with_new：只保留有新品的日期。选品平台要这个行为（没新品的
    日期没必要出现在日期选择器里）；今日概览则需要看到今天的全部结果，
    所以传 False。
    """
    result = {}
    if not CHANNELS_DIR.is_dir():
        return result

    for f in sorted(CHANNELS_DIR.glob('*.json')):
        if '-rejected' in f.name or '-trends' in f.name or '-raw' in f.name:
            continue
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            continue
        if 'products' not in data or not data.get('scan_date'):
            continue

        date = data['scan_date']
        if date in result:
            existing = {p.get('asin') for p in result[date]['products'] if p.get('asin')}
            for p in data['products']:
                if p.get('asin') and p['asin'] not in existing:
                    result[date]['products'].append(p)
                    existing.add(p['asin'])
        else:
            result[date] = data

    result = consolidate_past_months(result)

    if not only_with_new:
        return result

    return {
        date: data for date, data in result.items()
        if any(p.get('is_new') is True for p in data.get('products', []))
    }


def load_all_discovery():
    """按日期加载趋势发现数据。"""
    result = {}
    if not DISCOVERY_DIR.is_dir():
        return result
    for f in sorted(DISCOVERY_DIR.glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get('scan_date'):
            result[data['scan_date']] = data
    return consolidate_past_months(result)
