#!/usr/bin/env python3
"""Generate static HTML page - Apple-style light theme."""
import json, os, sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
CONFIG = json.loads((BASE / "config.json").read_text())


def load_latest():
    snap_dir = BASE / CONFIG["output"]["snapshot_dir"]
    hist_dir = BASE / CONFIG["output"]["history_dir"]
    snapshots = sorted(snap_dir.glob("*.json"))
    histories = sorted(hist_dir.glob("*.json"))
    today = datetime.now().strftime("%Y-%m-%d")
    current = json.loads(snapshots[-1].read_text()) if snapshots else []
    previous = json.loads(snapshots[-2].read_text()) if len(snapshots) >= 2 else []
    all_valid = json.loads(histories[-1].read_text()) if histories else []
    return current, previous, all_valid, snapshots[-1].stem if snapshots else today


def build_html(current, previous, all_valid, scan_date):
    total_scanned = len(all_valid)
    passed = len(current)
    sources = {}
    for p in all_valid:
        for s in p.get("sources", []):
            sources[s] = sources.get(s, 0) + 1
    for p in current:
        for s in p.get("sources", []):
            sources[s] = sources.get(s, 0) + 1

    prev_names = {p.get("name", "")[:40] for p in previous}
    new_items = [p for p in current if p.get("name", "")[:40] not in prev_names]

    # Category color map
    cat_colors = {
        "Sports": "#007AFF",
        "Automotive": "#FF9500",
        "Pet Supplies": "#34C759",
        "Kitchen": "#FF2D55",
        "DIY & Tools": "#AF52DE",
        "TikTok": "#5856D6",
    }

    def get_cat_color(name):
        for key, color in cat_colors.items():
            if key.lower() in name.lower():
                return color
        return "#8E8E93"

    # Source filter buttons
    filter_buttons = '<button class="fbtn active" onclick="filterBySrc(\'all\')">All</button>\n'
    for src in sorted(sources.keys()):
        c = get_cat_color(src)
        filter_buttons += f'<button class="fbtn" style="--accent:{c}" onclick="filterBySrc(\'{src}\')">{src}</button>\n'

    # Product cards
    cards_html = ""
    for i, p in enumerate(current, 1):
        name = p.get("name", "Unknown")[:80].replace('"', '&quot;')
        asin = p.get("asin", "")
        price = p.get("price", 0)
        margin = p.get("profit_margin", 0)
        net = p.get("net_profit", 0)
        score = p.get("score", 0)
        review_info = p.get("review_info", "Pending")
        sources_list = p.get("sources", [])
        rank = p.get("rank", "")
        bd = p.get("cost_breakdown", {})
        rating = p.get("rating", 0)
        is_new = p.get("name", "")[:40] not in prev_names

        cat_src = sources_list[0] if sources_list else ""
        accent = get_cat_color(cat_src)

        asin_link = f'<a href="https://www.amazon.co.uk/dp/{asin}" target="_blank" class="product-name">{name}</a>' if asin else f'<span class="product-name">{name}</span>'
        stars = min(5, max(1, (score - 40) // 10 + 1))
        star_html = '<svg width="14" height="14" viewBox="0 0 20 20" fill="' + accent + '"><path d="M10 1l2.39 4.84 5.34.78-3.87 3.77.91 5.33L10 13.27l-4.77 2.51.91-5.33L2.27 6.68l5.34-.78L10 1z"/></svg>' * stars

        new_badge = '<span class="badge new-badge">NEW</span>' if is_new else ""
        rank_text = f'<span class="rank-tag" style="color:{accent}">BSR #{rank}</span>' if rank else ""

        margin_pct = margin * 100
        if margin_pct >= 30:
            margin_color = "#34C759"
        elif margin_pct >= 20:
            margin_color = "#FF9500"
        else:
            margin_color = "#FF3B30"

        # Review display
        review_text = review_info if review_info and review_info != "Pending" else "No reviews yet"

        cards_html += f'''
      <div class="card" data-source="{' '.join(sources_list)}" data-name="{name.lower()}" data-asin="{asin.lower()}">
        <div class="card-top">
          <div class="card-rank" style="background:{accent}">#{i}</div>
          {new_badge}
        </div>
        <div class="card-body">
          {asin_link}
          <div class="card-subtitle">{review_text} {f"· {rating}★" if rating else ""}</div>
          <div class="card-tags">
            <span class="tag tag-price">\u00a3{price:.2f}</span>
            <span class="tag tag-margin" style="background:{margin_color}15;color:{margin_color}">{margin_pct:.1f}% margin</span>
            {rank_text}
          </div>
          <div class="card-metrics">
            <div class="metric">
              <span class="metric-label">Net Profit</span>
              <span class="metric-value">\u00a3{net:.2f}</span>
            </div>
            <div class="metric">
              <span class="metric-label">VAT</span>
              <span class="metric-value">\u00a3{bd.get("vat",0):.2f}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Commission</span>
              <span class="metric-value">\u00a3{bd.get("commission",0):.2f}</span>
            </div>
            <div class="metric">
              <span class="metric-label">FBA</span>
              <span class="metric-value">\u00a3{bd.get("fba",0):.2f}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Sourcing</span>
              <span class="metric-value">\u00a3{bd.get("sourcing",0):.2f}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Score</span>
              <span class="metric-value">{score}</span>
            </div>
          </div>
          <div class="margin-bar"><div class="margin-fill" style="width:{min(margin_pct/40*100,100):.0f}%;background:{margin_color}"></div></div>
        </div>
        <div class="card-footer">
          <span class="source-dot" style="background:{accent}"></span>
          <span class="source-label">{cat_src}</span>
          {f'<span class="star-row">{star_html}</span>' if stars else ""}
        </div>
      </div>'''

    # Source pills
    source_pills = ""
    for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
        c = get_cat_color(src)
        source_pills += f'<span class="source-pill" style="--pill-color:{c}"><span class="pill-dot" style="background:{c}"></span>{src} <b>{cnt}</b></span>\n'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Product Radar \u00b7 \u9009\u54c1\u96f7\u8fbe</title>
<link rel='stylesheet' href='../shared/oa-theme.css'>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f7;color:#1d1d1f;-webkit-font-smoothing:antialiased}}
.page{{max-width:1400px;margin:0 auto;padding:0 24px 40px}}
.source-pills{{display:flex;gap:8px;flex-wrap:wrap}}
.source-pill{{display:inline-flex;align-items:center;gap:5px;background:#fff;border-radius:20px;padding:6px 14px;font-size:.82em;font-weight:500;color:#1d1d1f;box-shadow:0 1px 2px rgba(0,0,0,.05)}}
.source-pill b{{color:var(--pill-color,#007AFF)}}
.pill-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}

/* Filter + Search */
.toolbar{{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center}}
.search{{flex:1;min-width:200px;padding:10px 16px;background:#fff;border:1px solid #d2d2d7;border-radius:12px;font-size:.9em;color:#1d1d1f;outline:none;transition:border .2s}}
.search:focus{{border-color:#007AFF;box-shadow:0 0 0 3px rgba(0,122,255,.12)}}
.search::placeholder{{color:#aeaeb2}}
.fbtn{{background:#fff;color:#1d1d1f;border:1px solid #d2d2d7;padding:7px 16px;border-radius:20px;cursor:pointer;font-size:.82em;font-weight:500;transition:all .2s;white-space:nowrap}}
.fbtn:hover{{border-color:#86868b}}
.fbtn.active{{background:#1d1d1f;color:#fff;border-color:#1d1d1f}}

/* Product Grid */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}}
.card{{background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);transition:transform .2s,box-shadow .2s;position:relative}}
.card:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(0,0,0,.08),0 4px 10px rgba(0,0,0,.04)}}
.card.new{{border-left:3px solid #34C759}}
.card-top{{display:flex;align-items:center;justify-content:space-between;padding:12px 18px 0}}
.card-rank{{font-size:.72em;font-weight:700;color:#fff;padding:3px 10px;border-radius:10px;letter-spacing:.03em}}
.new-badge{{font-size:.68em;font-weight:600;color:#34C759;background:#34C75912;padding:2px 8px;border-radius:8px}}
.card-body{{padding:10px 18px 14px}}
.product-name{{font-size:.95em;font-weight:600;color:#1d1d1f;text-decoration:none;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
a.product-name:hover{{color:#007AFF}}
.card-subtitle{{font-size:.78em;color:#86868b;margin-top:4px}}
.card-tags{{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}}
.tag{{display:inline-block;padding:3px 10px;border-radius:8px;font-size:.78em;font-weight:600}}
.tag-price{{background:#f5f5f7;color:#1d1d1f}}
.tag-margin{{border-radius:8px}}
.rank-tag{{font-size:.78em;font-weight:600}}
.card-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#f0f0f2;border-radius:10px;overflow:hidden;margin:10px 0}}
.metric{{background:#fafafa;padding:8px 10px;text-align:center}}
.metric-label{{display:block;font-size:.65em;color:#86868b;text-transform:uppercase;letter-spacing:.04em;font-weight:500}}
.metric-value{{display:block;font-size:.88em;font-weight:600;color:#1d1d1f;margin-top:1px}}
.margin-bar{{height:4px;background:#f0f0f2;border-radius:2px;overflow:hidden}}
.margin-fill{{height:100%;border-radius:2px;transition:width .6s ease}}
.card-footer{{display:flex;align-items:center;gap:6px;padding:10px 18px;border-top:1px solid #f5f5f7}}
.source-dot{{width:6px;height:6px;border-radius:50%;flex-shrink:0}}
.source-label{{font-size:.72em;color:#86868b;font-weight:500}}
.star-row{{margin-left:auto;display:flex;gap:1px}}

/* Footer */
.footer{{text-align:center;padding:48px 0 32px;color:#aeaeb2;font-size:.8em}}
.footer a{{color:#007AFF;text-decoration:none}}

@media(max-width:768px){{
  .page{{padding:0 16px 24px}}
  .oa-hero-title{{font-size:1.8em}}
  .oa-kpi-grid{{grid-template-columns:repeat(2,1fr)}}
  .grid{{grid-template-columns:1fr}}
  .toolbar{{flex-direction:column}}
  .search{{min-width:100%}}
  .card-metrics{{grid-template-columns:repeat(2,1fr)}}
}}
</style>
</head>
<body>
<div class="oa-hero">
  <div class="oa-hero-text">
    <span class="oa-eyebrow">Analysis Dashboard</span>
    <p class="oa-page-eyebrow">RESTOCK TRACKING</p>
    <h1 class="oa-page-title">📦 补货跟进</h1>
    <p class="oa-page-desc"><strong>{total_scanned}</strong> 个产品扫描 · <strong style="color:#FF9500">{passed}</strong> 个需补货 · 数据来源: 领星ERP + Amazon UK</p>
  </div>
</div>

<div class="oa-kpi-grid">
  <div class="oa-kpi">
    <div class="oa-kpi-label">Scanned</div>
    <div class="oa-kpi-value">{total_scanned}</div>
  </div>
  <div class="oa-kpi">
    <div class="oa-kpi-label">Passed</div>
    <div class="oa-kpi-value" style="color:var(--oa-green)">{passed}</div>
  </div>
  <div class="oa-kpi">
    <div class="oa-kpi-label">New</div>
    <div class="oa-kpi-value" style="color:var(--oa-orange)">{len(new_items)}</div>
  </div>
  <div class="oa-kpi">
    <div class="oa-kpi-label">Sources</div>
    <div class="oa-kpi-value" style="color:var(--oa-purple)">{len(sources)}</div>
  </div>
</div>

<div class="oa-section">
  <div class="oa-section-header">
    <h2 class="oa-section-title">Sources</h2>
  </div>
  <div class="oa-flex oa-flex-wrap oa-gap-sm">
{source_pills}
  </div>
</div>

<div class="page">
  <div class="toolbar">
    <input type="text" class="search" id="searchBox" placeholder="Search products, ASIN, sources\u2026" oninput="doFilter()">
    {filter_buttons}
  </div>

  <div class="grid" id="productGrid">
{cards_html}
  </div>
</div>

<div class="footer">
  Product Radar \u00b7 Built with <a href="https://github.com/Baodan168/ai-news-radar">Hermes Agent</a>
</div>

<script>
function doFilter(){{
  var q=document.getElementById('searchBox').value.toLowerCase();
  document.querySelectorAll('.card').forEach(function(c){{
    var n=c.dataset.name||'',a=c.dataset.asin||'',s=c.dataset.source||'';
    c.style.display=(n.indexOf(q)>=0||a.indexOf(q)>=0||s.indexOf(q)>=0)?'':'none';
  }});
}}
function filterBySrc(src){{
  document.querySelectorAll('.fbtn').forEach(function(b){{b.classList.remove('active');}});
  event.target.classList.add('active');
  document.querySelectorAll('.card').forEach(function(c){{
    c.style.display=(src==='all'||(c.dataset.source||'').indexOf(src)>=0)?'':'none';
  }});
}}
</script>
</body>
</html>'''
    return html


if __name__ == "__main__":
    current, previous, all_valid, scan_date = load_latest()
    html = build_html(current, previous, all_valid, scan_date)
    out_path = BASE / "output" / "index.html"
    out_path.write_text(html)
    print(f"HTML: {out_path} | {len(current)} products / {len(all_valid)} scanned")
