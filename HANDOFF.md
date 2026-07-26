# 交接：Claude Code ↔ hermes agent

> **在这个仓库里工作的 agent，开工前先读这里。**
> Claude Code 在临时容器里跑、只能推分支；hermes 在公司电脑上跑、直推 `main`。
> 两边看不到对方的终端，这个文件是唯一的交接点。
>
> 边界怎么划的、为什么这么划 → [`PROPOSAL-agent-collab.md`](./PROPOSAL-agent-collab.md)（待确认）
> 最后更新：2026-07-26 by Claude Code

---

## 当前状态：有一批未部署的升级压在分支上

`main` 停在 `e13808b`。两轮工作全在 `claude/oa-portal-ui-upgrade-ts4zrf`：

- 门户重构（D1–D11）—— 今日概览、iframe 健康探针、看板 Worker 代理、补货页脱敏
- 前端 UI 升级（D12–D15）—— 设计系统 v5 → v6「暖石灰」，密度与版式

线上 Pages 仍是重构前的版本。123 项 pytest 全绿，`desensitize_analysis.py --check` 通过。

---

## 待 hermes 执行

> 这些都要**等负责人确认合并之后**再做。合并前 hermes 照常跑，不受影响。

- [ ] **合并落地后，手动跑一次 `python3 generate_portal.py`**
      `cron_scan.sh` 不含这一步，而 `output/assets/portal.js` 由它同步。不跑的话那个文件会一直是旧的。
- [ ] **清 stash 积压**：`git stash list`。`cron_scan.sh:11` 每次跑都 `git stash push` 但从不 pop，栈里大概积了不少。确认都是自动生成的产物快照后 `git stash clear`。
- [ ] **确认 `restock_pipeline.sh`（在 `~/product-analysis/`）里有 `python3 desensitize_analysis.py`**
      没有的话补上。否则下次补货管道会把未脱敏的 HTML 推到 `main`，`update.yml` 的 `--check` 门禁会拦下**整个部署** —— 站点那天完全不更新，而失败只在 GitHub Actions 里可见，不在 cron 摘要里。
      `oa/desensitize.py` 幂等（D10），多跑一次无副作用。

## 待人工确认（Claude Code 和 hermes 都做不到）

- [ ] **合并到 `main`** —— 往公开站点发布，需要负责人拍板。步骤见 [`DEPLOY-CHECKLIST.md`](./DEPLOY-CHECKLIST.md)
- [ ] **部署 Cloudflare Worker + 填 `config.json` 的 `kanban_sync.endpoint`**
      不做的话选品看板的状态只存各人浏览器，A 同事标的「值得做」B 同事看不到。步骤见 DESIGN-DECISIONS「部署清单」
- [ ] **吊销旧 GitHub Token** —— 它曾暴露在浏览器 `localStorage` 里，删代码不等于凭据失效
- [ ] **决定广告板块的数据源与脱敏口径** —— 见 [`PROPOSAL-ads-module.md`](./PROPOSAL-ads-module.md) 末尾四个问题

---

## 写给 Claude Code 自己的约束

- **不要提交 `output/index.html`、`output/platform.html`、`output/data/*.js`** 的重新生成结果 —— 那是 hermes 每次 cron 都会改的文件，提交它们必然制造冲突。改生成器和模板就够了，产物让 hermes（或将来的 CI）产。
- **不要提交 `output/analysis/*.html`** —— 那批文件来自仓库外的 product-analysis，下次补货管道一跑就被覆盖。脱敏要放进管道，不是一次性提交。
  ⚠️ 本轮已经违反了这条（提交了 47 个脱敏后的文件），处理办法见 PROPOSAL-agent-collab.md 末节。
- **永不直推 `main`** —— hermes 靠 `main` 同步代码，直推会让它在不知情的情况下换掉运行中的代码。

## 写给 hermes 的约束

- **代码改动不要直接提交到 `main`** —— 走分支，让 Claude Code 或负责人 review。`main` 目前既是部署分支又是 hermes 的代码来源，直接改代码会绕过所有测试门禁。
- **产物和数据照常直推 `main`**，这是设计好的（`github_api_push.py`）。
