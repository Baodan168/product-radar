#!/usr/bin/env python3
"""
AnySearch trend fetcher v2 - expanded multi-source trend analysis
Searches: TikTok, HotUKDeals, Temu, Etsy, YouTube, Google Trends, Reddit
"""
import json, subprocess, re, sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
ANYSEARCH = str(Path.home() / ".hermes/skills/search/anysearch/scripts/anysearch_cli.py")


def _run_anysearch(query, domain="general", max_results=8, freshness="week"):
    # ⚠️ 2026-08-26 发现：anysearch CLI 没有 "general" 域名，传 general 会让
    # CLI 秒退 usage error → 11/21 个查询一直静默失败（UK 靠 ecommerce 撑着没暴露）。
    if domain == "general":
        domain = "home"  # 泛化查询 → home 域
    try:
        cmd = ["python3", ANYSEARCH, "search", query,
               "--domain", domain, "--max_results", str(max_results)]
        if freshness:
            cmd.extend(["--freshness", freshness])
        cmd.extend(["--zone", "intl"])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        print(f"  AnySearch error: {e}", file=sys.stderr)
    return ""


def _get_season(month):
    if month in (3, 4, 5): return "spring"
    if month in (6, 7, 8): return "summer"
    if month in (9, 10, 11): return "autumn"
    return "winter"


def fetch_trend_signals():
    """Fetch trend signals from multiple sources via AnySearch.
    
    Returns (trend_data, raw_results) where trend_data contains:
    - category_scores: category -> heat score (0-100)
    - source_signals: source -> list of matched keywords
    - demand_keywords: trending product keywords
    """
    now = datetime.now()
    month = now.strftime("%B")
    year = now.strftime("%Y")
    season = _get_season(now.month)

    # === Query groups by source ===
    query_groups = {
        "tiktok": [
            (f"TikTok Shop UK trending products {season} {year}", "ecommerce"),
            (f"TikTok viral products UK under £10 useful {year}", "ecommerce"),
            ("TikTok made me buy it UK 2026 best products", "ecommerce"),
        ],
        "hotukdeals": [
            ("site:hotukdeals.com Amazon UK best deals trending", "general"),
            (f"hotukdeals popular deals {season} {year} small items", "general"),
            ("hotukdeals most voted Amazon UK accessories gadgets", "general"),
        ],
        "temu": [
            (f"Temu UK best sellers trending products {season}", "ecommerce"),
            ("Temu trending products UK small items accessories gadgets", "ecommerce"),
            ("Temu viral products UK what to sell on Amazon", "ecommerce"),
        ],
        "etsy": [
            (f"Etsy UK trending products {season} {year} best sellers", "ecommerce"),
            ("Etsy UK trending handmade accessories home decor", "ecommerce"),
            ("Etsy trending now UK popular gift ideas", "ecommerce"),
        ],
        "youtube": [
            ("site:youtube.com Amazon UK haul best finds under £10 2026", "general"),
            ("youtube Amazon UK best sellers review small items haul", "general"),
            (f"youtube Amazon UK {season} must haves trending products", "general"),
        ],
        "google_trends": [
            (f"UK trending products {season} {year} popular buying", "general"),
            (f"Amazon UK new releases trending {month} {year}", "general"),
            (f"{season} products UK home garden outdoor trending", "general"),
        ],
        "reddit": [
            ("site:reddit.com UK Amazon best cheap finds under £10", "general"),
            ("site:reddit.com CasualUK small purchases improved life", "general"),
            ("site:reddit.com FrugalUK best value Amazon purchases", "general"),
        ],
        "market_intel": [
            (f"Amazon UK best sellers small items {year} trending accessories", "ecommerce"),
            (f"UK consumer trends {year} popular products home garden", "general"),
            (f"cross border ecommerce UK trending {season} {year}", "general"),
        ],
    }

    all_results = []
    source_keywords = {}  # source -> set of matched keywords

    for source, queries in query_groups.items():
        for q, domain in queries:
            print(f"  [{source}] {q[:55]}...", file=sys.stderr)
            text = _run_anysearch(q, domain=domain)
            if text:
                all_results.append({"query": q, "text": text, "domain": domain, "source": source})

    # Analyze all results
    trend_data = _analyze_trends(all_results, query_groups.keys())

    return trend_data, all_results


def _analyze_trends(results, source_names):
    """Analyze search results to extract trending categories and keywords."""
    category_keywords = {
        "kitchen": ["kitchen", "cooking", "baking", "utensil", "gadget", "organiser", "spice", "mug", "cup"],
        "garden": ["garden", "outdoor", "plant", "flower", "patio", "bbq", "grill", "solar", "bird"],
        "bathroom": ["bathroom", "shower", "toilet", "towel", "soap", "mirror", "bath"],
        "cleaning": ["cleaning", "cleaner", "vacuum", "mop", "duster", "brush", "sponge"],
        "car": ["car", "automotive", "vehicle", "dashboard", "phone holder", "organiser", "motor"],
        "office": ["desk", "office", "stationery", "pen", "notebook", "organiser", "laptop", "mouse"],
        "storage": ["storage", "organiser", "box", "basket", "shelf", "drawer", "container"],
        "lighting": ["led", "light", "lamp", "night light", "strip", "fairy", "solar light"],
        "pets": ["pet", "dog", "cat", "toy", "collar", "leash", "bed", "grooming"],
        "sports": ["fitness", "yoga", "gym", "exercise", "sport", "water bottle", "resistance"],
        "crafts": ["craft", "art", "paint", "brush", "stickers", "tape", "sewing"],
        "bedding": ["bedding", "pillow", "blanket", "sheet", "duvet", "cushion", "throw"],
        "travel": ["travel", "luggage", "packing", "passport", "neck pillow", "toiletry"],
        "phone": ["phone", "case", "charger", "cable", "holder", "stand", "ring light", "earbuds"],
        "beauty": ["makeup", "brush", "mirror", "hair", "nail", "skincare", "organiser"],
        "home decor": ["decor", "wall art", "candle", "vase", "frame", "mirror", "clock"],
        "baby": ["baby", "toddler", "child", "kids", "nursery"],
        "kitchen_gadgets": ["kitchen gadget", "peeler", "slicer", "grater", "measuring", "timer"],
        "eco": ["eco", "reusable", "sustainable", "bamboo", "organic", "zero waste"],
        "seasonal": ["christmas", "halloween", "easter", "valentine", "birthday", "gift"],
    }

    # Seasonal boost
    season_month = datetime.now().month
    seasonal_kw = set()
    if season_month in (6, 7, 8):
        seasonal_kw = {"garden", "outdoor", "bbq", "travel", "sports", "solar", "water bottle"}
    elif season_month in (11, 12, 1):
        seasonal_kw = {"christmas", "gift", "candle", "decor", "lighting", "blanket", "throw"}
    elif season_month in (3, 4, 5):
        seasonal_kw = {"garden", "cleaning", "storage", "organiser", "easter", "plant"}

    # Count category mentions across all results
    category_scores = {}
    category_evidence = {}
    source_signals = {src: {} for src in source_names}
    demand_keywords = set()

    for result in results:
        text_lower = result["text"].lower()
        source = result.get("source", "unknown")

        for cat, keywords in category_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    category_scores[cat] = category_scores.get(cat, 0) + 1
                    category_evidence.setdefault(cat, set()).add(kw)
                    # Track per-source signals
                    source_signals.setdefault(source, {}).setdefault(cat, 0)
                    source_signals[source][cat] = source_signals[source].get(cat, 0) + 1

        # Extract trending product keywords (phrases between quotes or numbered lists)
        for m in re.finditer(r'"([^"]{5,50})"', text_lower):
            phrase = m.group(1).strip()
            if any(c.isalpha() for c in phrase):
                demand_keywords.add(phrase)

        for m in re.finditer(r'\d+[.)]\s*([A-Za-z][a-z]+(?:\s+[a-z]+){1,4})', result["text"]):
            phrase = m.group(1).strip().lower()
            if 5 < len(phrase) < 40:
                demand_keywords.add(phrase)

    # Apply seasonal boost
    for cat in list(category_scores.keys()):
        if cat in seasonal_kw or any(sk in category_evidence.get(cat, set()) for sk in seasonal_kw):
            category_scores[cat] = int(category_scores[cat] * 1.3)

    # Normalize to 0-100
    if category_scores:
        max_score = max(category_scores.values())
        for cat in category_scores:
            category_scores[cat] = round((category_scores[cat] / max(max_score, 1)) * 100)

    # Cross-source validation: categories found in 3+ sources get a boost
    cross_validated = {}
    for cat in category_scores:
        sources_found = sum(1 for src in source_signals if cat in source_signals.get(src, {}))
        if sources_found >= 3:
            cross_validated[cat] = sources_found
            category_scores[cat] = min(100, category_scores[cat] + 15)

    # Filter garbage demand keywords (LLM instruction artifacts)
    GARBAGE_PATTERNS = {
        'analyze', 'compare', 'find profitable', 'best of', 'how to', 'what is',
        'top 10', 'top 5', 'review', 'guide', 'tutorial', 'tips for', 'ways to',
        'reasons to', 'things to', 'amazon comparing', 'the title', 'the product',
    }
    filtered_keywords = set()
    for kw in demand_keywords:
        kw_lower = kw.lower().strip()
        # Skip if too short or matches garbage pattern
        if len(kw_lower) < 6:
            continue
        if any(g in kw_lower for g in GARBAGE_PATTERNS):
            continue
        # Skip if it looks like an instruction (starts with verb + "the")
        if re.match(r'^(analyze|find|compare|check|review|list|identify)\s', kw_lower):
            continue
        filtered_keywords.add(kw)

    return {
        "category_scores": category_scores,
        "category_evidence": {k: list(v) for k, v in category_evidence.items()},
        "source_signals": {k: dict(v) for k, v in source_signals.items() if v},
        "cross_validated": cross_validated,
        "demand_keywords": sorted(filtered_keywords)[:30],
        "season": _get_season(season_month),
        "total_queries": len(results),
        "total_results_chars": sum(len(r["text"]) for r in results),
    }


def match_product_to_trends(product, trend_data):
    """Score a product against trend data. Returns (score_bonus, signals)."""
    name_lower = product.get("name", "").lower()
    category = product.get("category", "").lower()
    score_bonus = 0
    signals = []

    cat_scores = trend_data.get("category_scores", {})
    cat_evidence = trend_data.get("category_evidence", {})
    cross_validated = trend_data.get("cross_validated", {})

    for cat, trend_score in cat_scores.items():
        if cat in category or any(kw in name_lower for kw in cat_evidence.get(cat, [])):
            if trend_score >= 70:
                score_bonus += 20
                label = "🔥 热门" if cat not in cross_validated else "🔥 多源热门"
                signals.append(f"{label}({cat})")
            elif trend_score >= 40:
                score_bonus += 10
                signals.append(f"📈 趋势({cat})")
            break

    # Check demand keywords
    for kw in trend_data.get("demand_keywords", []):
        if kw in name_lower:
            score_bonus += 8
            signals.append(f"✨ 热词({kw[:20]})")
            break

    # Check cross-source validation
    for cat, count in cross_validated.items():
        if cat in category:
            score_bonus += count * 3
            signals.append(f"🔗 {count}源验证")

    return min(score_bonus, 35), signals


def get_trending_keywords(trend_data):
    """Extract top trending keywords for display."""
    evidence = trend_data.get("category_evidence", {})
    demand = trend_data.get("demand_keywords", [])
    all_kw = list(demand)
    for cat, kws in evidence.items():
        all_kw.extend(kws[:3])
    return list(set(all_kw))[:25]


if __name__ == "__main__":
    trend_data, raw = fetch_trend_signals()
    print(json.dumps(trend_data, ensure_ascii=False, indent=2))
