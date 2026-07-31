# 方案：Claude Code 与 hermes agent 的协作边界

> **状态：待确认，未实施。** 涉及 `cron_scan.sh` 和 `update.yml`，都是生产自动化，先出方案。

---

## 问题的根源只有一个

两个 agent 在改同一批 **git 跟踪的产物文件**。

| 谁 | 在哪 | 现在写什么 |
|----|------|-----------|
| Claude Code | 临时容器，只能推分支 | 代码 + **`output/index.html`、`output/platform.html`、`output/analysis/*.html`** |
| hermes agent | 公司电脑，直推 `main` | 数据 + **`output/index.html`、`output/platform.html`、`output/data/*.js`** |

加粗的部分就是全部摩擦的来源。由此派生出的具体症状：

- hermes 每次 cron 都得 `git stash push` 把本地重新生成的产物收走才能 pull（`cron_scan.sh:11`），而那个 stash **从来没有被 pop**，每跑一次积一层
- 一旦 hermes 跑的是旧代码、推的是旧 HTML，而 `shared/oa-theme.css` 已经是新版 → 线上是**旧 markup + 新 CSS 的混合体**，不是干净的回滚
- `github_api_push.py` 要推 1.2MB 的 `platform.html` 和 1.4MB 的 `radar-all.js`，这就是它注释里那句「绕过 git push 超时问题」的由来

## 建议：按「谁生产什么」重新划边界

```
代码（.py / .css / .js / 模板）   → Claude Code，走分支 + PR，永不直推 main
数据（data/**、status.json）      → hermes，直推 main（不变）
补货产物（output/analysis/）      → hermes（来自仓库外的 product-analysis）
门户与平台页面（output/*.html）    → 谁都不拥有，由 CI 在部署时生成
```

### 关键前提已经成立

`update.yml` 里加两行 `python3 generate_platform.py && python3 generate_portal.py` 就够了，因为：

- **数据全部在仓库里**：`data/channels` 297 个、`data/discovery` 33 个、`data/history` 80 个，都是 git 跟踪的
- **生成器只依赖标准库**：`requirements.txt` 里的 requests / bs4 / lxml / curl_cffi / playwright 全是给爬虫的；两个生成器只用 `json / re / os / sys / glob / shutil / urllib.parse / html / subprocess` + 仓库内模块
- **CI 已经能跑 Python**：`update.yml` 没有 `setup-python` 也没有 `pip install`，但 `desensitize_analysis.py --check` 一直跑得通
- **节日数据有仓库内回退**（D9），不依赖本机绝对路径

### 收益

1. **零重叠** —— 两个 agent 再也不会碰同一个文件
2. 线上产物必然是「当前代码 + 当前数据」的组合，**混合体这种失败模式从原理上消失**
3. hermes 的 stash 积压自然消失（它不再修改我也改的跟踪文件）
4. `github_api_push.py` 推送量降一个数量级，超时问题顺带解决
5. 我这边也变干净：分支里不再出现几 MB 的产物 diff，review 时看得见真正改了什么

### 代价与风险

- 生成失败 → 部署失败 → 站点当天不更新。**这比部署一个坏页面好**，但需要告警（见下）
- `output/index.html`、`output/platform.html`、`output/data/*.js` 要从 git 里 untrack（`git rm --cached`），并确认 `.gitignore` 覆盖
- 一次性的流程改动，改完前几天需要盯

---

## 三个护栏（跟上面那条独立，可单独做）

### 1. `cron_scan.sh` 的同步失败不能是静默的

现在开头三行是：

```bash
git fetch origin
git stash push -m "auto-scan-pre-sync" 2>/dev/null || true
git pull --rebase --autostash origin main 2>/dev/null || git merge --ff-only origin/main 2>/dev/null || true
```

每一步都 `2>/dev/null` + `|| true`。万一同步没成功，脚本会**继续用旧代码生成并推上去**，而 cron 只给一行摘要，你看不出来。

建议：同步失败要么中止，要么在最终那行摘要里明确带出「⚠️ 代码未同步」。另外那个 stash 要么 pop 要么别 push（`--autostash` 已经在做同样的事）。

### 2. `cron_scan.sh` 补一次 `generate_portal.py`

它现在只跑 `generate_platform.py`，但 `github_api_push.py` 的「总是推送」清单里有 `output/assets/portal.js`。那个文件由 `generate_portal.py` 同步，不跑就一直是旧的。
（目前有 `update.yml` 的拷贝顺序兜着 —— 根目录 `assets/` 排在 `output/*` 之后，所以线上不受影响。但这是巧合不是设计。）

### 3. 部署后自检

`update.yml` 末尾加一步：抓取刚部署的页面，断言几个标志物存在（比如 `oa-dash-strip`、`shared/oa-theme.css` 可达、没有字面量 `{fba_days}`）。
「旧 markup + 新 CSS」这种混合体人眼要看才发现，机器一断言就知道。

---

## 一个必须先解决的遗留

**我这轮提交了 47 个脱敏后的 `output/analysis/*.html`。下次补货管道一跑就会被覆盖成未脱敏版本。**

因果链：`restock_pipeline.sh`（在仓库外的 product-analysis）`cp` 新产物 → git push 到 main → `update.yml` 的 `desensitize_analysis.py --check` 门禁**拦下整个部署** → 站点那天完全不更新，而失败只出现在 GitHub Actions 里，不在 cron 摘要里。

所以脱敏必须是**管道里的一步**，不能是我一次性提交的结果。需要确认 `restock_pipeline.sh` 里有没有这行：

```bash
python3 desensitize_analysis.py
```

`oa/desensitize.py` 是幂等的（`_already_bucketed()` 会跳过已脱敏的值，见 D10），所以多跑一次没有副作用。

---

## 协作协议：仓库里放一份交接文件

架构和护栏都是一次性的。日常「无缝」靠的是一个双方都读的地方 —— [`HANDOFF.md`](./HANDOFF.md)：

- **我写**：代码升级后本机需要做什么、有哪些待人工确认的事
- **hermes 读**：下次 cron 时按清单执行，做完划掉
- **CLAUDE.md 里加了指引**，任何在这个仓库工作的 agent 开工前都会看到

这个协议成立的前提是 hermes 会读 CLAUDE.md。如果它的系统提示里没有这条，需要加一句。
