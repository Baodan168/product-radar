#!/usr/bin/env python3
"""
分析用户手动标记为"不考虑"的产品，提取共同特征，建议过滤规则改进。
数据来源：rejected_by_user.json（前端自动同步）

用法：python3 analyze_rejected.py [--add-rules]
  --add-rules  自动将建议的规则写入 config.json
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent
REJECTED_FILE = BASE / "rejected_by_user.json"
CONFIG_FILE = BASE / "config.json"


def load_rejected():
    if not REJECTED_FILE.exists():
        return {}
    return json.loads(REJECTED_FILE.read_text(encoding="utf-8"))


def load_config():
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def extract_keywords(name):
    """从产品名中提取有意义的关键词（去掉停用词和数字）"""
    stop_words = {
        'for', 'with', 'and', 'the', 'a', 'an', 'of', 'in', 'on', 'at',
        'to', 'is', 'it', 'by', 'from', 'or', 'as', 'be', 'this', 'that',
        'are', 'was', 'were', 'been', 'has', 'have', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
        'new', 'set', 'pcs', 'pack', 'piece', 'pieces', 'pc', 'mm', 'cm',
        'ml', 'l', 'g', 'kg', 'x', 'size', 'colour', 'color', 'style',
        'home', 'kitchen', 'office', 'car', 'outdoor', 'indoor',
    }
    words = re.findall(r'[a-z]{3,}', name.lower())
    return [w for w in words if w not in stop_words]


def analyze_patterns(rejected):
    """分析被拒绝产品的共同模式"""
    if not rejected:
        return {}

    categories = Counter()
    channels = Counter()
    keywords = Counter()
    price_ranges = {'<6': 0, '6-8': 0, '8-10': 0, '>10': 0}
    review_ranges = {'0-5': 0, '5-20': 0, '20-50': 0, '50-100': 0}
    source_counter = Counter()
    reasons = []  # 自动推断的拒绝原因

    for asin, info in rejected.items():
        name = info.get('name', '')
        cat = info.get('category', 'Unknown')
        categories[cat] += 1
        channels[info.get('channel', '')] += 1

        # 价格分布
        price = info.get('price', 0)
        if price < 6: price_ranges['<6'] += 1
        elif price < 8: price_ranges['6-8'] += 1
        elif price <= 10: price_ranges['8-10'] += 1
        else: price_ranges['>10'] += 1

        # 评论分布
        reviews = info.get('reviews', 0)
        if reviews <= 5: review_ranges['0-5'] += 1
        elif reviews <= 20: review_ranges['5-20'] += 1
        elif reviews <= 50: review_ranges['20-50'] += 1
        else: review_ranges['50-100'] += 1

        # 来源
        for src in info.get('sources', []):
            source_counter[src] += 1

        # 提取关键词
        for kw in extract_keywords(name):
            keywords[kw] += 1

    return {
        'total': len(rejected),
        'categories': categories,
        'channels': channels,
        'keywords': keywords,
        'price_ranges': price_ranges,
        'review_ranges': review_ranges,
        'sources': source_counter,
    }


VALID_CATS_MIN = 3


def load_passed_categories():
    """统计历史通过集（真正展示过的产品）的类目分布，作为类目拒绝率的真实分母。

    2026-10-17 修两点：
    1) 原来类目占比用「被拒样本」做分母（9/19=47%），把「被拒里汽车多」
       误读成「汽车类不适合」。真实拒绝率应 = 被拒数 / 该类展示总数。
    2) 分母必须按 ASIN 去重：同一个产品会在多个日期的扫描文件里重复出现，
       按文件累加会把 Automotive 摊薄成 9/85=11%，真实是 9/29=31%。
    """
    from collections import Counter
    counter = Counter()
    seen = set()
    channels_dir = BASE / "data" / "channels"
    if not channels_dir.exists():
        return counter
    for f in sorted(channels_dir.glob("*.json")):
        name = f.name
        if "-raw" in name or "-rejected" in name or "-trends" in name:
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        items = data if isinstance(data, list) else data.get("products", [])
        for p in items:
            if not isinstance(p, dict):
                continue
            asin = p.get("asin") or ""
            if asin:
                if asin in seen:
                    continue
                seen.add(asin)
            counter[(p.get("category") or "Unknown")] += 1
    return counter


def suggest_rules(analysis, config):
    """基于分析结果建议新的过滤规则"""
    suggestions = []
    forbidden_kw = set(config.get('forbidden_keywords', []))
    existing_lower = {k.lower() for k in forbidden_kw}

    total = analysis.get('total', 0)
    if total < 3:
        return suggestions

    # 1. 高频关键词（出现>=2次且占比>=30%）→ 建议加入禁选词
    keywords = analysis.get('keywords', Counter())
    for kw, count in keywords.most_common(20):
        ratio = count / total
        if count >= 2 and ratio >= 0.3:
            if kw not in existing_lower and len(kw) >= 4:
                suggestions.append({
                    'type': 'forbidden_keyword',
                    'keyword': kw,
                    'count': count,
                    'ratio': f'{ratio:.0%}',
                    'reason': f'"{kw}" 出现在 {count}/{total} 个不考虑产品中（{ratio:.0%}）',
                })

    # 2. 类目拒绝率 = 该类被拒数 / 该类历史展示总数（真实分母）
    #    旧逻辑用「被拒样本总数」当分母，会把“被拒里汽车多”误读成“汽车类不适合”。
    categories = analysis.get('categories', Counter())
    passed_cats = load_passed_categories()
    for cat, count in categories.most_common(8):
        total_in_cat = passed_cats.get(cat, 0)
        if total_in_cat < VALID_CATS_MIN:
            continue
        ratio = count / total_in_cat
        if count >= 3 and ratio >= 0.25:
            suggestions.append({
                'type': 'category_warning',
                'category': cat,
                'count': count,
                'total': total_in_cat,
                'ratio': f'{ratio:.0%}',
                'reason': f'类目 "{cat}" 展示 {total_in_cat} 个中 {count} 个被拒（{ratio:.0%}）',
            })

    # 3. 来源分析 — 如果某个来源的产品被大量拒绝，说明该来源质量低
    sources = analysis.get('sources', Counter())
    for src, count in sources.most_common(5):
        # 需要知道该来源总共推了多少产品，这里只做简单计数
        pass

    return suggestions


def format_report(analysis, suggestions):
    """格式化分析报告"""
    lines = []
    total = analysis.get('total', 0)

    lines.append(f"**不考虑产品分析** — 共 {total} 个产品\n")

    # 类目分布
    lines.append("**类目分布：**")
    for cat, count in analysis.get('categories', Counter()).most_common(8):
        bar = '█' * count + '░' * max(0, 5 - count)
        lines.append(f"  {bar} {cat}: {count}个")

    # 关键词 Top 10
    lines.append("\n**高频关键词（Top 10）：**")
    for kw, count in analysis.get('keywords', Counter()).most_common(10):
        lines.append(f"  • {kw} — {count}次")

    # 价格分布
    lines.append("\n**价格分布：**")
    for range_label, count in analysis.get('price_ranges', {}).items():
        lines.append(f"  {range_label}: {count}个")

    # 建议
    if suggestions:
        lines.append(f"\n**建议新增规则（{len(suggestions)}条）：**")
        for i, s in enumerate(suggestions, 1):
            if s['type'] == 'forbidden_keyword':
                lines.append(f"  {i}. 🔤 禁选词: \"{s['keyword']}\" — {s['reason']}")
            elif s['type'] == 'category_warning':
                lines.append(f"  {i}. ⚠️ 类目预警: {s['category']} — {s['reason']}")
    else:
        lines.append("\n暂无新规则建议（样本不足或无明显模式）")

    return '\n'.join(lines)


def auto_add_rules(suggestions, config):
    """自动将建议的禁选词写入 config.json"""
    new_keywords = []
    for s in suggestions:
        if s['type'] == 'forbidden_keyword':
            new_keywords.append(s['keyword'])

    if not new_keywords:
        print("没有新的禁选词需要添加")
        return

    forbidden = config.get('forbidden_keywords', [])
    existing_lower = {k.lower() for k in forbidden}
    added = []
    for kw in new_keywords:
        if kw.lower() not in existing_lower:
            forbidden.append(kw)
            added.append(kw)

    if added:
        config['forbidden_keywords'] = forbidden
        CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"✅ 已添加 {len(added)} 个禁选词: {', '.join(added)}")
    else:
        print("所有建议的禁选词已存在")


def main():
    add_rules = '--add-rules' in sys.argv

    rejected = load_rejected()
    if not rejected:
        print("📭 没有不考虑产品数据")
        print(f"   数据文件: {REJECTED_FILE}")
        print("   请在选品雷达页面标记几个\"不考虑\"产品后再运行")
        return

    config = load_config()
    analysis = analyze_patterns(rejected)
    suggestions = suggest_rules(analysis, config)
    report = format_report(analysis, suggestions)

    print(report)

    if add_rules and suggestions:
        auto_add_rules(suggestions, config)


if __name__ == '__main__':
    main()
