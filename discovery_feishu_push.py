#!/usr/bin/env python3
"""选品发现 - 飞书推送
读取discovery JSON，生成摘要卡片+飞书文档，推送到工作群。
用法: python3 discovery_feishu_push.py [json_path]
"""
import json, sys, os
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
from selection_feishu import get_token, create_doc, push_post, push_link

CHAT_ID = "oc_906e4db2810734d00495230b55f23711"
RADAR_DIR = Path(__file__).parent

def find_latest_discovery():
    discovery_dir = RADAR_DIR / "data" / "discovery"
    files = sorted(discovery_dir.glob("*.json"))
    if not files:
        print("❌ 无发现数据")
        sys.exit(1)
    return files[-1]

def generate_report_md(data, date_str):
    insights = data.get("insights", [])
    summary = data.get("summary", "")
    
    lines = []
    lines.append(f"# 🎯 选品发现 | {date_str}")
    lines.append("")
    lines.append(f"发现 **{len(insights)}** 个高潜力选品机会")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 摘要
    if summary:
        lines.append("## 📋 今日摘要")
        lines.append("")
        lines.append(summary[:500] + "..." if len(summary) > 500 else summary)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # 产品列表
    lines.append("## 🏆 推荐产品")
    lines.append("")
    for i, insight in enumerate(insights, 1):
        keyword_cn = insight.get('keyword_cn', '')
        trend_score = insight.get('trend_score', 0)
        final_score = insight.get('signal_scores', {}).get('final', 0)
        recommendation = insight.get('signal_scores', {}).get('recommendation', '')
        profit_window = insight.get('signal_scores', {}).get('profit_window', '')
        
        lines.append(f"### {i}. {keyword_cn}")
        lines.append(f"- **趋势评分**：{trend_score}/100 | **综合评分**：{final_score} | **建议**：{recommendation}")
        lines.append(f"- **利润窗口**：{profit_window}")
        lines.append("")
    
    return "\n".join(lines)

def generate_summary_json(data, date_str):
    insights = data.get("insights", [])
    
    content_blocks = []
    content_blocks.append([{"tag": "text", "text": f"发现 {len(insights)} 个选品机会 | 综合评分 68-72"}])
    content_blocks.append([{"tag": "text", "text": ""}])
    
    for i, insight in enumerate(insights[:3], 1):
        keyword_cn = insight.get('keyword_cn', '')
        final_score = insight.get('signal_scores', {}).get('final', 0)
        profit = insight.get('signal_scores', {}).get('profit_window', '')[:60]
        
        content_blocks.append([{"tag": "text", "text": f"① {keyword_cn[:35]} — 评分{final_score}"}])
        content_blocks.append([{"tag": "text", "text": f"   {profit}"}])
        content_blocks.append([{"tag": "text", "text": ""}])
    
    return {
        "title": f"🎯 选品发现 | {date_str}",
        "content_blocks": content_blocks
    }

def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else str(find_latest_discovery())
    print(f"📄 数据文件: {json_path}")
    
    data = json.load(open(json_path))
    date_str = data.get("scan_date", "unknown")
    insights = data.get("insights", [])
    
    if not insights:
        print("⚠️ 无推荐产品，跳过推送")
        return
    
    # 1. 生成报告 → 飞书文档
    report_md = generate_report_md(data, date_str)
    report_path = "/tmp/discovery_report.md"
    with open(report_path, "w") as f:
        f.write(report_md)
    
    doc_url = create_doc(f"选品发现 | {date_str}", report_path)
    
    # 2. 推送摘要卡片
    summary = generate_summary_json(data, date_str)
    summary_path = "/tmp/discovery_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, ensure_ascii=False)
    
    push_post(summary_path)
    
    # 3. 推送文档链接
    if doc_url:
        push_link(doc_url)
    
    print(f"\n✅ 推送完成: {len(insights)}个选品 → 飞书文档+摘要卡片+链接")
    
    # 4. 保存去重文件
    dedup_path = os.path.expanduser("~/.hermes/cron/output/discovery_last_recommendations.txt")
    os.makedirs(os.path.dirname(dedup_path), exist_ok=True)
    with open(dedup_path, "w") as f:
        for insight in insights:
            f.write(f"{insight.get('keyword_cn', '')}\n")

if __name__ == "__main__":
    main()
