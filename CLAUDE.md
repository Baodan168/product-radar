# Product Radar — Amazon UK 选品运营 OA

## 一句话定位

Amazon UK 三店（322·007·027）的选品与运营门户，3+1 混合架构：product-radar 仓库管门户/选品平台/补货跟进三个核心板块，kj-news-radar 独立仓库管跨境雷达。

## 怎么跑起来

```bash
# 扫描 → 生成 → 部署
cd /home/lee/product-radar
bash cron_scan.sh              # 扫描+过滤+评分+生成HTML+推送GitHub
python3 generate_platform.py   # 生成选品平台 HTML
python3 generate_portal.py     # 生成门户页面
python3 github_api_push.py "msg"  # 推送到 GitHub

# 本地预览
python3 -m http.server 8080    # 访问 http://localhost:8080/output/
```

## 关键文件

| 文件 | 作用 |
|------|------|
| `ARCHITECTURE.md` | 系统架构文档（数据流/设计原则/调度/运维） |
| `PROJECT-VISION.md` | 产品愿景文档（项目目标/选品哲学/设计理念） |
| `DESIGN-DECISIONS.md` | 重构决策记录（每条决策的选择/理由/代价/已知限制） |
| `PROPOSAL-ads-module.md` | **广告异常监控板块方案（待确认，未实施）** |
| `oa/config.py` | **门户板块配置（加新板块改这里）** |
| `oa/urls.py` | URL 协议+主机白名单 |
| `oa/render.py` | 模板装配 + 分语境转义（html/attr/js/url） |
| `templates/` `assets/` | 门户与平台的 HTML 模板、JS 资源 |
| `config.json` | 主配置（价格区间/重量/尺寸/禁售词） |
| `cron_scan.sh` | 定时扫描入口 |
| `run_scan_v2.py` | 扫描引擎 |
| `scanner.py` | 产品过滤规则（⚠️ is_forbidden()返回False非元组） |
| `generate_platform.py` | 选品平台生成器 V6（薄壳，模板见 templates/platform.html） |
| `generate_portal.py` | 门户生成器 V4（薄壳，配置见 oa/config.py） |
| `tools/snapshot.py` | 视觉回归截图（改样式前后各跑一次） |
| `tools/skinpreview.py` | 换肤方向对比（不改主题表就能预览） |
| `calc_profit.py` | 利润计算 |
| `festival_engine.py` | 节日引擎 |
| `github_api_push.py` | GitHub API 推送 |
| `oa/safe_write.py` | 数据文件写入防塌缩 |
| `oa/desensitize.py` | 补货页发布边界脱敏（毛利率/销量→档位标签） |
| `desensitize_analysis.py` | 脱敏 CLI（`--check` 供 CI 用） |
| `cloudflare-worker.js` | 抓取代理 + 看板同步代理（Token 存 Worker Secret） |
| `tests/` | pytest 回归（123 项） |
| `data/channels/` | 扫描数据（产品JSON） |
| `data/discovery/` | 趋势发现数据 |
| `output/` | 生成的 HTML |
| `shared/` | 共享设计系统（oa-theme.css） |

## 架构决策（3+1 混合方案C）

```
门户 (generate_portal.py) → iframe 聚合三模块
  ├─ 📡 跨境雷达 (kj-news-radar 独立仓库，iframe直链)
  ├─ 🎯 选品平台 (本仓库，4 Tab)
  └─ 📦 补货跟进 (本仓库，output/analysis/)
```

- 三个核心板块同在 product-radar 仓库，共享数据源 + oa-theme.css 统一维护
- 跨境雷达独立仓库（数据源不同，link引用oa-theme.css）
- 不拆补货跟进独立部署

## 操作禁忌

- ❌ **结构改动必须先讨论** — 板块独立/合并/URL变更必须先出方案再执行，不能直接改
- ❌ **改数据不直接改HTML** — 改数据源JSON，重新生成
- ❌ **改样式不走内联CSS** — 走 shared/oa-theme.css。颜色**只能**写在 `:root` 令牌里，
  组件层 / 模板 / JS / 生成器里出现任何 `#hex` 或 `rgba()` 都会被 `tests/test_theme.py` 拦下（见 D13）
- ❌ **修改data/channels/*.json前必须备份**
- ✅ **加新板块只改 `oa/config.py` 的 MODULES 数组**（v4.0 起从 generate_portal.py 移出，见 DESIGN-DECISIONS D8）
- ✅ **改门户交互改 `assets/portal.js`，改结构改 `templates/portal.html`**

## 关键坑

- `scanner.py` 的 `is_forbidden()` 返回 `False`（非元组），用 `if is_forbidden():` 判断
- PP每日缓存是单日快照非月累计，30天数据用 `pp_30day_export.py`
- 选品平台过滤参数从 `config.json` 读取，代码默认值需与 config 一致
- 部署验证需检查门户根页 iframe 内容（非仅 platform.html），CDN 缓存 600s
- 看板同步走 Cloudflare Worker，浏览器不再持有 GitHub Token；未部署 Worker 时只存本地
- 改数据文件走 `oa/safe_write.py`，空数据会被拒绝写入（防止数据源挂掉时覆盖好数据）
- **补货页产物提交前必须跑 `python3 desensitize_analysis.py`**，否则部署会被 CI 拦下（毛利率/销量不能上公开页）

## 数据安全

- GitHub Pages 公开部署，敏感字段（毛利率/月销量/库存）已脱敏 —— 补货页由 `oa/desensitize.py` 在发布边界换成档位标签，CI 有 `--check` 门禁
- 保留板块入口和功能（趋势/日历/补货/竞品），仅隐藏数字

## 当前状态

- 3+1 混合架构已跑通；**门户重构与 UI 升级尚未部署**（都在 claude/oa-portal-ui-upgrade-ts4zrf，main 未动）
- **唯一功能缺口：广告异常监控板块未建**（见 ARCHITECTURE.md §4.4 + PROPOSAL-ads-module.md）
- 距离交付团队还缺什么：见 **ARCHITECTURE.md §13**（不用每次重新盘）
- 选品平台 V6，门户 V4，设计系统 **v6「暖石灰」**（分支 claude/oa-portal-ui-upgrade-ts4zrf）
- 设计原则：**颜色只用来表意** —— 外壳走中性灰阶、主操作色是墨色，
  饱和色只留给语义（红=紧急/琥珀=观察/绿=健康）和四个数据源。详见 DESIGN-DECISIONS D12
- 配色是**暖石灰**低饱和路线，三层平面靠明度分层：侧栏 #f1efeb → 内容区 #f7f6f4 → 卡片白。
  **全站无深色块**（侧栏曾是近黑，v6 改浅，见 D15）
- 换肤入口：改 `shared/oa-theme.css` 顶部 `:root` 的令牌值，全站生效（这个前提由 4 条测试守着，见 D13）
- 无暗色模式（曾加过又移除，原因见 DESIGN-DECISIONS D11）
- 每天 08:40 趋势发现 + 09:10/14:00 雷达扫描
- 周一/四 08:00 补货跟进