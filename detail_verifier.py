#!/usr/bin/env python3
"""
detail_verifier.py — Amazon 详情页重量/尺寸二次验证 (2026-07-31 重建)

在 run_scan_v2.py 第 7a 步运行：filter_products() 通过初筛的产品，
抓 Amazon 详情页 Product Information，二次验证：
  - Item Weight        ≤ config.max_weight_g (200g)
  - Item/Package Dimensions 最长边≤30cm / 次长≤21cm / 最短≤6cm

⚠️ 2026-07-31 重建背景（原版 2026-07-24 丢失）：
- 原版用 Scrapling StealthyFetcher 且从未 git commit → 文件丢失、
  run_scan_v2.py 的 [7a] 调用从未入库 → 尺寸验证静默失效约一周
- 重建版改用 sources.amazon_uk._curl_fetch（curl_cffi + GBP cookies）。
  实测：Scrapling 抓 amazon.co.uk/dp/{asin} 返回 200 + 空 body（被反爬），
  curl 通道返回 1.7MB 完整 HTML，Product Information 可正常解析。
- ⚠️ 本文件必须 git commit + git push，否则再次丢失尺寸验证会再次静默失效。
"""

import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from sources.amazon_uk import _curl_fetch


# ---------- 解析 ----------

def _norm_weight(text):
    """'220 g' / '0.2 kg' / '7.05 oz' / '0.44 lb' → 克数；无数据返回 None"""
    if not text:
        return None
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(kilograms?|kilos?|kg|grams?|g|ounces?|oz|pounds?|lb)\b",
        text, re.I,
    )
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2).lower()
    if unit in ("kg", "kilogram", "kilograms", "kilo", "kilos"):
        return val * 1000
    if unit in ("oz", "ounce", "ounces"):
        return val * 28.35
    if unit in ("lb", "pound", "pounds"):
        return val * 453.6
    return val


def _extract_attr(html, label):
    """提取 Product Information 表格中某属性值。

    兼容两种布局：
    1. 旧式 prodDetTable: <th class="prodDetSectionEntry">Item Dimensions</th>
                          <td class="prodDetAttrValue">15 x 15 x 45 centimetres</td>
    2. 新式 po-break-word: <span class="a-text-bold">Item Dimensions L x W x H</span>
                           <span class="po-break-word">15 x 15 x 45 centimetres</span>
    """
    # 旧式：th + 相邻 td
    m = re.search(
        r"<th[^>]*>\s*" + label + r"\s*</th>\s*<td[^>]*>\s*(.*?)\s*</td>",
        html, re.I | re.S,
    )
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    # 新式：label 后 300 字符内找 po-break-word span
    m = re.search(
        label + r".{0,300}?po-break-word[^>]*>\s*(.*?)\s*</span>",
        html, re.I | re.S,
    )
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return None


# 只认 "A x B" / "A x B x C" 这种真正的尺寸表达式。
# 不能用 findall 扫全串取前三个数：详情页的属性值常带尾巴（"25 x 20 cm; 15 g"），
# 那个 15 是克重，会被当成 15cm 的第三维，于是 2D 商品按 3D 判、15>6 被误杀。
_DIM_EXPR = re.compile(
    r"(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)"
    r"(?:\s*[x×*]\s*(\d+(?:\.\d+)?))?",
    re.I,
)
# 单位必须按词边界认。曾经写成 `"in" in text.lower()`，结果命中的是材质词里的 in ——
# Stainless / Linen / Printed 全中，尺寸被乘 2.54。"30 x 21 x 6 cm; Stainless Steel"
# 这种正好卡在限值上的合格品会被算成 76x53x15 毙掉，而限值就是 30x21x6，
# 越贴近限值的合格品越容易中招。
_UNIT_INCH = re.compile(r'(?:\binch(?:es)?\b|\bins?\b|["″])', re.I)
_UNIT_MM = re.compile(r"\b(?:mm|millimet(?:er|re)s?)\b", re.I)


def _norm_dims(text):
    """'15 x 15 x 45 centimetres' / '44.5 x 15cm' / '80 x 40in' → cm 数值列表(降序)。

    无法解析出尺寸表达式时返回 None（调用方据此判为「未验证」，不拦截）。
    """
    if not text:
        return None
    m = _DIM_EXPR.search(text)
    if not m:
        return None
    vals = [float(g) for g in m.groups() if g is not None]

    # 单位只看尺寸表达式后面那一小段，避免被属性值尾巴上的材质、克重干扰
    tail = text[m.end():m.end() + 24]
    if _UNIT_INCH.search(tail):
        vals = [round(v * 2.54, 1) for v in vals]
    elif _UNIT_MM.search(tail):
        vals = [round(v / 10, 1) for v in vals]
    else:
        # 无单位时数值 > 200 大概率是 mm → cm
        vals = [v / 10 if v > 200 else v for v in vals]
    return sorted(vals, reverse=True)


# ---------- 单个产品验证 ----------

def verify_product(p, config):
    """验证单个产品。返回 (passed: bool, reason: str|None, data_found: bool)。

    data_found=False 表示详情页无重量/尺寸数据（未验证，不拦截但调用方应标记）。
    抓取失败 → data_found=False（不误杀）。
    """
    asin = p.get("asin")
    if not asin:
        return True, None, False
    max_w = config.get("max_weight_g", 200)
    md = config.get("max_package_dimensions", {"l_cm": 30, "w_cm": 21, "h_cm": 6})
    max_l, max_wd, max_h = md["l_cm"], md["w_cm"], md["h_cm"]

    try:
        html = _curl_fetch(f"https://www.amazon.co.uk/dp/{asin}")
    except Exception:
        return True, None, False  # 抓取失败不误杀
    if not html or len(html) < 2000:
        return True, None, False

    reasons = []
    data_found = False

    # 重量
    wt_text = _extract_attr(html, "Item Weight") or _extract_attr(html, "Item weight")
    if wt_text:
        data_found = True
        grams = _norm_weight(wt_text)
        if grams is not None and grams > max_w:
            reasons.append(f"重量 {grams:.0f}g (限{max_w}g)")

    # 尺寸
    dim_text = (
        _extract_attr(html, "Item Dimensions")
        or _extract_attr(html, "Item dimensions")
        or _extract_attr(html, "Package Dimensions")
        or _extract_attr(html, "Package dimensions")
    )
    if dim_text:
        data_found = True
        dims = _norm_dims(dim_text)
        if dims and len(dims) >= 3:
            if dims[0] > max_l or dims[1] > max_wd or dims[2] > max_h:
                reasons.append(
                    f"包装尺寸 {dims[0]:.0f}x{dims[1]:.0f}x{dims[2]:.0f}cm "
                    f"(限{max_l}x{max_wd}x{max_h}cm)"
                )
        elif dims and len(dims) == 2:
            # 2D（泡沫轴/瑜伽垫类）：长边≤30 且短边≤21
            if dims[0] > max_l or dims[1] > max_wd:
                reasons.append(
                    f"包装尺寸(2D) {dims[0]:.0f}x{dims[1]:.0f}cm "
                    f"(限{max_l}x{max_wd}x{max_h}cm)"
                )

    if reasons:
        return False, "; ".join(reasons), data_found

    # ⚠️ 2026-08-10 修复: Amazon 反爬"静默降级"检测。批量请求详情页时 Amazon
    # 会返回精简版 HTML（实测 419KB~944KB vs 正常 150万+ 字节），不含 Product
    # Information 表（prodDetTable/po-break-word）。此时解析不到数据 ≠ 卖家真
    # 没填数据，标记 _degraded 由 batch_verify 重试一次（KAYMAN 泡沫轴案例：
    # 08:50 降级页漏网，重抓完整页即拦截 45×15×15cm）。
    if not data_found and "prodDetTable" not in html and "po-break-word" not in html:
        p["_degraded"] = True
    return True, None, data_found


# ---------- 批量验证 ----------

def batch_verify(products, config, max_workers=3, time_budget=240, log=print):
    """3并发批量验证。返回 (passed, rejected)。

    - 跳过标题已含 g/kg/cm 尺寸信息的产品（scanner.is_forbidden 已用标题正则
      过滤，能通过即合规，无需再抓详情页）
    - 抓取失败/详情页无数据的放过（不误杀）
    - 被拦截产品写入 detail_reject_reason 字段
    - ⚠️ time_budget（秒）：[7a] 总时间预算。超过预算后未完成的产品按
      unverified 放行（不拦截），防止 Amazon 抓取变慢时拖垮整个扫描
      （2026-08-07：37个待验×最坏2分钟/个，600s scan 预算被 [7a] 吃光 → cron 超时）
    """
    to_verify, skipped = [], []
    for p in products:
        name = (p.get("name") or "").lower()
        # ⚠️ 2026-08-04 修复：跳过条件收紧为「标题尺寸明确合规」。
        # 旧逻辑「标题含 g/kg/cm 就跳过」建立在错误假设上——scanner 只校验
        # 3D 尺寸（32x22x6cm），2D 尺寸（137x274cm 桌布）scanner 不匹配，
        # 却被跳过规则当作"已校验"放行 → 桌布/可折叠大件漏网。
        # 折叠类产品（桌布/雨披）标题尺寸是展开尺寸，不代表包装尺寸，
        # 必须以详情页 Package Dimensions 为准。只有标题尺寸所有维度
        # ≤ 限值（scanner 已校验且合规）才跳过；含 2D 尺寸/超标/无法判断
        # 的标题一律抓详情页验证。
        max_w = config.get("max_weight_g", 200)
        md = config.get("max_package_dimensions", {"l_cm": 30, "w_cm": 21, "h_cm": 6})
        _max_l, _max_w, _max_h = md["l_cm"], md["w_cm"], md["h_cm"]
        # 3D 尺寸（scanner 同款正则）：32x22x6cm / 32×22×6 cm / 32*22*6mm
        m3d = re.search(
            r"(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*(?:cm|mm)?",
            name,
        )
        if m3d:
            d1, d2, d3 = (float(m3d.group(i)) for i in (1, 2, 3))
            # mm 值 >200 视为 cm（与 scanner 一致）
            if d1 > 200: d1 /= 10
            if d2 > 200: d2 /= 10
            if d3 > 200: d3 /= 10
            dims = sorted([d1, d2, d3], reverse=True)
            # 只有全部维度 ≤ 限值才信任标题（scanner 已验证合规）
            if dims[0] <= _max_l and dims[1] <= _max_w and dims[2] <= _max_h:
                skipped.append(p)
            else:
                to_verify.append(p)  # 标题尺寸超标 → 详情页复核（含2D展开尺寸误报场景）
        else:
            to_verify.append(p)  # 无3D尺寸信息（含2D尺寸如137x274cm）→ 必须详情页验证

    log(f"  [7a] 详情页验证: {len(to_verify)}个待验, {len(skipped)}个标题已含尺寸跳过")
    if not to_verify:
        return products, []

    passed, rejected = [], []
    t0 = time.time()
    ex = ThreadPoolExecutor(max_workers=max_workers)
    futs = {ex.submit(verify_product, p, config): p for p in to_verify}
    remaining = set(futs)
    budget_hit = False
    try:
        for fut in as_completed(futs):
            p = futs[fut]
            remaining.discard(fut)
            try:
                ok, reason, data_found = fut.result()
            except Exception:
                ok, reason, data_found = True, None, False
            if ok:
                # verify_status: verified=详情页有数据且合规 / unverified=无数据(降权展示)
                p["verify_status"] = "verified" if data_found else "unverified"
                passed.append(p)
            else:
                p["verify_status"] = "rejected"
                p["detail_reject_reason"] = reason
                rejected.append(p)
                log(f"    ❌ {p.get('name', '')[:45]} → {reason}")
            # 总时间预算：超时后剩余未完成产品按 unverified 放行（不误杀、不拖垮扫描）
            if remaining and time.time() - t0 > time_budget:
                for p2 in (futs[f2] for f2 in remaining):
                    p2["verify_status"] = "unverified"
                    passed.append(p2)
                log(f"  ⚠️ [7a] 超过 {time_budget}s 预算，剩余 {len(remaining)} 个未验证按 unverified 放行")
                budget_hit = True
                break
    finally:
        # ⚠️ 不能等线程池：shutdown(wait=True) 会等已在跑的慢任务（最坏2分钟/个）跑完，
        #    让 time_budget 形同虚设。cancel_futures=True 取消未启动任务，立即返回。
        ex.shutdown(wait=False, cancel_futures=True)
    if budget_hit:
        log(f"  [7a] 完成(截断): 通过 {len(passed)} | 拦截 {len(rejected)} | 预算内未验完 (总耗时 {time.time()-t0:.0f}s)")

    for p in skipped:
        # 标题已含尺寸/重量信息（scanner 已校验合规）→ 视为已验证
        p["verify_status"] = "verified"
    passed.extend(skipped)
    n_unv = sum(1 for p in passed if p.get("verify_status") == "unverified")
    log(f"  [7a] 完成: 通过 {len(passed)} | 拦截 {len(rejected)} | 未验证 {n_unv} (耗时 {time.time()-t0:.0f}s)")

    # ⚠️ 2026-08-10 修复: 降级页重试。首轮 unverified 且页面疑似降级（无 Product
    # Information 表）的产品重试 1 次——反爬降级是瞬态的，二次抓取常能拿到完整页。
    # 实例: 08:50 扫描 37/37 unverified（419KB~944KB 精简页），KAYMAN 泡沫轴
    # （真实包装 45×15×15cm）漏网；重抓完整页即拦截。
    retry_list = [p for p in passed if p.get("verify_status") == "unverified" and p.pop("_degraded", False)]
    if retry_list:
        log(f"  [7a] 重试 {len(retry_list)} 个降级页产品（首轮 HTML 不含 Product Information 表）")
        for idx, p in enumerate(retry_list):
            if time.time() - t0 > time_budget:
                log(f"  ⚠️ [7a] 重试阶段超预算，剩余 {len(retry_list)-idx} 个保持 unverified")
                break
            try:
                ok, reason, data_found = verify_product(p, config)
            except Exception:
                ok, reason, data_found = True, None, False
            if not ok:
                p["verify_status"] = "rejected"
                p["detail_reject_reason"] = reason
                passed.remove(p)
                rejected.append(p)
                log(f"    ❌ [重试] {p.get('name', '')[:45]} → {reason}")
            elif data_found:
                p["verify_status"] = "verified"
        n_unv = sum(1 for p in passed if p.get("verify_status") == "unverified")
        log(f"  [7a] 重试后: 通过 {len(passed)} | 拦截 {len(rejected)} | 未验证 {n_unv}")
    return passed, rejected


if __name__ == "__main__":
    # 独立测试：验证 channels JSON 中的产品
    import json

    config = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
    f = sys.argv[1] if len(sys.argv) > 1 else "data/channels/2026-07-31_0911.json"
    products = json.loads((BASE / f).read_text(encoding="utf-8")).get("products", [])
    print(f"加载 {len(products)} 个产品: {f}")
    passed, rejected = batch_verify(products, config)
    print(f"\n结果: 通过 {len(passed)} | 拦截 {len(rejected)}")
    for r in rejected:
        print(f"  ❌ {r.get('name', '')[:50]} | {r.get('detail_reject_reason')}")
