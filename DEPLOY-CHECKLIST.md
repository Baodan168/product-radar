# 接下来做什么 —— 部署与后续代办

> 给明天回公司的自己。按阶段走，别跳。
> 分支：`claude/oa-portal-ui-upgrade-ts4zrf` → `main`
> 风险分析的依据在 [`PROPOSAL-agent-collab.md`](./PROPOSAL-agent-collab.md)，
> 交接清单在 [`HANDOFF.md`](./HANDOFF.md)。

---

## 先理解一件事：为什么不能让 09:10 的 cron 当第一次验证

`cron_scan.sh` 开头会 `git pull` 同步代码，所以**不会出现「hermes 用旧样子覆盖」**——
这一层是设计好的。Step 0 已经修过一轮（去掉了吞错误的 `2>/dev/null`，改 autostash 并在
恢复失败时报警），比以前可靠得多。

但兜底那句 `|| true` 还在：万一 `pull` 和 `merge --ff-only` 都没成，脚本会
**继续用旧代码生成并推上去**，而 cron 只给你一行摘要，看不出来。
所以：**选一个你能盯着的时间合并，然后手动跑一遍完整链路。**

---

# 阶段 0 · 体检（1 条命令，只读）

```bash
cd /home/lee/product-radar
git fetch origin
git checkout claude/oa-portal-ui-upgrade-ts4zrf   # preflight.py 只在这个分支上，main 没有
python3 tools/preflight.py --fetch
```

它把原来那张判断表做成了脚本：环境、git 状态、stash 积压、产物新鲜度、
脱敏门禁、162 项测试、补货管道有没有脱敏、上次 cron 成功没有 —— 一次跑完，
最后给一行结论。**退出码 0 = 可以往下走，1 = 有阻塞项。**

阻塞项会直接告诉你怎么修。其中两项最要紧：

| 阻塞项 | 为什么要紧 |
|---|---|
| `output/*.html` 比源文件旧 | 这就是「旧 markup + 新 CSS」混合体的成因 |
| `restock_pipeline.sh` 里没有 `desensitize_analysis.py` | 下个周一/四会让 `--check` 门禁**拦下整个部署**，而失败只在 Actions 里可见 |

> 这一步只读，不改任何东西。结论决定后面走哪条路。
> 有阻塞项就先修，修完重跑到绿再进阶段 1。

---

# 阶段 1 · 先看真机效果（可选，10 分钟，不合并）

想先在手机和电脑上看看真实效果再决定，可以**不合并**就部署一次：

**GitHub → Actions → Deploy Product Radar → Run workflow → 分支选 `claude/oa-portal-ui-upgrade-ts4zrf` → Run**

等 2–3 分钟（CDN 缓存 600s），打开 https://Baodan168.github.io/product-radar/

**两个代价，别当成正式发布：**
1. 那段时间线上就是新版本，团队如果正在用会看到变化
2. hermes 下次推 `main` 会触发 `update.yml` 重新部署 `main` 的内容，**自动把线上刷回旧版**——它会自己回滚

看完觉得可以，再走阶段 2。

---

# 阶段 2 · 正式合并（关键动作）

GitHub 上开 PR 合并，或者本地：

```bash
cd /home/lee/product-radar
git fetch origin
git checkout main && git pull origin main
git merge --no-ff origin/claude/oa-portal-ui-upgrade-ts4zrf
git push origin main
```

推上去会触发 `update.yml`：先跑 `desensitize_analysis.py --check` 门禁，过了才部署。

**去 Actions 页面确认那次 workflow 是绿的。** 如果红了，看是不是卡在 `--check`
——那说明 `output/analysis/` 里有未脱敏的文件，本地跑一次 `python3 desensitize_analysis.py` 再提交。

**CDN 缓存 600s，等 2–3 分钟再验证。**

---

# 阶段 3 · 本机跟进（合并后立刻做）

```bash
cd /home/lee/product-radar
git fetch origin && git status --short     # 确认干净
bash cron_scan.sh                          # 手动跑一次完整链路
ls -t logs/cron_*.log | head -1 | xargs tail -40
```

**看日志里这三处，别看那一行摘要：**
- Step 0 之后没有报错
- `Step 3: 生成平台页面` 成功
- `Step 4: 部署到 GitHub Pages` 显示 `✅ 已部署 N 个文件`

然后：

```bash
python3 generate_portal.py        # ⚠️ cron_scan.sh 不含这步，必须手动补
python3 -m pytest tests/ -q       # 应该 162 passed
```

> `output/assets/portal.js` 由 `generate_portal.py` 同步，`cron_scan.sh` 不跑它。
> 不补这一步那个文件会一直是旧的。

---

# 阶段 4 · 线上验收

按顺序看，前面错了后面不用看：

- [ ] 门户根页出来的是**今日概览**（顶部六格指标条 + 四张卡），不是直接落到某个板块
- [ ] 侧栏是**浅色面板**，激活项是白色胶囊 —— 还是深色块就说明 CSS 没更新
- [ ] 三个板块 iframe 都能点开，不是空白
- [ ] `platform.html` 四个 Tab 是**灰底分段控件**，不是四个彩色按钮
- [ ] `analysis/` 表格行高明显变紧，表头滚动时粘顶
- [ ] **跨境雷达那一栏** —— 它通过 HTTP 直链引用本仓库的 `shared/oa-theme.css`，会跟着变样。
      已核对它用的 14 个变量在 v6 里全都还在，但没有视觉基线可比，得亲眼看
- [ ] 手机上再走一遍以上全部

**怎么识别「混合体」：** 如果颜色是新的（暖石灰底）但布局是旧的（没有顶部指标条、侧栏是深色），
说明 `shared/oa-theme.css` 更新了而 `output/*.html` 没有——那就是 hermes 推了旧产物。
处理：确认本机代码已同步，重跑 `generate_platform.py` + `generate_portal.py`，再推一次。

---

# 阶段 5 · 善后（当天内做完）

- [ ] **确认 `~/product-analysis/restock_pipeline.sh` 里有 `python3 desensitize_analysis.py`**

      ⚠️ **这条最要紧。** 不做的话下个周一/四补货管道会把未脱敏的 HTML 推到 `main`，
      `update.yml` 的 `--check` 门禁会**拦下整个部署**——站点那天完全不更新，
      而失败只在 GitHub Actions 里可见，不在 cron 摘要里。
      `oa/desensitize.py` 幂等（D10），补上去多跑一次没副作用。

- [ ] 清 stash 积压：`git stash list` → 确认无用后 `git stash clear`
- [ ] 盯一下第二天 09:10 那次自动 cron 的摘要

---

## 出问题怎么退

Pages 部署是幂等的，`main` 回退再推一次就恢复：

```bash
git checkout main
git revert <出问题的 commit 的 sha>
git push origin main
```

**2026-08-29 产物出库后的语义变化**（[PROPOSAL-artifacts-out-of-git.md](./PROPOSAL-artifacts-out-of-git.md)）：
`output/index.html`、`platform.html`、`output/data/*.js` 不再入库，由 CI 在部署时从
`data/` 现场生成。revert 只回退代码和数据，产物要等部署 workflow 重跑完（2~3 分钟窗口），
窗口内线上仍是旧产物。换来的是：生成器是「代码 × 数据」的确定性函数，revert 后 CI
生成的一定是「回退后代码 × 回退后数据」，**不会再出现「新产物 + 旧代码」的混合体**。
补货页 `output/analysis/` 仍入库，随 revert 原子回退。

---

# 部署之后：剩下的事按这个顺序

| 优先级 | 事项 | 为什么是这个位置 | 卡在谁 |
|---|---|---|---|
| **1** | **部署 Cloudflare Worker + 填 `config.json` 的 `kanban_sync.endpoint`** | 选品看板是唯一需要多人协作的功能，不做它就只是个单人工具。A 同事标的「值得做」B 同事看不到 | 需要你部署 Worker + 设 Secret，步骤见 DESIGN-DECISIONS「部署清单」 |
| **2** | **吊销旧 GitHub Token** | 它曾暴露在浏览器 `localStorage` 里。删代码不等于凭据失效 | 你在 GitHub 后台操作 |
| **3** | **写团队使用文档** | 团队第一次打开会问「达标/偏低是什么意思」「为什么毛利率不是数字」「可售天数怎么算」。现在没地方查 | 我可以写初稿，你补业务口径 |
| **4** | **广告异常监控板块** | 唯一的功能缺口。方案已出（[`PROPOSAL-ads-module.md`](./PROPOSAL-ads-module.md)），但卡在四个问题 | **需要你先定**：领星广告表的字段、数据粒度、更新频率、**公开页面怎么处理花费和 ACOS** |
| **5** | ~~协作边界重构~~ **✅ 2026-08-29 已落地**：CI 现场生成产物（`update.yml`），本机 cron 只推 `data/`，零重叠 | 见 [`PROPOSAL-artifacts-out-of-git.md`](./PROPOSAL-artifacts-out-of-git.md)；观察一周稳定后可删 `verify-ci-generation.yml` | — |

### 第 4 项那个必须你拍板的问题

Pages 是**全世界可见**的。广告花费和 ACOS 比毛利率更能反推出你们的单位经济模型，
而 `PROJECT-VISION.md §6` 目前只把毛利率/月销量/库存列为敏感字段，广告不在里面。

两条路：
- **走脱敏**（同 D10）：ACOS 和花费换成档位标签，只有紧急度和计数出数字
- **换托管**：如果团队需要看真实数字，那广告板块就是「Pages 该不该继续公开」这个决定的触发点

这条不定，广告板块没法开工。
