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
    return True, None, data_found


# ---------- 批量验证 ----------

def batch_verify(products, config, max_workers=3, log=print):
    """3并发批量验证。返回 (passed, rejected)。

    - 跳过标题已含 g/kg/cm 尺寸信息的产品（scanner.is_forbidden 已用标题正则
      过滤，能通过即合规，无需再抓详情页）
    - 抓取失败/详情页无数据的放过（不误杀）
    - 被拦截产品写入 detail_reject_reason 字段
    """
    to_verify, skipped = [], []
    for p in products:
        name = (p.get("name") or "").lower()
        # 标题明确标注小重量/尺寸（单位 g/kg/cm）→ scanner 已处理
        if re.search(r"\d+\s*(g|kg|cm)\b", name):
            skipped.append(p)
        else:
            to_verify.append(p)

    log(f"  [7a] 详情页验证: {len(to_verify)}个待验, {len(skipped)}个标题已含尺寸跳过")
    if not to_verify:
        return products, []

    passed, rejected = [], []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(verify_product, p, config): p for p in to_verify}
        for fut in as_completed(futs):
            p = futs[fut]
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

    for p in skipped:
        # 标题已含尺寸/重量信息（scanner 已校验合规）→ 视为已验证
        p["verify_status"] = "verified"
    passed.extend(skipped)
    n_unv = sum(1 for p in passed if p.get("verify_status") == "unverified")
    log(f"  [7a] 完成: 通过 {len(passed)} | 拦截 {len(rejected)} | 未验证 {n_unv} (耗时 {time.time()-t0:.0f}s)")
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
