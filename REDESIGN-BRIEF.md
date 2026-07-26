# Redesign Brief — for Claude Code

> 本文档是 Hermes Agent（本地维护者）写给 Claude Code（重构执行者）的协作简报。
> 目标：让你在开始工作前有完整的「局内人视角」，减少试错。

---

## 1. 重构目标

**不改功能，改体验。** 系统已经能正常跑，现在的瓶颈是：
- 前端 UI 粗糙（直接 Python 拼接 HTML 字符串）
- 页面布局/视觉风格不够专业
- 门户、选品平台、补货跟进之间视觉一致性差

**核心任务：** 在保留全部现有功能的前提下，让整个 OA 门户看起来像正规格的产品。

---

## 2. 我（Hermes）已经为你做了哪些准备

- ✅ 项目完整文档：PROJECT-VISION.md（愿景）、ARCHITECTURE.md（架构）、CLAUDE.md（速查）
- ✅ 数据文件和 HTML 产物不在 GitHub 上（gitignored），不会影响你的工作
- ✅ main 分支是稳定版，你在 redesign 分支随便改，main 不受影响
- ✅ config.json 和所有 Python generator 都可以安全重构
- ✅ 所有凭证（token/密码）在本地 .env，不在仓库里

---

## 3. 设计偏好（Lee 的口味）

这是 PROJECT-VISION.md 里没写的、来自长期使用反馈的设计约束：

### 3.1 选品平台页面（platform.html）

- **头部极简**：无 logo、无版本标签、无全局搜索按钮
- **h1 纯文字**：无 emoji 前缀
- **副标题**用长句描述（一句话说明这个页面干什么的）
- 所有内容紧凑排列，不浪费纵向空间
- 产品卡片必须有 Amazon UK 主图

### 3.2 门户页面（index.html）

- 保持现有 hero 布局（左侧导航 + 右侧内容区）
- 跨境雷达 iframe 区域保持完整布局（不砍它的 hero）
- 补货跟进入口保持简洁

### 3.3 通用

- Apple-inspired 设计风格：干净、留白适中、信息密度高
- 颜色主调保持 `#1a1a2e`（深色基调）
- 不要过度动画，不要花哨特效
- 中英文混排时注意字体兼容
- 响应式不是刚需（主要台式机使用），但不要太难看

---

## 4. 什么事不能做（红线）

| 红线 | 原因 |
|------|------|
| ❌ 不要改 `data/` 目录结构 | `data/channels/`、`data/discovery/`、`data/history/` 是扫描数据，generator 依赖它们的路径 |
| ❌ 不要改 `config.json` 的 schema | 所有 generator 和 scanner 依赖现有的 JSON 结构 |
| ❌ 不要改 `output/` 的生成路径 | 部署脚本（github_api_push.py）硬编码了这些路径 |
| ❌ 不要删现有文件 | 有些文件（如 `cron_scan.sh`、`restock_pipeline.sh`）不被 generator 直接引用，但生产调度依赖它们 |
| ❌ 不要改 `shared/oa-theme.css` 的引用方式 | 所有页面通过 `<link>` 引用，样式统一走这个文件 |
| ❌ 不要碰 product-analysis/ 的内容 | 那是独立本地项目，只输出产物到 output/analysis/ |
| ❌ 不要把数据存到 GitHub | 所有数据在本地生成，通过 github_api_push.py 部署产物 |

---

## 5. 重构优先级建议

### P0（必须做）
- 门户页（index.html）视觉升级 — 它是用户的 landing page，第一印象
- 选品平台（platform.html）视觉统一 — 最常用的功能页面

### P1（建议做）
- generator 代码结构优化 — `generate_platform.py` 1146 行，职责过重，建议拆分为模块化组件
- CSS 整理 — `oa-theme.css` 里可能有冗余/冲突的样式定义

### P2（有余力做）
- 补货跟进页面（analysis/）视觉对齐门户风格
- 响应式适配（主要桌面，但移动端不要太崩）

---

## 6. 已知坑点（爬过的坑）

这些是踩过之后才知道的，写文档时不会出现：

- `scanner.py` 的 `is_forbidden()` 返回 `False` 不是元组，用 `if is_forbidden():` 判断
- PP 每日缓存是单日快照，不是月累计（但重构 generator 用不到这个，仅供参考）
- `generate_platform.py` 的过滤参数要从 `config.json` 读取，代码默认值必须与 config 一致
- 部署后 GitHub Pages CDN 缓存约 600 秒，验证时要等 2-3 分钟

---

## 7. 协作方式

```
你（Claude Code Cloud Session）    我（Hermes 本地）
       │                                 │
       │  read REDESIGN-BRIEF.md         │
       │  read PROJECT-VISION / ARCH     │
       │         │                       │
       │  git checkout -b redesign       │
       │  do the work                    │
       │  git commit + push              │
       │         │                       │
       │                                 │  git pull (周一)
       │                                 │  python3 generate_portal.py
       │                                 │  测试验证
       │                                 │  给你反馈
```

**你只需要关注 redesign 分支上的代码质量。数据、部署、验证、回滚都交给我。**

---

## 8. 给 Claude Code 的最终建议

1. 先读 PROJECT-VISION.md 理解为什么做，再读 ARCHITECTURE.md 理解怎么做
2. 然后读 generate_portal.py 和 generate_platform.py 的完整代码
3. 在脑海里形成设计方向后再动手
4. **每一步 git commit，不要一次性改完再提交**
5. 关键设计决策写在 DESIGN-DECISIONS.md
6. 遇到不确定的，在代码里加 TODO 注释，周一 Hermes 会看到

---

*Happy redesigning. — Hermes*
