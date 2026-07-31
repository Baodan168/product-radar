#!/usr/bin/env python3
"""Product Radar - Core utilities
Provides: is_forbidden (keyword/category filter), calc_profit (margin calculator).
Scoring is handled by scoring_engine.py.
"""
import json, os, sys, re
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent
CONFIG = json.loads((BASE / "config.json").read_text())


def load_history(days=7):
    """Load recent snapshots for trend detection."""
    hist_dir = BASE / CONFIG["output"]["history_dir"]
    history = {}
    cutoff = datetime.now() - timedelta(days=days)
    for f in sorted(hist_dir.glob("*.json")):
        try:
            d = datetime.strptime(f.stem, "%Y-%m-%d")
            if d >= cutoff:
                data = json.loads(f.read_text())
                for item in data:
                    key = item.get("asin") or item.get("name", "").lower().strip()
                    if key not in history:
                        history[key] = []
                    history[key].append({
                        "date": f.stem,
                        "rank": item.get("rank"),
                        "price": item.get("price"),
                        "reviews": item.get("reviews"),
                        "score": item.get("score", 0)
                    })
        except (ValueError, json.JSONDecodeError):
            continue
    return history


def is_forbidden(name, category=""):
    """Check if product matches forbidden categories."""
    text = (name + " " + category).lower()

    # --- Shared keyword sets ---
    PET_KEYWORDS = {'cat', 'dog', 'pet', 'kitten', 'puppy', 'ferret', 'rabbit', 'hamster', 'catnip', 'silvervine'}
    PARTY_KEYWORDS = {'party', 'decoration', 'costume', 'pirate', 'halloween', 'christmas', 'birthday', 'fancy dress', 'bachelorette', 'wedding'}
    PARTY_EXEMPT_KW = {'kids', 'dress', 'shirt', 'children', 'trousers'}  # clothing keywords exempted when party context

    has_party = any(kw in text for kw in PARTY_KEYWORDS)

    # --- Special handling: "toy" ---
    has_toy = bool(re.search(r'(?<![a-z])toy(?:s)?(?![a-z])', text))
    if has_toy:
        has_pet = any(re.search(r'(?<![a-z])' + re.escape(kw) + r'(?![a-z])', text) for kw in PET_KEYWORDS)
        if not has_pet and not has_party:
            return True, "toy (非宠物/节日)"

    # --- Oversized bathroom products (too large for FBA small standard) ---
    OVERSIZE_HINTS = {'large capacity', 'extra large', '6 slot', '6 slots', '7 slot', '7 slots',
                      '8 slot', '8 slots', '9 slot', '9 slots', '10 slot', '10 slots',
                      'extra tall', 'super large', 'jumbo'}
    BATHROOM_HINTS = {'toothbrush', 'bathroom', 'shower', 'holder', 'organiser', 'organizer'}
    is_oversize_bathroom = (
        any(kw in text for kw in OVERSIZE_HINTS) and
        any(kw in text for kw in BATHROOM_HINTS)
    )

    # --- Main keyword loop ---
    for kw in CONFIG["forbidden_keywords"]:
        if kw == "toy":
            continue
        # Party exemption: skip clothing keywords for party/costume items
        if kw in PARTY_EXEMPT_KW and has_party:
            continue
        # Oversize bathroom filter
        if kw == "electric" and is_oversize_bathroom:
            return True, f"oversize: {kw} + 体积过大"
        # Word-boundary matching
        pattern = r'(?<![a-z])' + re.escape(kw.strip()) + r'(?![a-z])' if kw.strip().isalpha() else re.escape(kw)
        if re.search(pattern, text):
            return True, kw

    # --- Volume/weight detection ---
    max_ml = 0
    max_l = 0
    max_kg = CONFIG.get("max_weight_g", 200) / 1000
    CONTAINER_KEYWORDS = {'bottle', 'flask', 'tumbler', 'jug', 'carafe', 'pitcher', 'thermos', 'canteen', 'watering can'}
    is_container = any(kw in text for kw in CONTAINER_KEYWORDS)

    # --- Packaging dimension detection ---
    MAX_DIM = CONFIG.get("max_package_dimensions", {"l_cm": 32, "w_cm": 22, "h_cm": 6})
    MAX_L = MAX_DIM["l_cm"]
    MAX_W = MAX_DIM["w_cm"]
    MAX_H = MAX_DIM["h_cm"]
    # Match patterns like "32x22x6cm", "32×22×6 cm", "30 x 20 x 10 cm", "32*22*6cm"
    dim_match = re.search(
        r'(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*(?:cm|mm)?',
        text
    )
    if dim_match:
        d1, d2, d3 = float(dim_match.group(1)), float(dim_match.group(2)), float(dim_match.group(3))
        # Assume mm values > 200 are likely mm not cm
        if d1 > 200: d1 /= 10
        if d2 > 200: d2 /= 10
        if d3 > 200: d3 /= 10
        dims = sorted([d1, d2, d3], reverse=True)
        if dims[0] > MAX_L or dims[1] > MAX_W or dims[2] > MAX_H:
            return True, f"包装尺寸 {d1:.0f}x{d2:.0f}x{d3:.0f}cm (限{MAX_L}x{MAX_W}x{MAX_H}cm)"

    # --- OVERSIZE HINTS (products likely too large for small standard) ---
    OVERSIZE_KEYWORDS = {
        'large capacity', 'extra large', 'super large', 'jumbo', 'x-large', 'xxl',
        'giant', 'massive', 'oversized', '6 slot', '6 slots', '7 slot', '7 slots',
        '8 slot', '8 slots', '9 slot', '9 slots', '10 slot', '10 slots',
    }
    if any(kw in text for kw in OVERSIZE_KEYWORDS):
        return True, f"oversize: 关键词标记为超大体积"

    # --- Multi-piece kit check (sets with 5+ pieces risk bulky packaging) ---
    # Exclude obviously small items (e.g. pimple patches 36/72 pack, baking mats 2 pack)
    SET_SMALL_EXEMPT = {'patch', 'sheet', 'strip', 'stick', 'bag', 'sachet', 'lining', 'mouse', 'mice', 'feather', 'rattle', 'ball', 'catnip', 'cat'}
    # 覆盖格式: N-Piece / N Piece / N Pack / N pcs / N件 / N Set（数字在前，允许连字符）
    # 注意: "4-in-1"/"N in 1" 是"多合一"非套装，不能误拦（'in' 不在关键词表内，天然安全）
    set_match = re.search(r'(\d+)\s*-?\s*(?:pack|piece|pcs|件|片|个|枚|套|set)[^a-z]', text)
    # 数字在后的格式: "Pack of 6" / "Set of 6"
    if not set_match:
        set_match = re.search(r'\b(?:pack|set)\s+of\s+(\d+)\b', text)
    if set_match:
        qty = int(set_match.group(1))
        if qty >= 5 and not any(s in text for s in SET_SMALL_EXEMPT):
            return True, f"多件套装 {qty}pcs (≥5件, 包装易超标)"

    if not is_container:
        vol_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:l\b|litre|litres|liter|liters)', text)
        if vol_match and float(vol_match.group(1)) > max_l:
            return True, f"体积 {vol_match.group(0)} (>{max_l*1000:.0f}ml)"
        ml_match = re.search(r'(\d+)\s*ml', text)
        if ml_match and int(ml_match.group(1)) > max_ml:
            return True, f"体积 {ml_match.group(0)} (>{max_ml}ml)"

    kg_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', text)
    if kg_match and float(kg_match.group(1)) > max_kg:
        return True, f"重量 {kg_match.group(0)} (>{max_kg*1000:.0f}g)"
    g_match = re.search(r'(\d+)\s*(?:g\b|grams?)', text)
    if g_match and int(g_match.group(1)) > CONFIG.get("max_weight_g", 300):
        return True, f"重量 {g_match.group(0)} (>{CONFIG.get('max_weight_g', 300)}g)"

    return False


def calc_profit(price_gbp, category="general"):
    c = CONFIG["cost_structure"]
    comm_rate = c["commission_rate"]
    if "home" in category.lower() or "kitchen" in category.lower():
        comm_rate = c["commission_home"]
    elif "pet" in category.lower():
        comm_rate = c["commission_pets"]

    vat = price_gbp * c["vat_rate"]
    commission = price_gbp * comm_rate
    fba = c["fba_small_standard"]
    ads = price_gbp * c["ad_rate"]
    returns = price_gbp * c["return_rate"]
    sourcing = c.get("sourcing_cost", 0.80)

    total_cost = vat + commission + fba + ads + returns + sourcing
    net_profit = price_gbp - total_cost
    margin = net_profit / price_gbp if price_gbp > 0 else 0
    return {
        "net_profit": round(net_profit, 2),
        "margin": round(margin, 3),
        "breakdown": {
            "vat": round(vat, 2),
            "commission": round(commission, 2),
            "fba": fba,
            "ads": round(ads, 2),
            "returns": round(returns, 2),
            "sourcing": sourcing,
            "total_cost": round(total_cost, 2)
        }
    }
