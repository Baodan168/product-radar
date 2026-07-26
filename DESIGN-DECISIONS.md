# Design Decisions — OA 门户重构

> 本文档记录重构期间每个关键设计决策的**选择、理由和代价**。
> 「为什么存在」见 [PROJECT-VISION.md](./PROJECT-VISION.md)，「怎么运作」见 [ARCHITECTURE.md](./ARCHITECTURE.md)。
>
> 重构分支：`claude/oa-portal-redesign-9vaqif` · `main` 保持不动作为兜底

---

## 重构的起因

读完 PROJECT-VISION、ARCHITECTURE 和 audit-report 后，确认了三类结构性问题：

1. **门户是个空壳** — `generate_portal.py` 只做 iframe 切换。PROJECT-VISION §5.1.2 写着「每个页面只回答一个问题——现在该选什么、补什么、关注什么」，但门户根页一个问题都没回答，打开就落到某个板块，用户还得自己翻。
2. **设计系统分叉** — `shared/oa-theme.css` 1383 行里同时存在两套命名（203 条 `.oa-*` 组件类 + 509 条 `.shell/.hero/.date-bar` 页面私有类）和两套令牌（`--oa-*` 与 `--muted/--purple` 裸别名）。没有暗色模式。
3. **生成器单体 + 安全边界破了** — `generate_platform.py` 1146 行一个函数混着数据加载和 HTML/CSS/JS 拼接；14 处内联 `onclick`、16 处 `innerHTML` 拼外部数据；GitHub Token 存浏览器 `localStorage`（audit P0）。

---

## D1 — 保留 iframe 聚合架构，而不是改多页面或 SPA

**选择：** 保留 3+1 方案C 的 iframe 聚合，把它修好而不是换掉。

**理由：** 跨境雷达在独立仓库 `kj-news-radar`（数据源、更新频率、部署链路都不同），iframe 是唯一不需要跨仓库构建就能聚合的方式。改成多页面跳转会让门户退化成一个导航页，失去统一外壳和统一时钟/主题；改 SPA 则要把三个板块的渲染逻辑合并进一个构建，成本远超收益。

**代价：** iframe 的可观测性天生弱——跨域子页面的内部错误抓不到。因此必须补健康探针、加载超时和显式错误态（见 D4）。

---

## D2 — 分支用 `claude/oa-portal-redesign-9vaqif`

**选择：** 在环境指定的 `claude/oa-portal-redesign-9vaqif` 上开发，不新建 `redesign`。

**理由：** 自动化流程按这个分支名跟踪，另起一个名字会让 CI 和后续会话找不到工作。`main` 无论如何不动，兜底目的已经达成。

---

## D3 — 设计令牌统一到 `--oa-*`，裸别名降级为 shim

**选择：** `--oa-*` 是唯一的令牌命名空间。`--muted / --purple / --blue` 这类裸别名不再是一等公民，集中到文件末尾的遗留 shim 区，仅为存量页面服务。

**理由：** 两套令牌并存意味着改一个颜色要改两处，且新代码不知道该用哪套。裸变量名（`--blue`）还有和其他库冲突的风险。

**代价：** 不能直接删——`output/analysis/*.html` 和现有 platform 页面在用。所以是「隔离 + 标记废弃」而不是「删除」。

---

## D4 — iframe 加载状态区分四种，不再把空白当成功

**选择：** 加载结果分 `正常 / HTTP 错误 / 网络失败 / 加载超时` 四态，各有明确 UI。

**理由：** audit P2 指出 iframe 的 `error` 事件识别不了 HTTP 404/500——服务器返回错误页时浏览器照样触发 `load`。重构前的基线截图正好抓到这个 bug：跨境雷达 iframe 完全没加载出来，顶栏却显示「已加载 03:20」，右侧一片空白。用户无法判断是没数据还是挂了。

**做法：** 每个板块声明探针 URL，`fetch` 判可达；iframe 加 8s 超时；同源子页面通过 postMessage 上报「我渲染好了」。跨域的雷达只能判到网络层，状态显式标为「未知」而不是伪装成「正常」。

**代价：** 跨域板块的健康度永远只能是「可达/不可达/未知」三态，拿不到「页面内部是否正常渲染」。这是同源策略的硬限制，不掩饰。

---

## D5 — 看板状态同步走 Cloudflare Worker 代理

**选择：** Token 移到 Worker Secret，浏览器只 POST 状态 JSON 到 Worker，由 Worker 持凭据调 GitHub。

**理由：** audit P0——Token 存在 `localStorage` 里，任何能在页面执行 JS 的代码都能读走它，配合同页面的 XSS 面（16 处 `innerHTML` 拼外部数据）就是一条完整的凭据窃取链。GitHub Pages 是纯静态的，没有服务端，但仓库里**已经有一个 Cloudflare Worker**（`cloudflare-worker.js`，原本用作 Amazon 抓取代理），加一条路由的边际成本最低，且保住了多设备同步这个功能。

**代价：** 需要手动在 Cloudflare 部署新 Worker 并设 secret。在那之前看板同步不可用——但会**显式提示「同步未配置」，不静默失败**。

**被否掉的方案：** 取消浏览器写入改本地导入导出（干净但丢多设备同步）；保留现状只加防护（P0 降级不消失）。

---

## D6 — 首页四张卡全部服务端渲染，不走 iframe

**选择：** 「今日概览」由 `generate_portal.py` 直接渲染进门户主区，同源，无 iframe。四张卡：今日选品战情 / 补货告警 / 节日倒计时 / 数据新鲜度与板块健康。

**理由：** 首页是回答 PROJECT-VISION §5.1.2 那个问题的地方，必须秒开且不受 iframe 加载状态影响。数据全部复用现有模块（`load_all_radar`、`season_engine`、`festival_engine`、`success_tracker`），不新增数据管线。

**脱敏：** 遵守 PROJECT-VISION §6，毛利率/月销量/库存不出数字，只出「紧急 N 个」这类计数与标签。

---

## D7 — 缺失数据用 `{value, status, error}` 表达，不用 0 兜底

**选择：** dashboard 数据层统一 schema，区分「真实为 0 / 没抓到 / 抓取失败 / 不适用 / 正常」。

**理由：** audit P3——利润为 `0` 和「利润计算失败」对选品判断完全不是一回事，用默认值掩盖错误会让人做错决定。补货告警卡尤其需要：它靠**解析 HTML** 拿数据（`output/analysis/` 只产出 HTML，没有 JSON），解析失败必须显示「数据不可用」而不是「紧急 0 个」。

---

## D8 — `MODULES` 从 `generate_portal.py` 移到 `oa/config.py`

**选择：** 门户导航配置移入 `oa/config.py`，作为单一事实源。

**理由：** 门户壳拆成模板 + 资源后，`generate_portal.py` 只剩 CLI 入口，配置留在里面不合适；首页的「板块健康」卡也要读同一份板块清单，放在生成器里会形成循环依赖。

**代价：** 这改变了 CLAUDE.md 里「加新板块只改 `generate_portal.py` 的 `MODULES` 数组」这条规则。**CLAUDE.md 和 ARCHITECTURE.md §11 已同步更新**，避免文档和代码脱节。

---

## D9 — 数据文件的写入要防塌缩

**选择：** 凡是「重新生成整份数据文件」的写入都过 `oa/safe_write.py`，新数据为空或不足旧数据一半就拒绝写入并报警。

**理由：** 重构期间真实触发了一次。`load_festivals()` 的数据源是一台机器上的绝对路径，本机没有那个路径 → 静默返回 `[]` → 生成器把 `window.FESTIVALS = [];` 写进 `output/data/festivals.js`，133KB 数据没了。而且页面还「正常」生成，只是节日 Tab 空了——不点那个 Tab 根本发现不了。

**配套：** `FESTIVAL_SOURCES` 加了两级仓库内回退（`data/festivals_data.js` → 上次产物），不再依赖单台机器的绝对路径。

**原则：** 宁可显示上一次的数据，也不要显示空的。空数据看起来像「今年没节日」，而不是「数据源挂了」。

---

## 部署清单（Phase 5 之后需要手动做的）

看板同步改走 Worker 代理后，**在下面三步做完之前同步不可用**（页面显示「已存本地」，状态只保存在本机浏览器，不会静默失败）：

1. 部署 Worker：`wrangler deploy`，或在 Cloudflare 控制台粘贴 `cloudflare-worker.js`
   ⚠️ 文件已从 Service Worker 格式（`addEventListener`）改成 Module 格式（`export default`），因为 Secret 只能通过 `env` 参数拿到。控制台粘贴时注意选对格式。
2. 设置 Secret 与变量：
   ```
   wrangler secret put GITHUB_TOKEN        # 只需 Actions:write，不要给 contents:write
   # 环境变量 ALLOWED_ORIGIN = https://liyuhong168.github.io
   ```
3. 把 Worker 地址填进 `config.json` 的 `kanban_sync.endpoint`，重新生成平台页。

**另外：** 浏览器里之前存过的那个 GitHub Token 应当去 GitHub 后台**吊销**——它曾经暴露在 `localStorage` 里，代码删掉不等于凭据失效。

---

## 已知限制 / 待办

| 项 | 说明 |
|----|------|
| `output/analysis/*.html` 的内联样式 | 这些页面由**仓库外**的本地项目 `~/product-analysis/generate_html.py` 生成，带硬编码 `#fff / #6e6e73` 的内联 `<style>`。本仓库只能用更高特异度的 CSS 覆盖让它适配暗色，清不掉源头。根治需改 `product-analysis` 项目。 |
| 跨境雷达的主题跟随 | 跨域 iframe 无法注入主题。通过 `?theme=` 传参，对方仓库不实现则无效。 |
| 跨境雷达的健康探针 | 跨域只能 `no-cors` 探到网络层，判不出 HTTP 状态码，故显示「未知」。 |
| Worker 部署 | D5 的 `/kanban-sync` 路由需要手动部署 + 设 secret 才生效。 |
| ⚠️ 补货页脱敏缺口 | `output/analysis/index.html` 当前在公开页展示 **毛利率 / 7天销量 / 日均** 三列，与 PROJECT-VISION §6「毛利率、月销量、库存在公开 HTML 中隐藏」冲突。该页由仓库外的 `product-analysis` 项目生成，本仓库改不到。**需在 `product-analysis/generate_html.py` 侧处理**，已在 Phase 1 截图验证时发现并上报。 |
