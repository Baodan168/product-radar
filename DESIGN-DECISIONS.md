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

## D10 — 补货页脱敏放在发布边界，不在生成器

**选择：** 在 product-radar 内做发布边界脱敏（`oa/desensitize.py`），把毛利率、7 天销量、日均换成档位标签；售价、可售天数、建议补货量、库存状态保持原样。

**理由：** 上一轮把这条记为「仓库外，改不到」。这次把 `liyuhong168/product-analysis` 加进会话核实后发现两件事：

1. 那个仓库里**只有生成好的 HTML，没有任何 `.py`** —— 生成器源码根本没上 GitHub，确实改不到。
2. 而且那个仓库自己发布的那份表头是「评分 / BSR / 趋势」，**本来就不含毛利率**。含毛利率的是 `product-radar/output/analysis/` 这份，来源是本机 `/home/lee/product-analysis/gh-pages/`（`transform_analysis.py:5` 读的就是这个路径）。

根因够不到，但发布边界够得到 —— 这 47 个文件是 git 跟踪的，经 `update.yml` 的 `cp -r output/*` 进 Pages。在边界拦截还有个额外好处：不管上游生成器怎么变都拦得住。这和 `oa/restock.py`（容错解析上游产物）、`oa/safe_write.py`（防塌缩）是同一条「不信上游」的思路。

**档位阈值锚定 `config.json` 的 `min_profit_margin`**，不另立标准。

**代价与教训：** 正则改 HTML 很脆，而这次是写不是读。实施时真踩了一次：KPI 正则的 `(.*?)` 跨了卡片边界，把 46 个详情页的「售价」「库存状态」两张卡整个吞掉。而**只查「敏感数据还在不在」完全看不出来** —— 被删的卡里本来就没有敏感数字，体积也只掉了 4%，两道网都漏了。所以 `scrub_html()` 现在是三道检查：没泄露、**该留的还在**（`PRESERVED_MARKERS`）、体积没塌。第二道是被这次事故逼出来的。

另外脱敏必须幂等：脱敏后的值（达标/中/低）不含数字，再跑一遍会被判成「取不到数」而抹成「—」。`_already_bucketed()` 负责跳过。

---

## D11 — 移除暗色模式

**选择：** 把暗色模式整套删掉，回到单一浅色。

**理由：** 这是我理解偏差造成的返工，记下来免得重蹈。重构初期问「视觉语言怎么处理」，用户选了「整套设计系统升级」，我把它做成了**令牌层重写 + 暗色模式 + 新组件**，而用户想要的是**换一套新视觉**。结果是门户根页确实从空壳变成了今日概览，但选品平台和补货页的观感和重构前几乎一样 —— Phase 1 验收时截图逐字节一致，我当时还把它当作「无回归」的成绩，其实正说明视觉根本没动。

暗色本身没人用，留着是负担：改任何一个颜色令牌都要同步维护两个暗色块，遗留 shim 还得为存量页面写高特异度覆盖。

**代价：** 删掉约 180 行 CSS、40 行 JS 和 4 项测试。但**令牌层的整理没有白费** —— 正因为组件层几乎全部走 `var(--oa-*)`，暗色当初才能靠覆盖令牌值实现；同样的道理，下一轮换肤也只需要改 `:root` 的令牌值，全站生效。这个前提由 `tests/test_theme.py` 守着。

**教训：** 「升级设计系统」是个歧义词。下次遇到应当先确认是**换观感**还是**理架构** —— 两者投入产出完全不同，而且做完之后长得不一样。

---

## 下一轮：前端 UI 升级（交接）

> 写给接手的新会话。上下文对话读不到，但下面这些足够开工。

### 目标（用户已确认）

1. **视觉风格换新** —— 配色、字体、圆角、阴影、卡片质感，换一套更现代的皮
2. **信息密度与版式** —— 表格太宽 / 卡片太空 / 一屏看不完这类问题，重排布局与间距

明确**不要**暗色模式（见 D11）。

### 起点状态

分支 `claude/oa-portal-redesign-9vaqif`（`main` 未动，是兜底）。门户 v4 / 选品平台 v6 / 119 项 pytest 全绿。

```
shared/oa-theme.css   令牌层 :root → 组件层 .oa-* → 页面私有类 → 遗留 shim
templates/*.html      门户与平台的结构
assets/*.js           门户与平台的交互
oa/                   生成器内核（config / render / dashboard / desensitize …）
```

### 换肤的入口就一个

**改 `shared/oa-theme.css` 顶部 `:root` 的令牌值，全站生效。** 组件层几乎不写死颜色，这是 Phase 1 整理出来的前提，`tests/test_theme.py::test_no_bare_color_aliases_in_component_layer` 守着它。

改版式则主要动组件层的 `.oa-dash-*`（今日概览）、`.oa-card` / `.oa-table` / `.oa-kpi`（通用），以及页面私有类里的 `.pc`（产品卡）、`.kanban-*`（看板）、`.insight-*`（趋势卡）。

### 三条硬约束

1. **`output/analysis/*.html` 是仓库外产物** —— 由本机 `~/product-analysis/` 生成，自带硬编码颜色的内联 `<style>`，且排在 `<link>` 之后。要覆盖它的样式，选择器特异度必须高过裸类选择器。**改不到它的源码。**
2. **补货页产物提交前必须跑 `python3 desensitize_analysis.py`** —— 否则 CI 的 `--check` 门禁会拦下部署（毛利率/销量不能上公开页，见 D10）。
3. **改样式不走内联 CSS**，一律进 `shared/oa-theme.css`（CLAUDE.md 操作禁忌）。

### 第一步必做

```bash
python3 generate_platform.py && python3 generate_portal.py
python3 tools/snapshot.py --out .screenshots/before      # 建视觉基线
```

`.screenshots/` 不入库，新会话没有基线。而 `data/channels`（297 个）、`data/discovery`（33 个）、`output/analysis`（47 个）**都在仓库里**，所以 clone 完就能渲染出真实数据的页面，不是空壳。

改完再截一次对比 —— 视觉重构最容易在「改 A 页面顺手影响了 B 页面」上翻车，尤其是页面私有类和遗留 shim 那两层是多个页面共用的。

### 建议的推进方式

先出 2–3 个视觉方向给用户选（可以只改令牌值做几版对比图），定了再铺开。别一上来就全量改 —— 这轮会真实改动补货页和选品平台的观感，回归面比前面几轮大。

---

## WSL 接续（本地会话开场白）

> 前面几轮都在云端容器里做（Claude Code on the web）—— 能改仓库内的一切，
> 但碰不到本机的 `~/product-analysis/`、`~/.hermes/` 等等。
> 要让 Claude 直接操作那些，在 WSL 里装 CLI 从项目目录启动：
>
> ```bash
> npm install -g @anthropic-ai/claude-code
> cd /home/lee/product-radar && claude
> ```

启动后可直接粘贴这段：

```
读 CLAUDE.md 的「本地运行（WSL）」章节，和 DESIGN-DECISIONS.md 的
D1–D11。前面几轮重构都在云端做的，决策记录都在这两处。

当前分支应该是 claude/oa-portal-redesign-9vaqif（main 是兜底，别动）。
先确认能跑通：
  python3 -m pytest tests/ -q          # 应 119 项全绿
  python3 generate_platform.py && python3 generate_portal.py
  python3 desensitize_analysis.py --check

这一轮要做的是 <填你的目标>。
```

### 本地才能做、云端一直做不了的三件

1. **`~/product-analysis/` 生成器根因** —— 让它直接输出档位标签，
   本仓库的 `oa/desensitize.py` 就退化成冗余保险（见 D10）
2. **`{fba_days}` 占位符未渲染** —— 16 个详情页公开显示这个字面量
3. **真实管线端到端验证** —— 带凭据跑 `cron_scan.sh`，云端没凭据没外网

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
| 补货页脱敏（已处理） | 已由 D10 的发布边界方案解决。**根因仍在仓库外**：本机 `~/product-analysis/` 每跑一次仍会产出含敏感数字的 HTML，本仓库是在它进 `output/` 之后、上 Pages 之前拦截。若之后把那个项目的源码推上 GitHub，可以再改根因，届时本层作为冗余保留。 |
| ⚠️ 上游模板占位符未渲染 | 16 个详情页公开展示字面量 `{fba_days}`（「库存仅剩{fba_days}天，必须空运！」）—— 上游生成器的模板变量没替换。这是显示 bug 不是安全问题，脱敏工具没碰它。需在 `~/product-analysis/` 侧修。 |
| git 历史里的旧数据 | 这 47 个文件的历史版本仍在 commit 里，且仓库是 public。彻底清除需要 `git filter-repo` 改写历史并强推，风险自担，本次未做。 |
