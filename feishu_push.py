#!/usr/bin/env python3
"""选品雷达 - 飞书推送
读取雷达扫描JSON，生成摘要卡片+飞书文档，推送到工作群。
用法: python3 radar_feishu_push.py [json_path]
"""
import json, sys, os, glob
from pathlib import Path

# 复用 selection_feishu.py 的基础设施
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
from selection_feishu import get_token, create_doc, push_post, push_link

CHAT_ID = "oc_1e2556e71cd8f4d5bec6f351d168e9ea"
RADAR_DIR = Path(__file__).parent

def find_latest_json():
    """找到最新的扫描JSON（非rejected、非trends）"""
    channel_dir = RADAR_DIR / "data" / "channels"
    files = sorted(channel_dir.glob("*.json"))
    latest = [f for f in files if "-rejected" not in f.name and "-trends" not in f.name]
    if not latest:
        print("❌ 无扫描数据")
        sys.exit(1)
    return latest[-1]

def generate_report_md(data, date_str):
    """生成完整报告markdown"""
    products = data.get("products", [])
    stats = data.get("stats", {})
    divergences = stats.get("divergences", {})
    supply_demand = stats.get("supply_demand", {})
    
    lines = []
    lines.append(f"# 🔍 选品雷达 | {date_str}")
    lines.append("")
    lines.append(f"扫描 **{stats.get('total_scanned', 0)}** 个产品 → **{len(products)}** 个通过筛选")
    lines.append(f"数据来源：{', '.join(stats.get('channels', {}).keys())}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 产品列表
    lines.append("## 🏆 推荐产品")
    lines.append("")
    for i, p in enumerate(products, 1):
        margin_pct = f"{p['profit_margin']*100:.1f}%" if p.get('profit_margin') else '?'
        score = p.get('score', 0)
        stars = '⭐' * min(5, max(1, round(score / 20)))
        url = p.get('amazon_url', '')
        asin = p.get('asin', '')
        
        lines.append(f"### {i}. {p['name'][:80]}")
        lines.append(f"- **价格**：£{p.get('price', '?')} | **利润率**：{margin_pct} | **评分**：{score} {stars}")
        lines.append(f"- **Review**：{p.get('review_info', '?')} | **类目**：{p.get('category', '?')} | **来源**：{p.get('channel_name', '?')}")
        if url:
            lines.append(f"- **Amazon**：[查看商品]({url})")
        lines.append("")
    
    # 趋势变化
    lines.append("---")
    lines.append("")
    lines.append("## 📈 类目趋势变化")
    lines.append("")
    
    rising = [(k, v) for k, v in divergences.items() if v.get('direction') == 'rising']
    falling = [(k, v) for k, v in divergences.items() if v.get('direction') == 'falling']
    
    if rising:
        lines.append("**🔥 上升中：**")
        for k, v in rising:
            lines.append(f"- {k}: +{v['heat_change_pct']:.0f}% ({v['previous_heat']}→{v['current_heat']})")
        lines.append("")
    if falling:
        lines.append("**📉 下降中：**")
        for k, v in falling:
            lines.append(f"- {k}: {v['heat_change_pct']:.0f}% ({v['previous_heat']}→{v['current_heat']})")
        lines.append("")
    
    # 供需分析
    if supply_demand:
        lines.append("## 🌊 供需蓝海")
        lines.append("")
        blue_ocean = [(k, v) for k, v in supply_demand.items() if v.get('level') in ('deep_blue', 'blue')]
        for k, v in blue_ocean[:5]:
            lines.append(f"- **{k}**: {v['label']} (需求{v['demand']}/100)")
        lines.append("")
    
    return "\n".join(lines)

def generate_summary_json(data, date_str):
    """生成飞书摘要卡片JSON"""
    products = data.get("products", [])
    stats = data.get("stats", {})
    divergences = stats.get("divergences", {})
    
    total = stats.get('total_scanned', 0)
    passed = len(products)
    margins = [p['profit_margin']*100 for p in products if p.get('profit_margin')]
    min_m = f"{min(margins):.0f}%" if margins else "?"
    max_m = f"{max(margins):.0f}%" if margins else "?"
    
    content_blocks = []
    content_blocks.append([{"tag": "text", "text": f"扫描{total}个 → {passed}个通过 | 利润率{min_m}-{max_m}"}])
    content_blocks.append([{"tag": "text", "text": ""}])
    
    # Top 5 产品
    for i, p in enumerate(products[:5], 1):
        margin = f"{p['profit_margin']*100:.0f}%" if p.get('profit_margin') else '?'
        content_blocks.append([{"tag": "text", "text": f"① {p['name'][:40]} — £{p.get('price','?')} | 利润率{margin}".replace("①", f"{'①②③④⑤'[i-1]}") }])
        if p.get('amazon_url'):
            content_blocks.append([{"tag": "a", "text": "查看商品", "href": p['amazon_url']}])
    
    content_blocks.append([{"tag": "text", "text": ""}])
    
    # 趋势一句话
    rising = [k for k, v in divergences.items() if v.get('direction') == 'rising']
    if rising:
        content_blocks.append([{"tag": "text", "text": f"🔥 上升品类：{', '.join(rising[:3])}"}])
    
    return {
        "title": f"🔍 选品雷达 | {date_str}",
        "content_blocks": content_blocks
    }

def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else str(find_latest_json())
    print(f"📄 数据文件: {json_path}")
    
    data = json.load(open(json_path))
    date_str = data.get("scan_date", "unknown")
    products = data.get("products", [])
    
    if not products:
        print("⚠️ 无通过筛选的产品，跳过推送")
        return
    
    # 1. 生成报告 → 飞书文档
    report_md = generate_report_md(data, date_str)
    report_path = "/tmp/radar_report.md"
    with open(report_path, "w") as f:
        f.write(report_md)
    
    doc_url = create_doc(f"选品雷达 | {date_str}", report_path)
    
    # 2. 推送摘要卡片
    summary = generate_summary_json(data, date_str)
    summary_path = "/tmp/radar_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, ensure_ascii=False)
    
    push_post(summary_path)
    
    # 3. 推送文档链接
    if doc_url:
        push_link(doc_url)
    
    # 4. 保存去重文件
    dedup_path = os.path.expanduser("~/.hermes/cron/output/selection_last_recommendations.txt")
    os.makedirs(os.path.dirname(dedup_path), exist_ok=True)
    with open(dedup_path, "w") as f:
        for p in products:
            f.write(f"{p.get('name', '')[:50]}\n")
    
    print(f"\n✅ 推送完成: {len(products)}个产品 → 飞书文档+摘要卡片+链接")

if __name__ == "__main__":
    main()
