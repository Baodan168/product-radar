#!/bin/bash
set -a; source /home/lee/.hermes/.env; set +a
# Product Radar Daily Scan - Cron wrapper
# Credentials read from .env (SCRAPER_API_KEY, GITHUB_TOKEN)
# Runs scan + BSR enrichment + platform generation + deploy
set -e
cd "$(dirname "$0")"

# Step 0 前置：确认仓库处于可安全同步的状态。
#
# 这个脚本一直假定 checkout 在 main，但从不检查。2026-08-01 真出过事：
# 前一晚有人把仓库留在特性分支上，早上定时任务照跑，下面那句
# `git pull --rebase origin main` 于是把**那条特性分支**往 main 上重放，
# 在产物上撞了冲突，仓库卡在 rebase 进行中的半途状态。
# 那次没发布错产物（下面「同步失败即退出」挡住了），但根因在这儿：
# 挡住的是症状，这里才是病因。
GIT_DIR_PATH=$(git rev-parse --git-dir)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "❌ 仓库不在 main 上（当前：$BRANCH）| $(date '+%Y-%m-%d %H:%M')"
    echo "   本脚本会跑 git pull --rebase origin main —— 在别的分支上跑，"
    echo "   重放的是那条分支，撞冲突就会把仓库卡在半途。"
    echo "   本次跳过扫描，不发布。"
    echo "   处理：把该分支上的活提交或 stash 掉，git checkout main，再重跑。"
    exit 1
fi

# 上一次同步留下的半成品状态。带着它继续跑，生成的产物来自一个
# 「一半新一半旧」的工作区，而 cron 摘要看不出任何异常。
if [ -d "$GIT_DIR_PATH/rebase-merge" ] || [ -d "$GIT_DIR_PATH/rebase-apply" ] \
   || [ -f "$GIT_DIR_PATH/MERGE_HEAD" ] || [ -f "$GIT_DIR_PATH/CHERRY_PICK_HEAD" ]; then
    echo "❌ 仓库有未完成的 rebase/merge/cherry-pick | $(date '+%Y-%m-%d %H:%M')"
    echo "   工作区处于半合并状态，此时生成的产物来源说不清。"
    echo "   本次跳过扫描，不发布。"
    echo "   处理：git status 看清楚，然后 --continue 或 --abort 收尾后重跑。"
    exit 1
fi

# Step 0: 检查本地代码与 GitHub 远程是否一致（API 方式，不走 git/SSH 协议）
# 2026-08-03 修复：原 git fetch/pull 走 SSH，SSH key 失效导致 cron 在第一步就挂。
# 本机是唯一完整开发环境（16 处路径绑死本机），代码变更都在本地发生，
# 远程 main 只是发布载体（部署走 github_api_push.py，API 推送）。
# 因此用 api.github.com 对比版本 —— 与项目其他 cron 一致，零 SSH 依赖。
# 判断标准：本地 HEAD 是否在远程最近 100 个 commit 里。API 推送的产物 commit
# 会让远程领先本地（正常，不警告）；只有本地与远程分叉/被 force push 才警告。
LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_COMMITS=$(curl -s --max-time 20 -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/Baodan168/product-radar/commits?sha=main&per_page=100" 2>/dev/null \
  | python3 -c "import json,sys; print(' '.join(c['sha'] for c in json.load(sys.stdin)))" 2>/dev/null || echo "")
if [ -n "$REMOTE_COMMITS" ] && ! echo "$REMOTE_COMMITS" | grep -qw "$LOCAL_SHA"; then
    echo "⚠️ 警告: 本地 HEAD ($(echo $LOCAL_SHA | cut -c1-7)) 不在远程 main 历史中，可能与远程分叉" >&2
    echo "   本机为唯一开发环境，继续使用本地代码。如需同步请手动 git pull（本机需配好 SSH key）。" >&2
fi
# 冲突检测：rebase 后 autostash 未能自动恢复时报警（改动保留在 refs/autostash，不会静默丢失）
if git rev-parse --verify refs/autostash >/dev/null 2>&1; then
    echo "⚠️ 警告: 扫描前未提交改动未自动恢复(autostash冲突), 请运行 git stash pop 处理" >&2
fi

# All detail goes to log file; cron only sees the one-line result
LOG="$PWD/logs/cron_$(date '+%Y%m%d_%H%M%S').log"
mkdir -p "$PWD/logs"
find "$PWD/logs" -name "cron_*.log" -mtime +7 -delete 2>/dev/null

# ── 运行状态（机器可读）──
# 判定「这次跑成功没有」不要去 grep 日志里的 ❌：详情页验证给每个被淘汰的
# 产品也打 ❌，一次几十条，那是过滤器在干正事。emoji 同时当装饰和状态信号，
# 谁都会踩。真相写在这里，preflight 和任何监控都读这个文件。
STATUS_FILE="$PWD/logs/last_run.json"
STEP_FILE=$(mktemp)
WARN_FILE=$(mktemp)
STARTED_AT=$(date '+%Y-%m-%dT%H:%M:%S%z')
trap 'rm -f "$STEP_FILE" "$WARN_FILE"' EXIT

step() { echo "$1" > "$STEP_FILE"; }
warn() { echo "$1" >> "$WARN_FILE"; }

write_status() {  # write_status <ok:true|false>
    python3 - "$1" "$STATUS_FILE" "$LOG" "$STARTED_AT" "$STEP_FILE" "$WARN_FILE" <<'PY'
import json, sys, datetime, pathlib
ok, out, log, started, step_f, warn_f = sys.argv[1:7]
def read(p, default=''):
    try:
        return pathlib.Path(p).read_text(encoding='utf-8').strip()
    except Exception:
        return default
warns = [w for w in read(warn_f).splitlines() if w]
step = read(step_f) or 'unknown'
pathlib.Path(out).write_text(json.dumps({
    'ok': ok == 'true',
    'started_at': started,
    'finished_at': datetime.datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z'),
    'failed_step': None if ok == 'true' else step,
    'last_step': step,
    'warnings': warns,          # 降级但不致命的（BSR 抓取失败等）
    'log': log,
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY
}

{
echo "🔍 选品雷达自动扫描 | $(date '+%Y-%m-%d %H:%M')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Run radar scan (timeout: 10 min — 含 [7a] 详情页尺寸验证, 78产品约需4-7分钟)
# ⚠️ cron 外层 900s 硬超时（no_agent 系统限制），全步骤 timeout 总和必须 ≤900s
# 预算: scan 600 + bsr 30 + platform 20 + portal 20 + deploy 180 = 850s（留 50s 余量）
# 2026-08-13 优化: bsr 45→30, platform/portal 30→20（均含 fallback 不致命）；
#   部署已改为只推 hash 变更文件（138→~40 个），实际 deploy 通常 ~50s，
#   850s 预算给扫描波动留出呼吸空间（上次 17:10 扫描波动吃掉部署配额致 900s 超时）。
echo ""
step "scan"
echo "📡 Step 1: 雷达扫描..."
timeout 600 python3 -u run_scan_v2.py 2>&1 || { echo "❌ 扫描超时或失败"; exit 1; }

# Get latest data file
LATEST=$(ls -t data/channels/*.json 2>/dev/null | grep -v rejected | grep -v trends | grep -v bsr_data | head -1)
if [ -z "$LATEST" ]; then
    echo "❌ 扫描失败：无数据文件"
    exit 1
fi

# Step 2: BSR enrichment using Playwright (timeout: 30s, 失败不影响主流程)
echo ""
step "bsr"
echo "📊 Step 2: BSR数据抓取..."
timeout 30 python3 bsr_scraper.py --enrich 2>&1 || { echo "  ⚠️ BSR抓取失败（不影响主流程）"; warn "BSR抓取失败"; }

# Step 3: Generate platform page
echo ""
step "generate_platform"
echo "🔧 Step 3: 生成平台页面..."
timeout 20 python3 generate_platform.py 2>&1 || { echo "  ⚠️ 平台生成失败"; warn "平台页生成失败"; }

# Step 3b: 重新生成门户页（重构后「今日概览」dashboard 是服务端渲染的，
# 必须跑 generate_portal.py 才能刷新数据，否则战情/补货告警卡显示旧快照）
echo ""
step "generate_portal"
echo "🔧 Step 3b: 刷新门户 dashboard..."
timeout 20 python3 generate_portal.py 2>&1 || { echo "  ⚠️ 门户页生成失败（dashboard 可能显示旧数据）"; warn "门户页生成失败"; }

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
step "deploy"
echo "📦 Step 4: 部署到 GitHub Pages..."
# timeout 180: output/analysis 全量推送后 API 调用约 30 批，60s 不够会误判失败走 fallback
# ⚠️ 2026-08-03: 移除 SSH git push fallback（SSH key 已废弃，fallback 永远失败且白耗 120s）。
#    github_api_push.py 已内置 3 次重试（GFW 间歇断连 api.github.com 443 → RemoteDisconnected 可过）
if timeout 180 python3 github_api_push.py "auto-scan $(date -u '+%Y-%m-%d %H:%M')" 2>&1; then
    :
else
    echo "  ⚠️ API 推送失败，重试一次..."
    if timeout 180 python3 github_api_push.py "auto-scan $(date -u '+%Y-%m-%d %H:%M')" 2>&1; then
        :
    else
        echo "❌ 部署到 GitHub 失败（API 推送两次均失败）"
        exit 1
    fi
fi

echo ""
echo "✅ 部署完成：https://Baodan168.github.io/product-radar/platform.html"

} > "$LOG" 2>&1 || {
    # On failure, output error for cron alert
    write_status false
    echo "❌ 选品雷达扫描失败 | $(date '+%Y-%m-%d %H:%M')"
    tail -5 "$LOG"
    exit 1
}
write_status true

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
# [7a] 详情页拦截统计（重量/尺寸超标），拼到摘要行尾
DETAIL_REJ=""
if [ -n "$LATEST" ]; then
    DETAIL_REJ=$(python3 -c "
import json
try:
    d=json.load(open('$LATEST'))
    s=d.get('stats',{}).get('detail_reject',{})
    if s:
        print(' | [7a]拦截 ' + ' '.join(f'{v}个{k}' for k,v in s.items()))
except Exception:
    pass
" 2>/dev/null)
fi
if [ "$REPEAT_COUNT" -gt 0 ] 2>/dev/null; then
    echo "✅ 选品雷达扫描完成 | $(date '+%Y-%m-%d %H:%M') | ${PRODUCTS}个通过筛选（🆕${NEW_COUNT}新品 ♻️${REPEAT_COUNT}重复）→ 已部署GitHub${DETAIL_REJ}"
else
    echo "✅ 选品雷达扫描完成 | $(date '+%Y-%m-%d %H:%M') | ${PRODUCTS}个新品通过筛选 → 已部署GitHub${DETAIL_REJ}"
fi
