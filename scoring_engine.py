#!/usr/bin/env python3
"""
Product Radar v2 - Multi-factor scoring engine v3
Key changes from v2:
- Lower base score (30 vs 50)
- 0-review penalty for non-new-releases
- Demand signal requirement with penalty
- Category validation penalty
- Higher thresholds for recommendation labels
- Score capped at 99 for display
"""
import json, sys, re
from pathlib import Path

BASE = Path(__file__).parent
CONFIG = json.loads((BASE / "config.json").read_text())

# Category keyword map for validation
CATEGORY_KEYWORDS = {
    "kitchen": ["kitchen", "cooking", "baking", "utensil", "gadget", "spice", "mug", "cup", "pan", "pot", "chop", "peel", "slice", "grater", "measuring", "timer", "tray", "bowl", "plate"],
    "garden": ["garden", "outdoor", "plant", "flower", "patio", "bbq", "grill", "solar", "bird", "hose", "watering", "lawn", "hedge", "seed", "pot"],
    "diy": ["diy", "tool", "drill", "screw", "nail", "hammer", "wrench", "pliers", "tape measure", "level", "saw", "clamp", "socket", "hex", "torx", "breaker"],
    "sports": ["sport", "fitness", "yoga", "gym", "exercise", "resistance", "mat", "dumbbell", "kettlebell", "band", "jump rope", "grip", "foam roller"],
    "bathroom": ["bathroom", "shower", "toilet", "towel", "soap", "mirror", "bath", "shaver", "razor", "hook", "organiser", "dispenser"],
    "cleaning": ["clean", "mop", "duster", "brush", "sponge", "vacuum", "cloth", "wipe", "stain", "lint", "lint roller"],
    "office": ["desk", "office", "stationery", "pen", "notebook", "organiser", "laptop", "mouse", "keyboard", "monitor", "stand", "file", "folder", "stapler", "clip"],
    "automotive": ["car", "vehicle", "dashboard", "phone holder", "motor", "tyre", "wheel", "wiper", "seat", "mat", "tint", "winch", "tow", "hitch", "socket", "ratchet", "wrench", "nut", "bolt", "fuse", "led", "light", "flag", "motorcycle", "bike"],
    "lighting": ["led", "light", "lamp", "night light", "strip", "fairy", "solar light", "bulb", "lantern"],
    "storage": ["storage", "organiser", "box", "basket", "shelf", "drawer", "container", "bag", "pouch", "rack"],
    "crafts": ["craft", "art", "paint", "brush", "stickers", "tape", "sewing", "knit", "crochet", "needle", "thread", "fabric", "scissors"],
    "bedding": ["bedding", "pillow", "blanket", "sheet", "duvet", "cushion", "throw", "mattress", "sleep"],
    "pets": ["pet", "dog", "cat", "collar", "leash", "bed", "grooming", "litter", "feeder", "aquarium", "fish", "hamster", "rabbit"],
    "home": ["home", "decor", "wall", "candle", "vase", "frame", "mirror", "clock", "hook", "hanger", "doormat"],
}


def _validate_category(product):
    """Check if product name actually relates to its assigned category.
    Returns (is_valid, confidence 0-1).
    Also auto-corrects obviously wrong categories.
    """
    name_lower = product.get("name", "").lower()
    category = product.get("category", "").lower()

    if not category or category == "general":
        return True, 0.5

    # Find matching category keywords
    matched_cat = None
    for cat_key, keywords in CATEGORY_KEYWORDS.items():
        if cat_key in category:
            matched_cat = cat_key
            break

    if not matched_cat:
        return True, 0.3  # Unknown category, don't penalize

    # Check if any category keyword appears in product name
    keywords = CATEGORY_KEYWORDS[matched_cat]
    hits = sum(1 for kw in keywords if kw in name_lower)

    if hits >= 2:
        return True, 1.0
    elif hits == 1:
        return True, 0.7
    else:
        # Category mismatch! Try to auto-correct
        best_cat = None
        best_hits = 0
        for cat_key, cat_kws in CATEGORY_KEYWORDS.items():
            cat_hits = sum(1 for kw in cat_kws if kw in name_lower)
            if cat_hits > best_hits:
                best_hits = cat_hits
                best_cat = cat_key

        if best_cat and best_hits >= 2:
            # Auto-correct the category
            old_cat = product.get("category", "")
            product["category"] = best_cat.capitalize()
            product["category_corrected"] = True
            product["category_original"] = old_cat
            return True, 0.8  # Valid after correction

        return False, 0.0


def _classify_signal_sources(product):
    """Classify product signals into internal (Amazon) and external (independent demand signals).
    Returns (internal_sources, external_sources, external_count).

    Internal = Amazon platform data (new_releases, bsr, wished, gifts, movers_shakers)
    External = Independent demand signals (TikTok, Google Trends, HotUKDeals, Temu, Etsy, YouTube, Reddit)
    """
    sources = [x.lower() for x in product.get("sources", [])]
    sources_str = " ".join(sources)
    channel = product.get("channel", "")

    internal = []
    external = []

    # Internal: Amazon platform signals
    if "new_releases" in channel: internal.append("新品榜")
    if "bsr" in channel: internal.append("畅销榜")
    if "wished" in channel: internal.append("心愿榜")
    if "gifts" in channel: internal.append("送礼榜")
    if "movers_shakers" in channel: internal.append("飙升榜")

    # External: independent demand signals (each counts as 1)
    if "tiktok" in sources_str: external.append("TikTok")
    if product.get("google_trend") == "rising": external.append("Google")
    if "hotukdeals" in sources_str: external.append("HotUKDeals")
    if "temu" in sources_str: external.append("Temu")
    if "etsy" in sources_str: external.append("Etsy")
    if "youtube" in sources_str: external.append("YouTube")
    if "reddit" in sources_str: external.append("Reddit")

    return internal, external, len(set(external))


def _get_signal_confidence(internal, external_count):
    """Return signal confidence level and scoring impact.
    
    🔴 强信号 (≥3 external) → +20, priority push
    🟠 中信号 (2 external) → +10
    🟡 弱信号 (1 external) → 0 (no bonus, but passes demand check)
    ⚪ 无信号 (0 external, only Amazon internal) → -10
    """
    if external_count >= 3:
        return "strong", "🔴 强信号", 20
    elif external_count >= 2:
        return "medium", "🟠 中信号", 10
    elif external_count >= 1:
        return "weak", "🟡 弱信号", 0
    else:
        # No external signals — only Amazon internal data
        if internal:
            return "none", "⚪ 仅Amazon", -10
        else:
            return "none", "⚪ 无信号", -15


def _has_demand_signal(product):
    """Check if product has at least one external demand signal.
    Internal-only (Amazon) does NOT count as demand signal for filter purposes."""
    _, _, ext_count = _classify_signal_sources(product)
    return ext_count >= 1


# Scoring weights
WEIGHTS = {
    # Source signals
    "new_releases": 20,
    "wished": 15,
    "gifts": 10,
    "movers_shakers": 18,  # 新增：飙升榜权重
    "tiktok": 20,
    "google_rising": 15,
    "reddit": 5,
    "hotukdeals": 12,
    "temu": 8,
    "etsy": 6,
    "youtube": 10,

    # Multi-source boost (REPLACED by signal voting below)
    # "dual_source": 12,  → removed, use signal voting
    # "triple_source": 18, → removed, use signal voting

    # Competition (inverted: fewer reviews = higher competition risk for 0 reviews)
    "blue_ocean": 15,        # <20 reviews (true blue ocean)
    "verified_low": 10,      # 20-50 reviews (sweet spot)
    "moderate": 5,           # 50-150 reviews
    "established": 0,        # 150-300 reviews (neutral)

    # Profit
    "ultra_margin": 12,
    "high_margin": 8,
    "good_margin": 4,

    # Rating
    "high_rating": 5,

    # AnySearch trend
    "hot_category": 15,
    "trend_category": 8,
    "demand_keyword": 6,
    "cross_validated": 4,

    # History
    "rank_improving": 10,
    "consistent_growth": 8,

    # Penalties
    "zero_review_penalty": -15,
    "unverified_penalty": -8,
    "no_demand_signal": -15,
    "category_mismatch": -10,
    "off_season": -20,
    "category_overflow": -10,  # 新增：同类产品过多降分
    "event_overflow": -8,      # 新增：事件类产品过多降分
}


def score_product(product, trend_data=None, history=None):
    """Calculate multi-factor weighted score."""
    breakdown = {}
    total = 30  # Base (lowered from 50)

    name = product.get("name", "").lower()
    sources = [x.lower() for x in product.get("sources", [])]
    sources_str = " ".join(sources)
    reviews = product.get("reviews", 0)
    rating = product.get("rating", 0)
    margin = product.get("profit_margin", 0)
    channel = product.get("channel", "")

    # === Source Signals (Internal: Amazon platform) ===
    if "new_releases" in channel:
        pts = WEIGHTS["new_releases"]
        total += pts; breakdown["🆕 新品榜"] = pts

    if "wished" in channel:
        pts = WEIGHTS["wished"]
        total += pts; breakdown["💝 心愿榜"] = pts

    if "gifts" in channel:
        pts = WEIGHTS["gifts"]
        total += pts; breakdown["🎁 送礼榜"] = pts

    if "movers_shakers" in channel:
        pts = WEIGHTS["movers_shakers"]
        total += pts; breakdown["🚀 飙升榜"] = pts

    # === External Signals (independent demand sources) ===
    if "tiktok" in sources_str:
        pts = WEIGHTS["tiktok"]
        total += pts; breakdown["🎵 TikTok"] = pts

    if product.get("google_trend") == "rising":
        pts = WEIGHTS["google_rising"]
        total += pts; breakdown["📊 Google↑"] = pts

    if "reddit" in sources_str:
        pts = WEIGHTS["reddit"]
        total += pts; breakdown["💬 Reddit"] = pts

    if any("hotukdeals" in s for s in sources):
        pts = WEIGHTS["hotukdeals"]
        total += pts; breakdown["🔥 HotUKDeals"] = pts

    if any("temu" in s for s in sources):
        pts = WEIGHTS["temu"]
        total += pts; breakdown["🛒 Temu"] = pts

    if any("etsy" in s for s in sources):
        pts = WEIGHTS["etsy"]
        total += pts; breakdown["🎨 Etsy"] = pts

    if any("youtube" in s for s in sources):
        pts = WEIGHTS["youtube"]
        total += pts; breakdown["▶️ YouTube"] = pts

    # === Signal Voting (replaces old multi-source boost) ===
    internal, external_list, external_count = _classify_signal_sources(product)
    sig_level, sig_label, sig_pts = _get_signal_confidence(internal, external_count)
    product["signal_level"] = sig_level
    product["signal_label"] = sig_label
    product["external_sources"] = external_list
    product["internal_sources"] = internal
    if sig_pts != 0:
        total += sig_pts; breakdown[sig_label] = sig_pts

    # === AnySearch Trend Signals ===
    if trend_data:
        cat_scores = trend_data.get("category_scores", {})
        cat_evidence = trend_data.get("category_evidence", {})
        cross_validated = trend_data.get("cross_validated", {})
        category = product.get("category", "").lower()

        for cat, tscore in cat_scores.items():
            if cat in category or any(kw in name for kw in cat_evidence.get(cat, [])):
                if tscore >= 70:
                    label = "🔥 多源热门" if cat in cross_validated else "🔥 热门品类"
                    pts = WEIGHTS["hot_category"]
                    if cat in cross_validated:
                        pts += min(cross_validated[cat] * 2, 8)  # Capped
                    total += pts; breakdown[label + f"({cat})"] = pts
                elif tscore >= 40:
                    pts = WEIGHTS["trend_category"]
                    total += pts; breakdown[f"📈 趋势({cat})"] = pts
                break

        # Demand keywords
        for kw in trend_data.get("demand_keywords", []):
            if kw in name:
                pts = WEIGHTS["demand_keyword"]
                total += pts; breakdown["✨ 热词"] = pts
                break

    # === Competition ===
    if reviews == 0:
        # 0 reviews = unproven product
        if "new_releases" not in channel:
            pts = WEIGHTS["zero_review_penalty"]
            total += pts; breakdown["⚠️ 零评论(非新品)"] = pts
        else:
            # New releases with 0 reviews is expected, small penalty
            pts = WEIGHTS["unverified_penalty"]
            total += pts; breakdown["⏳ 待验证"] = pts
    elif reviews < 5:
        pts = WEIGHTS["unverified_penalty"]
        total += pts; breakdown["⏳ 评论偏少"] = pts
    elif reviews < 20:
        pts = WEIGHTS["blue_ocean"]
        total += pts; breakdown["🌊 蓝海"] = pts
    elif reviews <= 50:
        pts = WEIGHTS["verified_low"]
        total += pts; breakdown["🟢 低竞争"] = pts
    elif reviews <= 150:
        pts = WEIGHTS["moderate"]
        total += pts; breakdown["🟡 中等竞争"] = pts

    if rating and rating >= 4.5:
        pts = WEIGHTS["high_rating"]
        total += pts; breakdown["⭐ 高评分"] = pts

    # === Profit ===
    if margin >= 0.35:
        pts = WEIGHTS["ultra_margin"]
        total += pts; breakdown["💰 超高利润"] = pts
    elif margin >= 0.30:
        pts = WEIGHTS["high_margin"]
        total += pts; breakdown["💰 高利润"] = pts
    elif margin >= 0.25:
        pts = WEIGHTS["good_margin"]
        total += pts; breakdown["💰 较好利润"] = pts

    # === Category Validation ===
    cat_valid, cat_confidence = _validate_category(product)
    if not cat_valid:
        pts = WEIGHTS["category_mismatch"]
        total += pts; breakdown["❓ 品类不符"] = pts
    elif cat_confidence < 0.5:
        pts = WEIGHTS["category_mismatch"] // 2
        total += pts; breakdown["❓ 品类存疑"] = pts

    # === Demand Signal Check ===
    if not _has_demand_signal(product):
        pts = WEIGHTS["no_demand_signal"]
        total += pts; breakdown["📉 无需求信号"] = pts

    # === Seasonal ===
    from datetime import datetime
    month = datetime.now().month
    season = "summer" if month in (6,7,8) else "winter" if month in (12,1,2) else "spring" if month in (3,4,5) else "autumn"
    seasonal_cfg = CONFIG.get("seasonal_categories", {})
    hot_kw = set(kw.lower() for kw in seasonal_cfg.get(f"{season}_hot", []))

    name_for_season = product.get("name", "").lower() + " " + product.get("category", "").lower()
    is_seasonal_hot = any(kw in name_for_season for kw in hot_kw)
    is_off_season = product.get("off_season", False)

    if is_seasonal_hot and not is_off_season:
        pts = 10
        total += pts; breakdown[f"🌴 当季({season})"] = pts

    if is_off_season:
        pts = WEIGHTS["off_season"]
        total += pts; breakdown["❄️ 过季降权"] = pts

    # === Supply-Demand Index (from market_intelligence) ===
    sd_score = product.get("sd_score", 0)
    sd_label = product.get("sd_label", "")
    if sd_score != 0:
        total += sd_score
        breakdown[sd_label] = sd_score

    # === Trend Divergence (from market_intelligence) ===
    div_score = product.get("div_score", 0)
    div_label = product.get("div_label", "")
    if div_score != 0:
        total += div_score
        breakdown[div_label] = div_score

    # === History ===
    if history:
        key = product.get("asin") or product.get("name", "").lower().strip()
        if key in history:
            hist = history[key]
            if len(hist) >= 2:
                recent = hist[-1].get("rank")
                older = hist[-2].get("rank")
                if recent and older and recent < older:
                    pts = WEIGHTS["rank_improving"]
                    total += pts; breakdown["📈 排名上升"] = pts
                if len(hist) >= 3:
                    scores = [h.get("score", 0) for h in hist[-3:]]
                    if all(scores[i] <= scores[i+1] for i in range(len(scores)-1)):
                        pts = WEIGHTS["consistent_growth"]
                        total += pts; breakdown["📊 持续上升"] = pts

    return max(total, 0), breakdown


def score_all_products(products, trend_data=None, history=None):
    """Score all products and add score fields.
    Also applies category diversity penalties to avoid single-category domination."""
    from collections import Counter

    # Count products per category for diversity scoring
    cat_counts = Counter(p.get("category", "unknown") for p in products)

    # Track event products for overflow penalty
    EVENT_KEYWORDS = {
        'world cup', 'euro', 'olympic', 'olympics', 'jubilee', 'coronation',
        'christmas', 'halloween', 'easter', 'valentine'
    }

    for p in products:
        score, breakdown = score_product(p, trend_data, history)

        # Sponsored Ad 降权：广告位产品 = 该关键词竞争激烈 + 多为低质测品，信号不可靠
        if (p.get("name") or "").lower().startswith("sponsored ad"):
            pts = -10
            score += pts
            breakdown["📢 广告位"] = pts

        # 未验证降权：详情页无重量/尺寸数据（[7a] 抓不到）→ 有超标风险，降权展示
        if p.get("verify_status") == "unverified":
            pts = -8
            score += pts
            breakdown["⚠️ 未验证"] = pts

        # Category diversity penalty: if same category has too many products
        category = p.get("category", "unknown")
        cat_count = cat_counts.get(category, 0)
        if cat_count >= 8:
            pts = WEIGHTS["category_overflow"]
            score += pts
            breakdown["⚠️ 品类过密"] = pts
        elif cat_count >= 5:
            pts = WEIGHTS["category_overflow"] // 2
            score += pts
            breakdown["⚠️ 品类较多"] = pts

        # Event overflow penalty: if product is event-related
        name_lower = p.get("name", "").lower()
        is_event = any(kw in name_lower for kw in EVENT_KEYWORDS)
        if is_event:
            # Count how many event products exist in same category
            event_in_cat = sum(1 for pp in products
                              if pp.get("category") == category
                              and any(kw in pp.get("name", "").lower() for kw in EVENT_KEYWORDS))
            if event_in_cat >= 4:
                pts = WEIGHTS["event_overflow"]
                score += pts
                breakdown["🎯 事件过密"] = pts

        # Freshness bonus: first appearance in history
        asin = p.get("asin", "")
        if history and asin not in history:
            score += 10
            breakdown["✨ 新发现"] = 10

        p["score"] = score
        p["score_breakdown"] = breakdown

        if score >= 100:
            p["stars"] = 5
        elif score >= 80:
            p["stars"] = 4
        elif score >= 60:
            p["stars"] = 3
        elif score >= 40:
            p["stars"] = 2
        else:
            p["stars"] = 1

    products.sort(key=lambda x: -x.get("score", 0))
    return products


def get_score_label(score):
    if score >= 100: return "🔥 强烈推荐", "#FF2D55"
    elif score >= 80: return "⭐ 值得关注", "#FF9500"
    elif score >= 60: return "👍 可以考虑", "#007AFF"
    elif score >= 40: return "👀 待观察", "#8e8e93"
    else: return "💤 优先级低", "#c7c7cc"
