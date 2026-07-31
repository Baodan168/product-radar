# 交接：给生产机上的 Claude Code

> **在这个仓库里工作的 agent，开工前先读这里。**
> 最后更新：2026-07-31 by Claude Code（云端会话）

现在这个项目有三个执行者，各自能碰到什么不一样：

| 执行者 | 在哪 | 能碰到什么 | 推哪 |
|--------|------|-----------|------|
| **hermes** | 公司电脑，后台 cron，飞书交互 | 全部（凭据/ERP 导出/crontab） | 直推 `main`（产物+数据） |
| **生产机 Claude Code** | 同一台电脑的 WSL 终端 | 全部，含 `~/product-analysis/` 等仓库外源码 | 分支 → 合 `main` |
| **云端 Claude Code** | 临时容器 | 只有本仓库的代码 | 只推分支 |

---

## 一、现在的状态（2026-07-31）

`main` 已经有了：门户重构（D1–D11）、补货页脱敏、`update.yml` 的 `--check` 门禁。
最近 8 次 Actions 全绿，公开页上的毛利率已经是「达标 / 偏低」档位标签，不是数字了。

**还差最后一层：前端 UI 升级。** 全部在分支 `claude/oa-portal-ui-upgrade-ts4zrf`：

- 设计系统 v5 → **v6「暖石灰」**（D12–D15）：侧栏从近黑 `#1a1a2e` 改成浅面板 `#f1efeb`，
  三层平面靠明度分层，全站无深色块
- 收编 76 处散在 `:root` 外的硬编码颜色，顺带修好 5 处被批量替换弄坏的值
  （`var(--oa-surface)7ed` 这种，当时静默干掉了节日 Tab 的标签底色）
- 信息密度：门户加顶部六格指标条；补货表首屏 17 行 → 27 行；平台首屏洞察卡 2.2 → 3.5 张
- 4 条新测试守住「改令牌就能换肤」这个前提（这前提以前是假的，见 D13）
- 新增 `tools/preflight.py`（部署前只读体检）、`tools/skinpreview.py`（换肤预览）

分支已经并入最新 `main`（含 verify_status、套装正则、`{fba_days}` 修复那批），
**合过去是零冲突快进，162 项 pytest 全绿，`desensitize_analysis.py --check` 通过。**

---

## 二、生产机 Claude Code 的启动提示词（整段贴进终端）

```
先读这三份再动手：CLAUDE.md、HANDOFF.md、DEPLOY-CHECKLIST.md。

第一件事，只读体检：
  cd /home/lee/product-radar
  git fetch origin
  git checkout claude/oa-portal-ui-upgrade-ts4zrf
  python3 tools/preflight.py --fetch

把结论原样发我。有阻塞项就按它给的修法修，修完重跑到绿。
（preflight.py 只在这个分支上，main 上没有，所以要先 checkout。）

绿了之后按 DEPLOY-CHECKLIST.md 的阶段 2→3→4 走：
  1. 合并 claude/oa-portal-ui-upgrade-ts4zrf 到 main 并推送
  2. 去 Actions 确认 Deploy Product Radar 是绿的
  3. bash cron_scan.sh 跑一次完整链路，日志最后 40 行发我
  4. python3 generate_portal.py（cron_scan.sh 不含这步，必须手动补）
  5. python3 -m pytest tests/ -q，应该 162 passed
  6. 逐条走线上七项验收，结果发我

这几件事必须先问我，不要自己做：
- 部署 Cloudflare Worker、设 Secret、改 config.json 的 kanban_sync.endpoint
- 吊销任何凭据
- 动 crontab
- 新建板块（结构改动先出方案 —— 广告板块方案已在 PROPOSAL-ads-module.md）

hermes 的定时任务在 08:00 / 08:40 / 09:10 / 14:00，避开这几个点操作。
```

## 三、或者，一次终端都不用开

合并可以在 GitHub 网页上点 PR，线上七项验收就是用浏览器打开看。
只有「跑一次 `cron_scan.sh` 验证完整链路」需要机器，那一步可以飞书让 hermes 干：

```
在 /home/lee/product-radar 下：
1. git fetch origin && git checkout main && git pull origin main
2. bash cron_scan.sh，把日志最后 40 行发我
3. python3 generate_portal.py
4. python3 -m pytest tests/ -q
不要动 crontab，不要碰凭据，不要改 config.json。
```

---

## 四、合并之后还剩什么

| 优先级 | 事项 | 卡在谁 |
|---|---|---|
| 1 | 部署 Cloudflare Worker + 填 `config.json` 的 `kanban_sync.endpoint`。不做的话选品看板只存各人浏览器，A 标的「值得做」B 看不到 | 负责人（部署 Worker + 设 Secret） |
| 2 | 吊销旧 GitHub Token —— 它曾暴露在浏览器 `localStorage` 里，删代码不等于凭据失效 | 负责人（GitHub 后台） |
| 3 | 确认 `~/product-analysis/restock_pipeline.sh` 里有 `python3 desensitize_analysis.py` | 生产机 Claude Code |
| 4 | 写团队使用文档（「达标/偏低是什么意思」「可售天数怎么算」现在没地方查） | Claude 写初稿，负责人补业务口径 |
| 5 | 广告异常监控板块 —— 唯一的功能缺口 | 负责人先定 PROPOSAL-ads-module.md 末尾四个问题，尤其**公开页怎么处理花费和 ACOS** |
| 6 | 协作边界重构：把 `output/*.html` 的生成挪进 CI，让两边零重叠。见 PROPOSAL-agent-collab.md | 不着急，等这次部署稳了 |

第 3 项的因果链值得记住：`restock_pipeline.sh` 在仓库外，`cp` 完产物就 git push。
里面没有脱敏调用的话，未脱敏 HTML 会推上 `main`，`update.yml` 的 `--check` 会**拦下整个部署** ——
站点那天完全不更新，而失败只在 Actions 里可见，不在 cron 摘要里。
`oa/desensitize.py` 幂等（D10），补上去多跑一次没副作用。

---

## 五、三方各自的红线

**云端 Claude Code**
- 不提交 `output/index.html`、`output/platform.html`、`output/data/*.js` 的重新生成结果 ——
  那是 hermes 每次 cron 都会改的文件。**唯一例外是合并冲突**：产物必须是
  「合并后的代码 + 合并后的数据」的函数，这时候正确解法是重新生成，不是手挑冲突标记
- 不提交 `output/analysis/*.html` —— 那批归补货管道所有，本轮已把分支上多持有的那些退回 `main` 版本
- 永不直推 `main`

**生产机 Claude Code**
- 改代码走分支，别直推 `main`
- 上面那四件事先问负责人

**hermes**
- 代码改动走分支，让人 review；`main` 既是部署分支又是 hermes 的代码来源，直推代码会绕过所有测试门禁
- 产物和数据照常直推 `main`，这是设计好的（`github_api_push.py`）

**共同**
- **别本地和云端同时改同一个分支。** 这轮之后云端会话转只读，
  `claude/oa-portal-ui-upgrade-ts4zrf` 归生产机。
