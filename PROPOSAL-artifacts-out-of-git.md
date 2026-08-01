# 方案：产物出库，生成挪进 CI

> 状态：**待拍板，未实施。**
> 这是结构改动，按 CLAUDE.md「结构改动必须先讨论」的规矩先出方案。
> 相关：[`PROPOSAL-agent-collab.md`](./PROPOSAL-agent-collab.md)（更早的版本，本文是它的收窄与具体化）

## 一句话

`output/*.html` 不再入库，改由 CI 在部署时生成 —— 消掉「三方写同一个 main」这个反复收税的结构。

---

## 问题是什么

`output/` 现在有 37 个文件、3.9M 入库，由三方写：

| 谁 | 什么时候写 | 写什么 |
|---|---|---|
| hermes | 每次 cron（08:40 / 09:10 / 14:00） | `index.html`、`platform.html`、`data/*.js` |
| 补货管道 | 每周一/四 08:00 | `analysis/*.html` |
| 人（生产机 / 云端） | 改代码时 | 上面全部，只要跑了生成器 |

产物是「代码 × 数据」的函数，而代码和数据由不同的人在不同的时间推。
于是**每一次合并都要单独处理产物的时序**，这个税每次都要交。

### 2026-07-31 当天实际交的税

1. **快进合并会让线上数据倒退。** UI 升级分支的 `index.html` 是 10:51 的快照，
   `main` 上是 15:09 的（hermes 中间跑过一次）。合并是快进，不重新生成就会把
   4 小时前的数据推上线。当天是靠合并前手工重新生成才避开的。

2. **改方向时必须掐掉正在跑的 cron。** 当天两次要调整发布方向，两次都得中途
   停掉 `cron_scan.sh` —— 因为它跑完会把新代码生成的产物推上 main，正好盖在
   回退之上，形成「新产物 + 旧代码」的混合体。**完整链路因此一次都没跑通。**

3. **`DEPLOY-CHECKLIST` 的验收项里专门有一条教人认混合体**
   （「如果颜色是新的但布局是旧的……」）。需要写这种条目本身就是信号：
   这个失败模式常见到值得写进清单。

## 改成什么样

```
main 只有代码和数据
      │
      ├─ push 触发 update.yml
      │     ├─ desensitize --check          （门禁，不变）
      │     ├─ python3 generate_platform.py  ← 新增：CI 里生成
      │     ├─ python3 generate_portal.py    ← 新增
      │     └─ 部署到 Pages
      │
      └─ hermes cron 只推 data/，不再推 output/
```

改动清单：

| 文件 | 改什么 |
|---|---|
| `.gitignore` | 加 `output/`（`output/analysis/` 单独讨论，见下） |
| `git rm -r --cached output/` | 从索引移除，保留本地文件 |
| `.github/workflows/update.yml` | 部署前跑两个生成器 |
| `cron_scan.sh` | Step 4 只推 `data/` 和 `status.json` |
| `github_api_push.py` | 推送白名单去掉 `output/*` |
| `~/product-analysis/restock_pipeline.sh` | 见下面「补货页怎么办」 |

## 换来什么

- **合并不再需要考虑产物时序** —— 今天那两个税一次性消掉
- **回退变干净** —— `git revert` 代码，CI 自然生成对应产物，不会留混合体
- **仓库瘦 3.9M**，且不再有每天几十次的产物 diff 噪音
- **hermes 和人的写入范围零重叠** —— hermes 只写 `data/`，人只写代码

## 代价与风险

**1. 回退的语义变了（最要紧的一条）**

现在 `git revert` 那个合并 commit，产物跟着一起退，是原子的。
改完之后 revert 只退代码，产物要等 CI 重新生成 —— 中间有 2~3 分钟窗口
线上还是旧产物。可以接受，但**必须在 DEPLOY-CHECKLIST 里改掉回退那节**，
否则按老流程操作的人会以为退完就完事了。

**2. CI 里生成不出来怎么办**

生成器依赖本机路径：`~/uk-festival-planner/index.html`（节日数据源，
有兜底回退到 `data/festivals_data.js`）、`~/product-analysis/gh-pages/`（补货）。
**CI 里这些都没有。** 所以：

- 节日：走现有兜底，需确认 `data/festivals_data.js` 一直是最新的（现在是 hermes 顺带更新的，要改成显式提交）
- 补货：见下

这一条是**方案能不能成立的关键**，实施前必须先在 CI 上跑通一次生成，
确认产出和本机一致。建议先开个 PR 只加生成步骤、不删 `output/`，
对比两边产物 diff 为空，再做删除那一步。

**3. 补货页怎么办**

`output/analysis/` 由仓库外的 `~/product-analysis/` 产出，CI 拿不到源数据。
两个选项：

- **A（省事）**：`output/analysis/` 继续入库，只把 `index.html` / `platform.html` / `data/*.js` 出库。
  收益拿到大部分（那三个才是每天churn的），补货页每周只变两次，冲突概率低。
- **B（彻底）**：补货管道改成推 JSON 数据到本仓库，HTML 也在 CI 生成。
  更干净，但要动仓库外的管道，工作量大得多。

**建议先做 A。** B 留到补货管道本身要重构时再一起做。

**4. 本地预览会变麻烦**

`python3 -m http.server 8080` 看 `output/` 的习惯不变（本地文件还在，只是不入库），
但新克隆的仓库需要先跑一次生成器才有东西看。在 README 里写一行即可。

## 分几步走

1. **只加不删**：`update.yml` 里加生成步骤，`output/` 仍入库。跑一次，对比 CI 产物和入库产物 diff 是否为空。**这一步能验证 CI 环境够不够。**
2. diff 为空后，`git rm -r --cached` 那三类文件 + 改 `.gitignore`
3. 改 `cron_scan.sh` 和 `github_api_push.py` 的推送范围
4. 改 `DEPLOY-CHECKLIST.md` 的回退那节
5. 观察一周的 cron

第 1 步是只读的验证，随时可以停。**如果第 1 步发现 CI 里生成不出来，
整个方案就不成立**，那就退回到 `PROPOSAL-agent-collab.md` 里说的其他路子。

## 需要你定的

- **A 还是 B**（补货页出不出库）—— 我的建议是 A
- **要不要接受回退多出 2~3 分钟窗口** —— 这是唯一实质性的能力损失
- 什么时候做。这个改动期间 hermes 的 cron 最好停一轮，避免中途撞车
