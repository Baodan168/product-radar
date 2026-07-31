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
| `calc_profit.py` | 利润计算 |
| `festival_engine.py` | 节日引擎 |
| `github_api_push.py` | GitHub API 推送 |
| `oa/safe_write.py` | 数据文件写入防塌缩 |
| `oa/desensitize.py` | 补货页发布边界脱敏（毛利率/销量→档位标签） |
| `desensitize_analysis.py` | 脱敏 CLI（`--check` 供 CI 用） |
| `cloudflare-worker.js` | 抓取代理 + 看板同步代理（Token 存 Worker Secret） |
| `tests/` | pytest 回归（119 项） |
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
- ❌ **改样式不走内联CSS** — 走 shared/oa-theme.css
- ❌ **修改data/channels/*.json前必须备份**
- ❌ **改配色/字号别和结构重构放同一个分支** — 见下节，这条是拿真钱买来的
- ✅ **加新板块只改 `oa/config.py` 的 MODULES 数组**（v4.0 起从 generate_portal.py 移出，见 DESIGN-DECISIONS D8）
- ✅ **改门户交互改 `assets/portal.js`，改结构改 `templates/portal.html`**

### 视觉改动怎么分批

审美是可以被否掉的，结构不是。两者放同一条分支，否掉审美就得连结构一起退。

2026-07-31 实测过一次：v6 那轮把「把颜色从 Python 搬进 CSS 类名」（纯结构改进，
无争议）和「换成暖石灰配色」（审美决策）打包在一条分支里。配色被否时，
`generate_platform.py` 发的 `st-supplier`、`festival_engine.py` 发的 `cat-gift`
这些类名在旧样式表里根本不存在 —— 只退 CSS 会让状态徽章和品类标签变成没颜色的
裸标签。结果整条分支陪葬，连带 `tools/preflight.py` 都得单独捞回来。

所以分两批：

1. **结构批** — 颜色/字号搬进令牌、组件层改用 `var(--oa-*)`。
   验收标准是**新旧配色都能正常渲染**。这批合进去不改变任何视觉。
2. **审美批** — 只动 `:root` 里的令牌值。
   退起来就是 revert 一个 commit，不牵连任何生成器。

第二批必须**先出截图给人看过再合**（`python3 tools/snapshot.py --out .screenshots/after`，
或 `tools/skinpreview.py` 并排对比多个方向）。配色和字号这种事，
看图三十秒能定的，别用一次线上部署去试。

## 关键坑

- `scanner.py` 的 `is_forbidden()` 返回 `False`（非元组），用 `if is_forbidden():` 判断
- PP每日缓存是单日快照非月累计，30天数据用 `pp_30day_export.py`
- 选品平台过滤参数从 `config.json` 读取，代码默认值需与 config 一致
- 部署验证需检查门户根页 iframe 内容（非仅 platform.html），CDN 缓存 600s
- 看板同步走 Cloudflare Worker，浏览器不再持有 GitHub Token；未部署 Worker 时只存本地
- 改数据文件走 `oa/safe_write.py`，空数据会被拒绝写入（防止数据源挂掉时覆盖好数据）
- **补货页产物提交前必须跑 `python3 desensitize_analysis.py`**，否则部署会被 CI 拦下（毛利率/销量不能上公开页）

## 本地运行（WSL）

这个项目只能在搭它的那台机器上完整跑起来 —— 有 16 处路径绑死在本机。
云端会话（Claude Code on the web）能改仓库内的一切，但碰不到下面这些。

**环境要求：Python 3.12+**（Hermes venv 就是 3.12）。低版本历史上炸过一次：
`festival_engine.py` 曾用嵌套同类三引号 f-string，要 PEP 701 才能解析。

| 类别 | 路径 | 缺了会怎样 |
|------|------|-----------|
| Hermes 凭据 | `~/.hermes/.env`、`github_token.txt`、`scraperapi_key.txt` | 扫描抓不到数据、推不上 GitHub |
| Hermes 运行时 | `/home/lee/hermes-agent`、`hermes-venv/` | `sources/_extract_helper.py` 导入失败 |
| 补货数据源 | `~/product-analysis/gh-pages/index.html` | `transform_analysis.py` 跑不了 |
| 节日数据源 | `~/uk-festival-planner/index.html` | 自动回退到 `data/festivals_data.js`（有兜底，不会挂） |
| 抓取浏览器 | `~/.cloakbrowser/chromium-*` | BSR 抓取失败（不影响主流程） |

### ⚠️ 跑完补货管线必须补一步

```bash
python3 desensitize_analysis.py     # ← 必须！否则毛利率会重新出现在公开页
```

> 注：`transform_analysis.py` 已过时（重构后 `generate_html.py` 直接输出 radar 风格+oa-theme.css，transform 的 assert 匹配不上新结构）。列表页样式由上游保证，不再需要转换步骤。

### 其他

- `cron_scan.sh` 第一行 `source ~/.hermes/.env`，没有该文件会直接失败退出
- **别本地和云端同时改同一个分支** —— 会撞车。要么本地为主云端只读，要么反过来
- `.claude/settings.json` 已预置常用命令的权限允许列表；个人覆盖写 `.claude/settings.local.json`（不入库）

## 数据安全

- GitHub Pages 公开部署，敏感字段（毛利率/月销量/库存）已脱敏 —— 补货页由 `oa/desensitize.py` 在发布边界换成档位标签，CI 有 `--check` 门禁
- 保留板块入口和功能（趋势/日历/补货/竞品），仅隐藏数字

## 当前状态

- 3+1 混合架构已部署运行
- 选品平台 V6，门户 V4（重构分支 claude/oa-portal-redesign-9vaqif）
- **下一轮做前端 UI 升级（视觉换新 + 信息密度）— 开工前先读 `DESIGN-DECISIONS.md` 的「下一轮：前端 UI 升级（交接）」章节**
- 无暗色模式（曾加过又移除，原因见 DESIGN-DECISIONS D11）
- 每天 08:40 趋势发现 + 09:10/14:00 雷达扫描
- 周一/四 08:00 补货跟进