#!/usr/bin/env python3
"""Daily selection report generator for product-radar.

Reads discovery JSON, radar channel data, and optionally Bitable status
to produce a formatted markdown summary.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / "data"
DISCOVERY_DIR = DATA_DIR / "discovery"
CHANNELS_DIR = DATA_DIR / "channels"


def _load_json(path):
    """Safely load a JSON file, return None on failure."""
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def _get_discoveries_for_date(target_date=None):
    """Load discovery data for a specific date (default: today)."""
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    path = DISCOVERY_DIR / f"{target_date}.json"
    return _load_json(path)


def _get_latest_radar():
    """Load the most recent radar channel data (by mtime, not filename).

    Filename ordering is unreliable: legacy files like ``20260720_140412.json``
    sort after ``2026-07-31_1400.json`` lexicographically, so alphabetical
    ordering could pick a weeks-old scan as "latest".
    """
    files = [f for f in CHANNELS_DIR.glob("*.json")
             if "-trends" not in f.name and "-rejected" not in f.name and f.name != "bsr_data.json"]
    if not files:
        return None
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return _load_json(latest)


def _get_discoveries_this_week():
    """Load all discovery files from this week (Mon-Sun)."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    discoveries = []
    for i in range(7):
        day = monday + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        path = DISCOVERY_DIR / f"{day_str}.json"
        if path.exists():
            data = _load_json(path)
            if data and data.get("insights"):
                discoveries.append(data)
    return discoveries


def _count_pipeline_stats():
    """Count discovery pipeline: total → verified → ordered → listed.

    Since we don't have Bitable access in offline mode, count from local data.
    Returns dict with counts and keyword lists.
    """
    total_keywords = set()
    all_discoveries = []

    for f in sorted(DISCOVERY_DIR.glob("*.json")):
        data = _load_json(f)
        if not data:
            continue
        for ins in data.get("insights", []):
            kw = ins.get("keyword", "")
            if kw:
                total_keywords.add(kw)
                all_discoveries.append(ins)

    return {
        "total_discovered": len(total_keywords),
        "all_discoveries": all_discoveries,
    }


def _get_radar_highlights(radar_data, top_n=5):
    """Extract top-scored categories/products from radar data."""
    if not radar_data:
        return []

    # Current format: dict with 'products' key containing passed products
    if isinstance(radar_data, dict):
        products = radar_data.get("products", [])
        if products:
            # Sort by score descending
            sorted_products = sorted(products, key=lambda x: x.get("score", 0), reverse=True)
            highlights = []
            for p in sorted_products[:top_n]:
                name = p.get("name", "")[:50]
                price = p.get("price", 0)
                reviews = p.get("reviews", 0)
                score = p.get("score", 0)
                margin = p.get("profit_margin", 0)
                # sources entries are str in current format but were dicts
                # ({'type','source','keyword'}) in legacy scans — normalize both.
                raw_sources = p.get("sources", [])[:3]
                source_names = [s if isinstance(s, str) else s.get("source", "") for s in raw_sources]
                sources = ", ".join(n for n in source_names if n)
                ocean = "🌊蓝海" if reviews < 20 else "🟢低竞争" if reviews <= 50 else "🟡中等"
                highlights.append({
                    "category": name,
                    "trend_score": f"分数{score}",
                    "demand_label": f"£{price:.2f} | {reviews}评论 {ocean} | 利润率{margin*100:.0f}%",
                    "demand_level": sources,
                })
            return highlights
        
        # Fallback: old format with trend_categories
        stats = radar_data.get("stats", {})
        categories = stats.get("trend_categories", {})
        supply_demand = stats.get("supply_demand", {})
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        highlights = []
        for cat, score in sorted_cats[:top_n]:
            sd = supply_demand.get(cat, {})
            highlights.append({
                "category": cat,
                "trend_score": score,
                "demand_label": sd.get("label", ""),
                "demand_level": sd.get("level", ""),
            })
        return highlights

    return []


def generate_daily_report(target_date=None):
    """Generate a daily selection report in markdown format.

    Args:
        target_date: Date string YYYY-MM-DD (default: today)

    Returns:
        Formatted markdown string
    """
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    report_date = datetime.strptime(target_date, "%Y-%m-%d")
    lines = []

    # ── Header ──
    lines.append(f"# 📦 选品日报 | {target_date}")
    lines.append("")

    # ── New discoveries today ──
    today_data = _get_discoveries_for_date(target_date)
    insights = today_data.get("insights", []) if today_data else []

    lines.append("## 🔍 今日新发现")
    lines.append("")
    if insights:
        lines.append(f"共发现 **{len(insights)}** 个选品关键词：")
        lines.append("")
        for i, ins in enumerate(insights, 1):
            kw = ins.get("keyword", "")
            kw_cn = ins.get("keyword_cn", "")
            score = ins.get("trend_score", 0)
            direction = ins.get("trend_direction", "")
            direction_emoji = {"rising": "📈", "stable": "➡️", "falling": "📉"}.get(direction, "")
            lines.append(f"{i}. **{kw}**（{kw_cn}）— 评分 {score} {direction_emoji}")
            reason = ins.get("reason", "")
            if reason:
                lines.append(f"   > {reason[:150]}{'...' if len(reason) > 150 else ''}")
            lines.append("")
    else:
        lines.append("今日暂无新发现。")
        lines.append("")

    # ── Radar highlights ──
    radar_data = _get_latest_radar()
    highlights = _get_radar_highlights(radar_data)

    lines.append("## 📡 雷达热点")
    lines.append("")
    if highlights and isinstance(radar_data, dict):
        # Count new vs repeat
        radar_products = radar_data.get("products", [])
        new_count = sum(1 for p in radar_products if p.get("is_new") is True)
        repeat_count = sum(1 for p in radar_products if p.get("is_new") is False)
        total_count = len(radar_products)

        scan_ts = radar_data.get("scan_ts", "")
        lines.append(f"最新扫描：{scan_ts}")
        lines.append(f"扫描 {radar_data.get('stats', {}).get('total_scanned', '?')} 个 → **{total_count} 个通过筛选**（🆕 {new_count} 新品 / ♻️ {repeat_count} 重复）")
        lines.append("")
        for h in highlights:
            lines.append(f"- **{h['category']}** — 趋势分 {h['trend_score']} {h['demand_label']}")
        lines.append("")
    else:
        lines.append("暂无雷达数据。")
        lines.append("")

    # ── Week-to-date progress ──
    week_data = _get_discoveries_this_week()
    week_keywords = set()
    week_insights = []
    for wd in week_data:
        for ins in wd.get("insights", []):
            kw = ins.get("keyword", "")
            if kw and kw not in week_keywords:
                week_keywords.add(kw)
                week_insights.append(ins)

    lines.append("## 📊 本周进度 (WTD)")
    lines.append("")
    lines.append(f"| 指标 | 数量 |")
    lines.append(f"|------|------|")
    lines.append(f"| 本周新发现 | {len(week_keywords)} |")

    # Top scored this week
    if week_insights:
        top = sorted(week_insights, key=lambda x: x.get("trend_score", 0), reverse=True)
        lines.append(f"| 本周最高分 | {top[0].get('trend_score', 0)} ({top[0].get('keyword', '')}) |")

        # Direction breakdown
        directions = Counter(ins.get("trend_direction", "") for ins in week_insights)
        rising = directions.get("rising", 0)
        lines.append(f"| 上升趋势 | {rising} |")
    lines.append("")

    # ── Pipeline metrics (all-time from local data) ──
    pipeline = _count_pipeline_stats()

    lines.append("## 🔄 选品漏斗 (全量)")
    lines.append("")
    lines.append("```")
    lines.append(f"  已发现 → 待验证 → 已验证 → 已下单 → 已上架")
    lines.append(f"    {pipeline['total_discovered']:>4}      -       -       -       -")
    lines.append("```")
    lines.append("")
    lines.append("*注：验证/下单/上架数据来自飞书多维表格，需配置 BITABLE_APP_TOKEN 后自动同步。*")
    lines.append("")

    # ── Trend forecast ──
    if today_data and today_data.get("trend_forecast"):
        lines.append("## 🔮 趋势预测")
        lines.append("")
        lines.append(today_data["trend_forecast"])
        lines.append("")

    # ── Bitable link ──
    lines.append("---")
    lines.append("📋 [飞书多维表格](https://feishu.cn) — 团队协作选品追踪")
    lines.append("🔗 [选品平台](https://Baodan168.github.io/product-radar/platform.html)")

    return "\n".join(lines)


def main():
    """CLI: python3 selection_report.py [YYYY-MM-DD]"""
    target = sys.argv[1] if len(sys.argv) > 1 else None
    report = generate_daily_report(target)
    print(report)


if __name__ == "__main__":
    main()
