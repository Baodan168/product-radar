#!/usr/bin/env python3
"""本轮优化修复的回归测试：
1. _norm_weight 单位变体表驱动（kilograms 全称 bug 防回归）
2. _norm_dims 尺寸解析（cm/mm/inch/2D）
3. verify_product 验证状态标记（verified/unverified/rejected）
4. scanner 套装正则（7-Piece / 5 Set / Pack of 6 / 4-in-1 不误伤）
5. limit_theme_products 主题去重
6. scoring_engine 降权（Sponsored Ad / 未验证）
"""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from detail_verifier import _norm_weight, _norm_dims, verify_product, batch_verify  # noqa: E402
from scanner import is_forbidden  # noqa: E402
from run_scan_v2 import limit_theme_products  # noqa: E402
from scoring_engine import score_all_products  # noqa: E402

CONFIG = {
    "max_weight_g": 200,
    "max_package_dimensions": {"l_cm": 30, "w_cm": 21, "h_cm": 6},
}


# ---------- 1. 重量单位解析 ----------

@pytest.mark.parametrize("text,expected", [
    ("0.37 Kilograms", 370.0),       # 全称复数（曾经的 bug）
    ("1.2 Kilogram", 1200.0),        # 全称单数
    ("200 Grams", 200.0),            # 克全称
    ("220 g", 220.0),                # 克缩写
    ("0.2 kg", 200.0),               # 千克缩写
    ("2.5 kilos", 2500.0),           # kilo 口语
    ("7.05 oz", 199.8675),           # 盎司（临界值）
    ("0.44 lb", 199.584),            # 磅缩写（临界值）
    ("1.5 pounds", 680.4),           # 磅全称复数
    ("110 g", 110.0),
    (None, None),                    # 空数据
    ("See size chart", None),        # 无单位不解析
])
def test_norm_weight(text, expected):
    got = _norm_weight(text)
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected, abs=0.01)


# ---------- 2. 尺寸解析 ----------

@pytest.mark.parametrize("text,expected", [
    ("15 x 15 x 45 centimetres", [45.0, 15.0, 15.0]),
    ("30 × 21 × 6 cm", [30.0, 21.0, 6.0]),
    ("32*22*6cm", [32.0, 22.0, 6.0]),
    ("44.5 x 15cm", [44.5, 15.0]),          # 2D
    ("80 x 40in", [203.2, 101.6]),          # 英寸换算
    ("10 x 8 x 2 inches", [25.4, 20.3, 5.1]),  # 英寸3D
    ("450 x 300 x 60 mm", [45.0, 30.0, 6.0]),  # mm→cm
    ("no dims here", None),
    (None, None),
])
def test_norm_dims(text, expected):
    got = _norm_dims(text)
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected, abs=0.1)


# ---------- 3. verify_product 验证状态 ----------

def _fake_fetch(html):
    """monkeypatch _curl_fetch 返回固定 HTML。"""
    import detail_verifier
    detail_verifier._curl_fetch = lambda url: html


def _make_prod(asin="B0TEST123"):
    return {"asin": asin, "name": "Test Product"}


def _pad(html):
    """verify_product 要求 html 长度 ≥2000，否则视为抓取失败。"""
    return html + "<!-- " + "x" * 2500 + " -->"


def test_verify_no_data_marks_unverified(monkeypatch):
    """详情页无 Item Weight/Dimensions → data_found=False（不拦截但标记未验证）。"""
    _fake_fetch(_pad("<html><body>Product Information</body></html>"))
    ok, reason, data_found = verify_product(_make_prod(), CONFIG)
    assert ok is True
    assert data_found is False


def test_verify_overweight_rejects(monkeypatch):
    """0.37 Kilograms（370g）→ 拦截。"""
    html = """<table id="productDetails_techSpec_section_1">
      <th class="prodDetSectionEntry">Item Weight</th>
      <td class="prodDetAttrValue">0.37 Kilograms</td>
    </table>"""
    _fake_fetch(_pad(html))
    ok, reason, data_found = verify_product(_make_prod(), CONFIG)
    assert ok is False
    assert "370g" in reason
    assert data_found is True


def test_verify_oversize_rejects(monkeypatch):
    """45cm 长边 → 拦截。"""
    html = """<table><th>Item Dimensions</th>
      <td>15 x 15 x 45 centimetres</td></table>"""
    _fake_fetch(_pad(html))
    ok, reason, _ = verify_product(_make_prod(), CONFIG)
    assert ok is False
    assert "45" in reason and "cm" in reason


def test_verify_compliant_passes(monkeypatch):
    """200g 边界 + 合规尺寸 → 通过且 verified。"""
    html = """<table><th>Item Weight</th><td>200 Grams</td>
      <th>Item Dimensions</th><td>20 x 15 x 4 cm</td></table>"""
    _fake_fetch(_pad(html))
    ok, reason, data_found = verify_product(_make_prod(), CONFIG)
    assert ok is True
    assert data_found is True


def test_batch_verify_sets_status(monkeypatch):
    """batch_verify 给产品打 verify_status。"""
    htmls = {
        "B0OK1": _pad("<table><th>Item Weight</th><td>110 g</td></table>"),          # 合规
        "B0OK2": _pad("<html>no data</html>"),                                       # 无数据
        "B0BAD": _pad("<table><th>Item Dimensions</th><td>50 x 50 x 50 cm</td></table>"),  # 超标
    }
    import detail_verifier

    def fake_fetch(url):
        asin = url.rsplit("/", 1)[-1]
        return htmls.get(asin, _pad("<html></html>"))
    detail_verifier._curl_fetch = fake_fetch

    prods = [_make_prod(a) for a in ("B0OK1", "B0OK2", "B0BAD")]
    passed, rejected = batch_verify(prods, CONFIG, max_workers=3)
    by_asin = {p["asin"]: p.get("verify_status") for p in passed}
    assert by_asin["B0OK1"] == "verified"
    assert by_asin["B0OK2"] == "unverified"
    assert [p["asin"] for p in rejected] == ["B0BAD"]
    assert rejected[0]["detail_reject_reason"]


# ---------- 4. 套装过滤正则 ----------

@pytest.mark.parametrize("name,should_reject", [
    ("Compression Packing Cubes 7-Piece Set", True),     # 连字符格式（曾逃逸）
    ("5 Set Compression Packing Cubes", True),           # set 关键词（曾逃逸）
    ("Merefame Pack of 6 Money Bags", False),            # bag 豁免（轻小，合规放行）
    ("100ml Leakproof Travel Bottles 5 Pcs Set", True),  # pcs 套装
    ("GEVECORI 4-in-1 Travel Bottles", False),           # N合一不是套装
    ("4Pcs Compression Packing Cubes", False),           # 4<5 不拦
    ("10 Pcs Pirate Costume", True),
    ("2 Pack Baking Mats", False),                       # 2<5
    ("Single Packing Cube Set", False),                  # 无数值
    ("36 Pimple Patches", False),                        # 豁免 patch（但beauty类会被禁选词拦）
])
def test_set_match(name, should_reject):
    r = is_forbidden(name, "home")
    ok = r[0] if isinstance(r, tuple) else r
    assert ok == should_reject, f"{name}: {r}"


# ---------- 5. 主题去重 ----------

def test_limit_theme_products():
    def prod(asin, name, score):
        return {"asin": asin, "name": name, "score": score}

    products = [
        prod("A1", "Travel Bottles for Toiletries Leakproof", 90),
        prod("A2", "Silicone Travel Bottles 4 Pcs", 85),
        prod("A3", "100ml Travel Bottles Set", 80),
        prod("A4", "Travel Bottles Dispenser", 70),
        prod("A5", "Fadvan Travel Bottle", 60),
        prod("B1", "Pirate Treasure Coin", 95),
        prod("B2", "Pirate Costume Accessories", 88),
        prod("C1", "Dog Collar Light", 92),   # 单例主题不限制
    ]
    kept, trimmed = limit_theme_products(products, max_per_theme=3)
    kept_asins = {p["asin"] for p in kept}
    assert kept_asins == {"A1", "A2", "A3", "B1", "B2", "C1"}
    assert {p["asin"] for p in trimmed} == {"A4", "A5"}
    # 保留的是高分
    assert "A4" not in kept_asins


# ---------- 6. 评分降权 ----------

def test_sponsored_ad_penalty():
    p1 = {"asin": "S1", "name": "Sponsored Ad - 100ml Travel Bottles", "price": 8.0,
          "rating": 4.3, "reviews": 100, "sources": ["keyword"], "channel": "keyword",
          "category": "Search", "cost_breakdown": {}, "verify_status": "verified"}
    p2 = {"asin": "S2", "name": "Travel Bottles Normal Product", "price": 8.0,
          "rating": 4.3, "reviews": 100, "sources": ["keyword"], "channel": "keyword",
          "category": "Search", "cost_breakdown": {}, "verify_status": "verified"}
    out = score_all_products([p1, p2])
    s1, s2 = {p["asin"]: p for p in out}["S1"], {p["asin"]: p for p in out}["S2"]
    assert s1["score"] < s2["score"]
    assert "📢 广告位" in s1["score_breakdown"]


def test_unverified_penalty():
    p1 = {"asin": "U1", "name": "Packing Cubes", "price": 8.0,
          "rating": 4.3, "reviews": 100, "sources": ["keyword"], "channel": "keyword",
          "category": "Search", "cost_breakdown": {}, "verify_status": "unverified"}
    p2 = {"asin": "U2", "name": "Packing Cubes", "price": 8.0,
          "rating": 4.3, "reviews": 100, "sources": ["keyword"], "channel": "keyword",
          "category": "Search", "cost_breakdown": {}, "verify_status": "verified"}
    out = score_all_products([p1, p2])
    s1, s2 = {p["asin"]: p for p in out}["U1"], {p["asin"]: p for p in out}["U2"]
    assert s1["score"] < s2["score"]
    assert "⚠️ 未验证" in s1["score_breakdown"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
