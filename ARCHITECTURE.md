# Amazon UK 选品运营 OA — 架构文档

> 对应仓库：[liyuhong168/product-radar](https://github.com/liyuhong168/product-radar)
> 门户地址：https://liyuhong168.github.io/product-radar/

---

## 1. 系统定位

Amazon UK FBA 小件铺货卖家的选品与运营门户，服务一个三店体系（老店稳定出单 + 测品增长 + 新店启动），聚焦 £6–10 价位段的轻小件蓝海选品。

---

## 2. 架构总览：3+1 混合方案

```
用户（浏览器）
     │
     ▼
┌──────────────────────────────────────────┐
│  OA 门户 (output/index.html)             │ ← iframe 聚合三大板块
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ 📡 跨境雷达│ │ 🎯 选品  │ │ 📦 补货  │ │
│  │ (iframe) │ │ 平台     │ │ 跟进    │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────┘
         │                │           │
         ▼                ▼           ▼
   kj-news-radar    product-radar   product-analysis
   (独立仓库)        (主仓库)        (本地项目)
```

**核心原则：** 三个核心板块（门户/选品平台/补货跟进）同仓库共享维护，跨境雷达因数据源差异独立部署。

---

## 3. 仓库与项目分工

| 仓库/项目 | 定位 | 代码位置 | 部署方式 |
|-----------|------|---------|---------|
| **product-radar** | OA 主仓库：门户生成、选品平台、补货跟进页面 | GitHub | git + GitHub API |
| **kj-news-radar** | 跨境雷达（24h 跨境电商情报聚合） | GitHub | GitHub Actions → Pages |
| **product-analysis/** | 补货分析引擎（本地项目，不在 GitHub） | 本地 | 生成产物 → cp 到 product-radar → 统一部署 |

> **关于 product-analysis/**：补货引擎的源码是本地项目，其生成的 HTML 产物通过 `restock_pipeline.sh` 复制到 `product-radar/output/analysis/`，经由 product-radar 的部署流程统一推送到 GitHub Pages。外部 agent 如需理解补货逻辑，需要同时查看本地 `~/product-analysis/` 目录。

---

## 4. 三大板块详述

### 4.1 🎯 选品平台

| 项目 | 说明 |
|------|------|
| **定位** | 四合一选品工具：趋势发现 + 雷达扫描 + 节日选品 + 选品看板 |
| **数据源** | Amazon UK（主）、TikTok、1688、Google Trends |
| **更新频率** | 每天 08:40 趋势发现 → 09:10 上午扫描 → 14:00 下午扫描（周一到六） |
| **关键文件** | `run_scan_v2.py`（扫描引擎）、`scanner.py`（过滤链）、`scoring_engine.py`（评分）、`generate_platform.py`（页面生成）、`config.json`（参数配置） |
| **访问路径** | `platform.html`（4 个 Tab：趋势发现/雷达扫描/节日选品/选品看板） |

### 4.2 📡 跨境雷达

| 项目 | 说明 |
|------|------|
| **定位** | 24h 跨境电商情报聚合，30+ 中文源自动采集 |
| **数据源** | 20+ 跨境资讯源（公众号/网站/RSS） |
| **更新频率** | 每天 09:00（GitHub Actions 自动） |
| **关键文件** | `scripts/update_crossborder.py`（采集脚本）、`data/latest-24h.json`（产物） |
| **访问方式** | OA 门户通过 iframe 直链引用独立仓库的 GitHub Pages |
| **评分权重** | Amazon UK +0.12 > Amazon 全球 +0.08 > EU/UK 合规 +0.05 > 跨境新闻 基准 > 非 Amazon -0.15 |

### 4.3 📦 补货跟进

| 项目 | 说明 |
|------|------|
| **定位** | 库存监控 + 补货建议，覆盖测品店和新店 |
| **数据源** | 领星 ERP PP 缓存（7 天数据） |
| **更新频率** | 每周一/四 08:00 |
| **关键文件**（本仓库） | `output/analysis/`（生成的补货页面） |
| **关键文件**（本地项目） | `product-analysis/replenish_engine.py`、`product-analysis/generate_html.py`、`product-analysis/restock_pipeline.sh` |
| **访问路径** | `analysis/`（补货分析页面） |

### 4.4 📈 广告异常监控 —— 未建

**这一节记录一个缺口，不是一个板块。** 团队负责人给的产品目标里，第三条是
「结合领星 ERP 数据和 AI，一到公司打开 OA 就知道哪些产品要补货、**哪些产品的广告要调整**」。
补货那半边已经跑通（§4.3），广告这半边**在网页上还不存在**：

- `product-radar` 无任何广告相关代码（搜 `ACOS`/`TACOS`/`campaign`/`adspend` 无命中）
- `product-analysis` 仓库的 32 个 HTML（index + 31 个 ASIN 页）全是趋势分析/库存状态/补货方案
- 全部文档里「广告」只出现一次：`PROJECT-VISION.md` §7「未来可能的方向」

领星导出和分析脚本可能已在本机存在某种形态，但**没有正式接进 OA**。
按 CLAUDE.md「结构改动必须先讨论」，加板块要先出方案再执行，
方案见 [`PROPOSAL-ads-module.md`](./PROPOSAL-ads-module.md)（待确认，未实施）。

---

## 5. 端到端数据流

### 5.1 选品扫描管道

```
Amazon UK 搜索 / TikTok 趋势 / 1688 / Google Trends
    │
    ▼
run_scan_v2.py（扫描引擎，CloakBrowser/Playwright）
    │
    ▼
scanner.py（过滤链）
  ├─ 价格过滤（config.json: £5.99–12.99）
  ├─ 评论数过滤（≤200）
  ├─ 评分过滤（≥3.5）
  ├─ 重量过滤（≤200g）
  ├─ 尺寸过滤（≤30×21×6cm）
  ├─ 禁售关键词过滤（100+ 项）
  └─ 多件套装排除（≥5pcs，极薄件豁免）
    │
    ▼
scoring_engine.py（评分引擎）
  ├─ UK 相关性 +0.12
  ├─ 全球 Amazon 相关性 +0.08
  ├─ EU/UK 合规相关 +0.05
  └─ 非 Amazon 主题 -0.15
    │
    ▼
calc_profit.py（利润计算：FBA 费用估算 + 20% 目标利润率）
    │
    ▼
generate_platform.py → output/platform.html（选品平台 4 Tab）
    │
    ▼
github_api_push.py → GitHub Pages 部署
```

### 5.2 补货管道

```
领星 ERP（近 7 天数据导出，Playwright 自动抓取）
    │
    ▼
product-analysis/replenish_engine.py（SKU 维度分析）
    │
    ▼
product-analysis/generate_html.py（生成 ASIN 分析 HTML）
    │
    ▼
restock_pipeline.sh
  ├─ cp 产物 → product-radar/output/analysis/
  ├─ generate_portal.py（刷新门户 iframe 引用）
  └─ github_api_push.py → GitHub Pages
```

### 5.3 部署方式

```
┌──────────────────────────────────────────┐
│  代码文件（.py .sh .json .css）            │
│  → git push → GitHub 仓库                 │
├──────────────────────────────────────────┤
│  产物文件（HTML 页面）                      │
│  → github_api_push.py → GitHub Pages API  │
├──────────────────────────────────────────┤
│  CDN 缓存：600s，部署后约 2-3 分钟生效      │
└──────────────────────────────────────────┘
```

### 5.4 数据生产拓扑：谁在跑什么

理解这套系统最容易搞错的一点：**绝大部分产出不在 CI 里跑，而在一台公司电脑上跑。**
`.github/workflows/` 里没有任何 `cron:` —— §9 那张调度表是 hermes agent 的
本机 crontab，不是 GitHub Actions。这是设计选择，不是遗漏。

| 类别 | 在哪跑 | 跑什么 | 依赖 |
|------|--------|--------|------|
| **A · 本机** | 公司电脑（24h 开机）上的 hermes agent | 选品趋势发现（LLM Agent）、雷达上午/下午扫描、补货管道全链路 | 机器在线；`/home/lee/` 下的 6 处绝对路径（`.env` 凭据、hermes-agent、CloakBrowser、领星产物） |
| **B · CI** | GitHub Actions | 跨境雷达每天 09:00 采集（`kj-news-radar`）；`update.yml` 仅在 push `main` 时**部署**，不产数据 | 无本机依赖 —— 三个板块里唯一一条 |
| **C · 浏览器** | 团队成员各自的浏览器 | 选品看板的产品状态 | `localStorage`；`config.json` 的 `kanban_sync.endpoint` 为空时**不跨设备同步** |

**这个拓扑决定了三件事：**

1. 团队看到的数据新鲜度 = 那台电脑最后一次跑成功的时间。首页「数据新鲜度」卡就是为此存在的（D6/D7），它显示的是**文件更新时间**，不是"系统是否健康"。
2. 跨境雷达即使本机全挂也照常更新 —— 因为它在 CI 里。
3. 看板是唯一需要多人协作的功能，而它当前**只存本地**。Worker 未部署前，A 同事标的「值得做」B 同事看不到（D5 的部署清单）。

---

## 6. 过滤规则与评分体系

### 6.1 核心过滤参数（来自 config.json）

| 参数 | 值 | 说明 |
|------|-----|------|
| 价格区间 | £5.99–12.99 | 目标价位段 |
| 最高评论数 | ≤200 | 蓝海判断标准 |
| 最低评分 | ≥3.5 | 质量底线 |
| 最大重量 | ≤200g | 轻小件物流策略 |
| 最大包装尺寸 | 30×21×6cm | FBA 小件标准件上限 |
| 最低利润率 | 20% | 目标毛利率红线 |
| 禁售关键词 | 100+ 项 | 电器/灯具/液体/侵权词等 |

### 6.2 特殊过滤规则

- **多件套装**：≥5pcs 默认排除（极薄件如贴纸/书签可豁免）
- **品牌商标**：标题关键词也可能侵权（如注册商标名），不只看产品造型
- **液体产品**：全拒（FBA 限制）
- **电器/灯具**：全拒（带电/大体积）
- **容器类（水瓶/保温杯）**：保留，不视为液体

### 6.3 评分权重体系

| 维度 | 权重 | 说明 |
|------|------|------|
| Amazon UK 直接相关 | +0.12 | 最高优先级 |
| Amazon 全球相关 | +0.08 | 亚马逊生态 |
| EU/UK 合规相关 | +0.05 | 政策法规 |
| 跨境新闻（一般） | 基准 | 普通资讯 |
| 非 Amazon 主题 | -0.15 | 非目标市场信息 |

---

## 7. 三店体系（选品定位）

| 店铺 | 定位 | 选品策略 |
|------|------|---------|
| 老店 | 稳定出单，利润贡献 | 已验证品类持续运营 |
| 测品增长店 | 主力测品，增长驱动 | 新品小批量空运测品（单次 ≤60 件） |
| 新店 | 测品启动，品类拓展 | 扩大品类覆盖，观察复购后补货 |

**物流策略：** 新品阶海小批量空运测品，复购确认后再考虑补第二批。不发海运大批量。

---

## 8. 设计原则

1. **UK 优先，不做算法完美**
   - 所有功能围绕「帮他更快看英国站 FBA 相关信息」这个目标
   - 评分体系 UK 权重最高（+0.12），非 Amazon 信息扣分（-0.15）
   - 宁可简单但相关，不要复杂但跑偏

2. **品牌平替是机会，不是禁区**
   - `forbidden_brands` 为空
   - 筛查重点在品类和关键词侵权，不在品牌名本身

3. **轻小件为基本盘**
   - 不做电器/灯具/液体（FBA 限制或体积过大）
   - 重量 ≤200g，尺寸 ≤30×21×6cm
   - 不发海运

4. **数据驱动，持续迭代**
   - 每次扫描记录历史数据（data/history/），支持趋势分析
   - PP 缓存是单日快照，30 天累计数据用专用脚本
   - 反馈学习：手动标记「不考虑」的产品自动提取特征 → 优化过滤规则

---

## 9. 定时调度（Hermes Cron）

| 时间 | 频率 | 任务 | 脚本 | 说明 |
|------|------|------|------|------|
| 08:00 | 周一/四 | 补货跟进更新 | `restock_pipeline.sh`（在 product-analysis/） | 领星 ERP → 补货分析 → 部署 |
| 08:40 | 每天(1-6) | 选品趋势发现 | LLM Agent 驱动 | 搜索趋势 → 生成趋势数据 |
| 09:10 | 每天(1-6) | 选品雷达上午扫描 | `cron_scan.sh`（在 product-radar/） | 扫描 → 过滤 → 评分 → 生成 → 部署 |
| 14:00 | 每天(1-6) | 选品雷达下午扫描 | `cron_scan.sh`（在 product-radar/） | 同上，第二次扫描 |
| 09:00 | 每天 | 跨境雷达更新 | `update_crossborder.py`（GitHub Actions） | 自动采集 30+ 资讯源 |

**调度关系：** 补货管道跨两个目录运行（product-analysis → product-radar），由 `restock_pipeline.sh` 统一编排。

---

## 10. 数据安全与公开策略

- **公开页面已脱敏**：毛利率、月销量、库存等敏感字段在公开 HTML 中隐藏
- **板块入口保留**：趋势/日历/补货/竞品等板块功能可见，仅隐藏数字
- **团队内部文档不上 GitHub**：含人名、分工、内部流程的文档通过 `.gitignore` 排除
- **Token/密码不提交**：所有凭证从 `.env` 读取

---

## 11. 关键操作规范

| 规则 | 说明 |
|------|------|
| 改数据不直接改 HTML | 改数据源 JSON → 重新生成 |
| 改样式不走内联 CSS | 走 `shared/oa-theme.css`（分层：令牌/暗色/组件/页面私有/遗留 shim） |
| 加新板块 | 只改 `oa/config.py` 的 `MODULES` 数组（v4.0 起，见 DESIGN-DECISIONS D8） |
| 结构改动 | 必须先出方案讨论，不直接改 |
| 改 `data/channels/*.json` | 先备份 |
| 跨境雷达 | 注意 `master` 分支是部署分支 |
| 补货跟进 | 不独立部署，走 `output/analysis/` 本地路径 |
| 部署验证 | 检查门户根页 iframe 内容（非仅 platform.html）；确认 `assets/portal.js` 已随产物部署 |

---

## 12. 已知坑点

| 坑 | 细节 |
|----|------|
| `is_forbidden()` 返回 `False`（非元组） | 用 `if is_forbidden():` 判断，不是 `if is_forbidden() is not None:` |
| 看板同步需要 Worker | Token 已从浏览器移除，走 Cloudflare Worker 代理。未部署时页面显示「已存本地」，见 DESIGN-DECISIONS「部署清单」 |
| 数据文件写入有塌缩保护 | 新数据为空或不足旧数据一半会被拒绝写入，见 `oa/safe_write.py` |
| 补货页需脱敏后才能部署 | `output/analysis/*.html` 来自仓库外项目、含毛利率与销量，须跑 `desensitize_analysis.py`；`update.yml` 部署前有 `--check` 门禁 |
| 节日数据有三级回退 | `/home/lee/uk-festival-planner/` → `data/festivals_data.js` → 上次产物 |
| PP 缓存是单日快照 | 30 天累计数据用 `pp_30day_export.py` |
| 选品平台过滤参数 | 从 `config.json` 读取，代码默认值需与 config 保持一致 |
| 部署验证 | CDN 缓存 600s，部署后等 2-3 分钟再验证 |
| 补货管道 | 数据源从领星 ERP 导出为主，PP 缓存重建为备选 |
| patch 工具 | 对 offset/limit 读过的文件可能不生效，同一文件避免超 3 次 patch |

---

## 13. 距离交付团队还缺什么

> 按「是不是功能缺口」分两类。写在这里是为了不用每次都重新盘一遍。
> 最后核对：2026-07-26。

### 13.1 功能缺口（只有一个）

| 缺口 | 状态 |
|------|------|
| **广告异常监控板块** | 网页上不存在。缺口描述见 §4.4，方案见 [`PROPOSAL-ads-module.md`](./PROPOSAL-ads-module.md)（待确认） |

产品目标里的另外三条 —— 给开发专员提供趋势方向与产品建议、跨境资讯/政策、
补货提醒 —— **链路都已完整、产物都在跑**，缺的只是下面这些收尾。

### 13.2 收尾项（都不是开发工作）

| 项 | 说明 | 卡在谁 |
|----|------|--------|
| **部署** | 门户重构（D1–D11）+ UI 升级（D12–D15）全部压在 `claude/oa-portal-ui-upgrade-ts4zrf`，`main` 未动，线上仍是重构前版本。`update.yml` 只在 push `main` 时触发 | 需负责人确认发布 |
| **看板同步** | `config.json` 的 `kanban_sync.endpoint` 为空，Worker 未部署 → 看板状态只存各人浏览器。**这是唯一需要协作的功能，当前不协作** | 需部署 Worker + 设 Secret，见 DESIGN-DECISIONS「部署清单」 |
| **吊销旧 GitHub Token** | 它曾暴露在浏览器 `localStorage` 里。删代码不等于凭据失效 | 需在 GitHub 后台操作 |
| **团队使用文档** | 团队会问「达标/偏低是什么意思」「为什么毛利率不是数字」「可售天数怎么算」。仓库内无面向团队的说明（`OA系统介绍-团队版.md` 刻意 gitignore） | 待写 |
| **手机端真机验证** | 已有 375px 截图验证渲染正确，但侧栏抽屉手势、iOS Safari 下 iframe 高度自适应、触屏上的粘顶表头都未在真机试过 | 待验 |

### 13.3 部署前值得先看一眼的

| 项 | 说明 |
|----|------|
| **跨境雷达会跟着变样** | `kj-news-radar/index.html` 通过 HTTP 直链引用本仓库的 `shared/oa-theme.css`。product-radar 一部署，跨境雷达的观感也变。已核对：它用到的 14 个 CSS 变量在 v6 主题里全部仍然存在（多为 shim 别名），自身 `styles.css` 仅 1 处硬编码 hex，所以不会崩 —— 但会变，且无视觉基线可比 |
| **上游 product-analysis 的三笔债** | 列表页多一个 `</div>`；16 个详情页公开展示字面量 `{fba_days}`；脱敏根因在仓库外。都改不到源码，只能在边界兜 |
| **访问控制是个决定** | Pages 全世界可见，当前靠脱敏兜底。广告板块若要展示真实花费/ACOS，这个决定就必须先做（见方案文档第 4 问） |
