# 部署检查清单：把分支上的升级发到线上

> 给明天回公司的自己。逐条走，别跳。
> 分支：`claude/oa-portal-ui-upgrade-ts4zrf` → `main`
> 风险分析的依据都在 [`PROPOSAL-agent-collab.md`](./PROPOSAL-agent-collab.md)

---

## 为什么不能让 09:10 的 cron 当第一次验证

`cron_scan.sh` 开头会 `git pull` 同步代码，所以**不会出现「hermes 用旧样子覆盖」**——
这一层是设计好的。但那三行每一步都带 `2>/dev/null || true`，同步失败是静默的，
脚本会继续用旧代码生成并推上去。cron 只给你一行摘要，看不出来。

所以：**选一个你能盯着的时间合并，然后手动跑一遍完整链路。**

---

## 第 0 步：合并前，在公司电脑上先看一眼

```bash
cd /home/lee/product-radar
git stash list          # 积了多少层（cron_scan.sh 每次 push 但从不 pop）
git status              # 有哪些本地改动
git log --oneline -3    # 本机在哪个 commit
```

**判断：** stash 里如果全是自动生成的产物快照，`git stash clear` 掉。
`git status` 里如果有你自己手改过的东西，先单独存出来。

## 第 1 步：合并

在 GitHub 上给 `claude/oa-portal-ui-upgrade-ts4zrf` 开 PR 合到 `main`，或者本地：

```bash
git fetch origin
git checkout main && git pull
git merge --no-ff origin/claude/oa-portal-ui-upgrade-ts4zrf
git push origin main
```

推上去会触发 `update.yml`：先跑 `desensitize_analysis.py --check` 门禁，过了才部署。
**CDN 缓存 600s，等 2–3 分钟再验证。**

## 第 2 步：手动跑一遍完整链路

```bash
cd /home/lee/product-radar
git fetch origin && git status        # 确认干净
bash cron_scan.sh                     # 看日志，不看那一行摘要
tail -40 logs/cron_*.log | tail -40   # 确认 Step 0 同步成功、Step 3 生成成功
python3 generate_portal.py            # ⚠️ cron_scan.sh 不含这步，手动补
python3 -m pytest tests/ -q           # 123 项应该全绿
```

## 第 3 步：验证线上

按这个顺序看，前面错了后面不用看：

- [ ] `https://liyuhong168.github.io/product-radar/` —— 门户根页出来的是**今日概览**（顶部六格指标条 + 四张卡），不是直接落到某个板块
- [ ] 侧栏是**浅色面板**，激活项是白色胶囊 —— 如果还是深色块，说明 CSS 没更新
- [ ] 三个板块 iframe 都能点开，不是空白
- [ ] `platform.html` 的四个 Tab 是**灰底分段控件**，不是四个彩色按钮
- [ ] `analysis/` 表格行高明显变紧、表头滚动时粘顶
- [ ] **跨境雷达那一栏** —— 它通过 HTTP 直链引用本仓库的 `shared/oa-theme.css`，会跟着变样。已核对它用的 14 个变量在 v6 里全都还在，但没有视觉基线可比，得亲眼看
- [ ] 手机上再走一遍上面这些

**混合体的识别方法：** 如果页面颜色是新的（暖石灰底）但布局是旧的（没有顶部指标条、侧栏是深色），
说明 `shared/oa-theme.css` 更新了而 `output/*.html` 没有 —— 那就是 hermes 推了旧产物。
处理：在公司电脑上确认代码已同步，重跑 `generate_platform.py` + `generate_portal.py`，再推一次。

## 第 4 步：善后

- [ ] 走一遍 [`HANDOFF.md`](./HANDOFF.md) 的「待 hermes 执行」清单
- [ ] 确认 `~/product-analysis/restock_pipeline.sh` 里有 `python3 desensitize_analysis.py`
      —— **这条不做，下个周一/四的部署会被门禁整个拦下**
- [ ] 盯一下第二天 09:10 那次自动 cron 的摘要

---

## 出问题怎么退

Pages 部署是幂等的，`main` 回退再推一次就恢复：

```bash
git checkout main
git revert -m 1 <合并那个 commit 的 sha>
git push origin main
```

因为产物（`output/*.html`）也在那个 commit 里，revert 会连产物一起回退，
所以是干净的回滚，不会留下混合体。

---

## 一个不用合并就能看真机效果的办法

`update.yml` 有 `workflow_dispatch`。可以直接从分支手动跑一次部署，**不合并 `main`**：
Actions → Deploy Product Radar → Run workflow → 选 `claude/oa-portal-ui-upgrade-ts4zrf`。

线上立刻变成新版本，你在手机和电脑上看完再决定。

**两个代价，别当成正式发布：**
1. 那段时间线上就是新版本，团队如果正在用会看到变化
2. hermes 下次推 `main` 会触发 `update.yml` 重新部署 `main` 的内容，**自动把线上刷回旧版** —— 它会自己回滚
