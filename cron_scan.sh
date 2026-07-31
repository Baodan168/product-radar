#!/bin/bash
set -a; source /home/lee/.hermes/.env; set +a
# Product Radar Daily Scan - Cron wrapper
# Credentials read from .env (SCRAPER_API_KEY, GITHUB_TOKEN)
# Runs scan + BSR enrichment + platform generation + deploy
set -e
cd "$(dirname "$0")"

# Step 0: 同步代码到 GitHub 最新（安全方式，保留本地产物）
git fetch origin
git stash push -m "auto-scan-pre-sync" 2>/dev/null || true
git pull --rebase --autostash origin main 2>/dev/null || git merge --ff-only origin/main 2>/dev/null || true

# All detail goes to log file; cron only sees the one-line result
LOG="$PWD/logs/cron_$(date '+%Y%m%d_%H%M%S').log"
mkdir -p "$PWD/logs"
find "$PWD/logs" -name "cron_*.log" -mtime +7 -delete 2>/dev/null

{
echo "🔍 选品雷达自动扫描 | $(date '+%Y-%m-%d %H:%M')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Run radar scan (timeout: 20 min — 含 [7a] 详情页尺寸验证, 78产品约需4-7分钟)
echo ""
echo "📡 Step 1: 雷达扫描..."
timeout 1200 python3 -u run_scan_v2.py 2>&1 || { echo "❌ 扫描超时或失败"; exit 1; }

# Get latest data file
LATEST=$(ls -t data/channels/*.json 2>/dev/null | grep -v rejected | grep -v trends | grep -v bsr_data | head -1)
if [ -z "$LATEST" ]; then
    echo "❌ 扫描失败：无数据文件"
    exit 1
fi

# Step 2: BSR enrichment using Playwright (timeout: 3 min)
echo ""
echo "📊 Step 2: BSR数据抓取..."
timeout 180 python3 bsr_scraper.py --enrich 2>&1 || echo "  ⚠️ BSR抓取失败（不影响主流程）"

# Step 3: Generate platform page
echo ""
echo "🔧 Step 3: 生成平台页面..."
timeout 60 python3 generate_platform.py 2>&1 || echo "  ⚠️ 平台生成失败"

# Step 3b: 重新生成门户页（重构后「今日概览」dashboard 是服务端渲染的，
# 必须跑 generate_portal.py 才能刷新数据，否则战情/补货告警卡显示旧快照）
echo ""
echo "🔧 Step 3b: 刷新门户 dashboard..."
timeout 60 python3 generate_portal.py 2>&1 || echo "  ⚠️ 门户页生成失败（dashboard 可能显示旧数据）"

# Extract summary
PRODUCTS=$(python3 -c "import json; d=json.load(open('$LATEST')); print(len(d.get('products',[])))")
SCANNED=$(python3 -c "import json; d=json.load(open('$LATEST')); print(d.get('stats',{}).get('total_scanned',0))")
DATE=$(python3 -c "import json; d=json.load(open('$LATEST')); print(d.get('scan_date',''))")
TIME=$(python3 -c "import json; d=json.load(open('$LATEST')); print(d.get('scan_time',''))")

# New vs repeat breakdown
NEW=$(python3 -c "
import json
d=json.load(open('$LATEST'))
prods = d.get('products',[])
new_count = sum(1 for p in prods if p.get('is_new')==True)
repeat_count = sum(1 for p in prods if p.get('is_new')==False)
print(f'{new_count},{repeat_count}')
")
NEW_COUNT="${NEW%,*}"
REPEAT_COUNT="${NEW#*,}"

echo ""
echo "📊 扫描结果：${SCANNED}个产品 → ${PRODUCTS}个通过筛选"
if [ "$REPEAT_COUNT" -gt 0 ]; then
    echo "   ├ 🆕 新品：${NEW_COUNT}个"
    echo "   └ ♻️ 重复（已有）：${REPEAT_COUNT}个"
fi
echo "📅 扫描时间：${DATE} ${TIME}"

# Top 3 products with BSR
echo ""
echo "🏆 Top 3 推荐："
python3 -c "
import json
d = json.load(open('$LATEST'))
for i, p in enumerate(d.get('products',[])[:3], 1):
    sig = p.get('signal_label', '?')
    sd = p.get('sd_label', '')
    bsr = p.get('bsr_rank', 'N/A')
    sub = p.get('bsr_sub_category', '')
    daily = p.get('estimated_daily_sales', 'N/A')
    print(f'  {i}. {p[\"name\"][:50]}')
    print(f'     £{p[\"price\"]} | 利润{p[\"profit_margin\"]*100:.0f}% | BSR#{bsr} ({sub}) | 日销≈{daily}')
    print(f'     {sig} {sd}')
"

# Step 4: Deploy to GitHub
echo ""
echo "📦 Step 4: 部署到 GitHub Pages..."
# timeout 180: output/analysis 全量推送后 API 调用约 30 批，60s 不够会误判失败走 fallback
timeout 180 python3 github_api_push.py "auto-scan $(date -u '+%Y-%m-%d %H:%M')" 2>&1 || {
    # Fallback to git push (with longer timeout for 1.3MB platform.html)
    timeout 60 git add data/ output/ status.json -f 2>/dev/null
    git diff --cached --quiet && echo "  无变更" && exit 0
    timeout 20 git commit -m "auto-scan $(date -u '+%Y-%m-%d %H:%M')" 2>/dev/null
    timeout 60 git pull --rebase 2>/dev/null || true
    timeout 120 git push origin main 2>&1
} || {
    echo "❌ 部署到 GitHub 失败"
    exit 1
}

echo ""
echo "✅ 部署完成：https://liyuhong168.github.io/product-radar/platform.html"

} > "$LOG" 2>&1 || {
    # On failure, output error for cron alert
    echo "❌ 选品雷达扫描失败 | $(date '+%Y-%m-%d %H:%M')"
    tail -5 "$LOG"
    exit 1
}

# On success, one-line summary for cron delivery
# Re-extract counts (outside the subshell where main logic ran)
LATEST=$(ls -t data/channels/*.json 2>/dev/null | grep -v rejected | grep -v trends | grep -v bsr_data | head -1)
PRODUCTS="?"
NEW_COUNT="?"
REPEAT_COUNT="?"
if [ -n "$LATEST" ]; then
    IFS=',' read -r NEW_COUNT REPEAT_COUNT PRODUCTS <<< $(python3 -c "
import json
d=json.load(open('$LATEST'))
prods = d.get('products',[])
new_c = sum(1 for p in prods if p.get('is_new')==True)
rep_c = sum(1 for p in prods if p.get('is_new')==False)
print(f'{new_c},{rep_c},{len(prods)}')
")
fi
if [ "$REPEAT_COUNT" -gt 0 ] 2>/dev/null; then
    echo "✅ 选品雷达扫描完成 | $(date '+%Y-%m-%d %H:%M') | ${PRODUCTS}个通过筛选（🆕${NEW_COUNT}新品 ♻️${REPEAT_COUNT}重复）→ 已部署GitHub"
else
    echo "✅ 选品雷达扫描完成 | $(date '+%Y-%m-%d %H:%M') | ${PRODUCTS}个新品通过筛选 → 已部署GitHub"
fi
