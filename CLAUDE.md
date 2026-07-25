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
| `config.json` | 主配置（价格区间/重量/尺寸/禁售词） |
| `cron_scan.sh` | 定时扫描入口 |
| `run_scan_v2.py` | 扫描引擎 |
| `scanner.py` | 产品过滤规则（⚠️ is_forbidden()返回False非元组） |
| `generate_platform.py` | 选品平台生成器 V5（~1146行，职责重） |
| `generate_portal.py` | 门户生成器 V3（MODULES数组配置化） |
| `calc_profit.py` | 利润计算 |
| `festival_engine.py` | 节日引擎 |
| `github_api_push.py` | GitHub API 推送 |
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
- ✅ **加新板块只改 generate_portal.py 的 MODULES 数组**

## 关键坑

- `scanner.py` 的 `is_forbidden()` 返回 `False`（非元组），用 `if is_forbidden():` 判断
- PP每日缓存是单日快照非月累计，30天数据用 `pp_30day_export.py`
- 选品平台过滤参数从 `config.json` 读取，代码默认值需与 config 一致
- 部署验证需检查门户根页 iframe 内容（非仅 platform.html），CDN 缓存 600s

## 数据安全

- GitHub Pages 公开部署，敏感字段（毛利率/月销量/库存）已脱敏
- 保留板块入口和功能（趋势/日历/补货/竞品），仅隐藏数字

## 当前状态

- 3+1 混合架构已部署运行
- 选品平台 V5，门户 V3
- 每天 08:40 趋势发现 + 09:10/14:00 雷达扫描
- 周一/四 08:00 补货跟进