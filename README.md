# Product Radar — Amazon UK 选品运营 OA

多源产品发现与运营门户系统，聚合 Amazon UK 趋势扫描、跨境情报、补货监控、节日选品，为 Amazon UK 三店（322·007·027）提供一站式运营工具。

> **架构：** 3+1 混合方案 — 门户/选品平台/补货跟进同仓库，跨境雷达独立仓库（iframe 直链）
> **架构文档：** [ARCHITECTURE.md](./ARCHITECTURE.md) — 系统全景、数据流、设计原则、调度说明
> **访问：** [Baodan168.github.io/product-radar](https://Baodan168.github.io/product-radar/)

## 三大板块

| 板块 | 定位 | 数据源 | 更新频率 |
|------|------|--------|---------|
| 🎯 **选品平台** | 趋势发现 + 雷达扫描 + 节日选品 + 选品看板 | Amazon UK / TikTok / 1688 / Google Trends | 每天 08:40 / 09:10 / 14:00 |
| 📡 **跨境雷达** | 24h 跨境电商情报聚合（独立仓库） | 30+ 中文跨境资讯源 | 每天 09:00 |
| 📦 **补货跟进** | 库存监控 + 补货建议 | 领星ERP PP缓存 | 周一/四 08:00 |

## 快速开始

```bash
# 扫描 + 生成 + 部署
cd /home/lee/product-radar
bash cron_scan.sh              # 全流程
python3 generate_platform.py   # 仅生成选品平台
python3 generate_portal.py     # 仅生成门户
python3 github_api_push.py "msg"  # 推送到 GitHub

# 本地预览
python3 -m http.server 8080
# 访问 http://localhost:8080/output/
```

## 配置

主配置文件 `config.json`，核心参数：

| 参数 | 值 | 说明 |
|------|-----|------|
| `price_range` | £5.99–12.99 | 选品价格区间 |
| `max_weight_g` | 200g | 最大重量 |
| `max_package_dimensions` | 30×21×6cm | 最大包装尺寸 |
| `min_profit_margin` | 20% | 最低利润率 |
| `max_reviews` | 200 | 蓝海评论数阈值 |
| `forbidden_keywords` | 100+ 项 | 禁售关键词 |

## 目录结构

```
product-radar/
├── config.json              # 主配置
├── cron_scan.sh             # 定时扫描入口
├── run_scan_v2.py           # 扫描引擎
├── generate_platform.py     # 选品平台生成器 V5
├── generate_portal.py       # 门户生成器 V3
├── scanner.py               # 产品过滤规则
├── scoring_engine.py        # 评分引擎
├── calc_profit.py           # 利润计算
├── festival_engine.py       # 节日引擎
├── github_api_push.py       # GitHub API 推送
├── CLAUDE.md                # Agent 规则文件
├── data/                    # 扫描数据
│   ├── channels/            # 产品扫描结果
│   ├── discovery/           # 趋势发现数据
│   └── competitor_analysis/ # 竞品分析
├── output/                  # 生成的 HTML
│   ├── index.html           # 门户页
│   ├── platform.html        # 选品平台
│   └── analysis/            # 补货跟进页
└── shared/                  # 共享设计系统
    └── oa-theme.css         # 统一样式
```

## 部署

- **源文件**（.py/.sh/.json/.md）：git push 部署
- **产物文件**（HTML）：GitHub API 直接推送
- **CDN 缓存**：600s，部署后等 2-3 分钟

## 数据安全

公开部署，敏感字段（毛利率/月销量/库存）已脱敏。

## License

MIT