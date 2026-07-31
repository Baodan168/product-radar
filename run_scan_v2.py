#!/usr/bin/env python3
"""
Product Radar v2 - Multi-source Channel Aggregation
Sources: Amazon (New/BSR/Wished/Gifts), TikTok, HotUKDeals, Temu, Etsy, YouTube, Google Trends, Reddit
"""
import json, sys, os
import concurrent.futures
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from scanner import is_forbidden, calc_profit
from sources.amazon_uk import fetch as fetch_amazon
from sources.tiktok_shop import fetch as fetch_tiktok
from sources.google_trends import fetch_demand_signals, extract_trending_keywords
from sources.reddit_demand import fetch_demand_signals as fetch_reddit
from sources.anysearch_trends import fetch_trend_signals
from scoring_engine import score_all_products
from market_intelligence import analyze_market, get_product_sd_score, get_product_divergence_score
from gap_opportunity import analyze_gaps
from keyword_scanner import run_keyword_scan


def match_keywords_to_products(keywords, products, source_tag):
    """Improved keyword-to-product matcher with word boundary and multi-hit requirement."""
    import re
    kw_set = set()
    kw_phrases = set()
    for kw_item in keywords:
        name = kw_item.get("name", "").lower().strip() if isinstance(kw_item, dict) else str(kw_item).lower().strip()
        if len(name) > 4:
            kw_phrases.add(name)  # Full phrase match
        for word in name.split():
            word = word.strip()
            if len(word) >= 5 and word.isalpha():  # Only real words, min 5 chars
                kw_set.add(word)

    matched = []
    for p in products:
        p_name = p.get("name", "").lower()
        # Word boundary matching for single words
        word_hits = 0
        for kw in kw_set:
            if re.search(r'(?<![a-z])' + re.escape(kw) + r'(?![a-z])', p_name):
                word_hits += 1
        # Phrase matching (more reliable)
        phrase_hits = sum(1 for kw in kw_phrases if kw in p_name)
        total_hits = word_hits + phrase_hits * 2  # Phrases count double

        if total_hits >= 2:  # Require at least 2 signal strength
            if source_tag not in p.get("sources", []):
                p.setdefault("sources", []).append(source_tag)
            matched.append(p)
    return matched


def enrich_from_trend_data(products, trend_data):
    """Add trend-based signals to products using evidence keywords + raw text matching.
    
    Uses three matching strategies:
    1. category_evidence keywords (specific terms like "grooming", "collar") → product name
    2. source_signals categories → product category field (loose match)
    3. Raw AnySearch text → product name keyword extraction (like Google/Reddit enrichment)
    """
    import re
    source_signals = trend_data.get("source_signals", {})
    cat_evidence = trend_data.get("category_evidence", {})
    cat_scores = trend_data.get("category_scores", {})
    
    source_map = {
        "hotukdeals": "HotUKDeals热帖",
        "temu": "Temu热销",
        "etsy": "Etsy趋势",
        "youtube": "YouTube种草",
        "tiktok": "TikTok趋势",
    }

    # Strategy 1: Use category evidence keywords for precise matching
    # e.g., "pets" has evidence ["grooming", "collar", "leash", "feeder"]
    # A product named "Dog Grooming Brush" matches because "grooming" is in evidence
    for p in products:
        name_lower = p.get("name", "").lower()
        category = p.get("category", "").lower()
        
        matched_sources = set()
        for cat, evidence_kws in cat_evidence.items():
            if cat_scores.get(cat, 0) < 30:  # Only care about trending categories
                continue
            # Check if evidence keyword appears in product name
            for kw in evidence_kws:
                kw_lower = kw.lower().strip()
                if len(kw_lower) >= 4 and kw_lower in name_lower:
                    # Find which sources had this category
                    for source_key, source_tag in source_map.items():
                        if source_key in source_signals:
                            if cat in source_signals[source_key]:
                                matched_sources.add(source_tag)
                    break  # One match per category is enough
        
        for tag in matched_sources:
            if tag not in p.get("sources", []):
                p.setdefault("sources", []).append(tag)

    # Strategy 2: Match by product category field (only for products not yet matched)
    for p in products:
        if p.get("sources"):  # Already matched by evidence keywords — skip
            continue
        category = p.get("category", "").lower()
        if not category:
            continue
        for source_key, source_tag in source_map.items():
            if source_key in source_signals:
                cats = source_signals[source_key]
                for cat in cats:
                    if cat in category or category in cat:
                        if source_tag not in p.get("sources", []):
                            p.setdefault("sources", []).append(source_tag)
                        break

    return products


def enrich_google_trends(products, gtrends_text):
    if not gtrends_text:
        return products
    import re
    keywords = extract_trending_keywords(gtrends_text)
    gtrends_lower = gtrends_text.lower()
    for p in products:
        name_lower = p.get("name", "").lower()
        words = [w for w in name_lower.split() if len(w) >= 5 and w.isalpha()]
        match_count = 0
        for kw in keywords:
            if len(kw) >= 5 and re.search(r'(?<![a-z])' + re.escape(kw) + r'(?![a-z])', name_lower):
                match_count += 1
        for word in words[:5]:
            if len(word) >= 5 and re.search(r'(?<![a-z])' + re.escape(word) + r'(?![a-z])', gtrends_lower):
                match_count += 1
        if match_count >= 2:
            p["google_trend"] = "rising"
            if "Google趋势" not in p.get("sources", []):
                p.setdefault("sources", []).append("Google趋势")
    return products


def enrich_reddit(products, reddit_text):
    if not reddit_text: return products
    import re
    reddit_lower = reddit_text.lower()
    generic = {'that', 'this', 'with', 'from', 'have', 'been', 'your', 'they', 'will', 'more', 'than', 'what', 'when', 'very', 'just', 'like', 'would', 'could', 'should', 'about', 'these', 'those', 'here', 'there', 'some', 'each', 'much', 'many'}
    for p in products:
        words = [w for w in p.get("name", "").lower().split() if len(w) >= 5 and w.isalpha()]
        match = sum(1 for word in words[:5]
                    if word not in generic
                    and re.search(r'(?<![a-z])' + re.escape(word) + r'(?![a-z])', reddit_lower))
        if match >= 2:
            if "Reddit需求" not in p.get("sources", []):
                p.setdefault("sources", []).append("Reddit需求")
    return products


def filter_products(products, config):
    passed, rejected = [], []
    from datetime import datetime
    month = datetime.now().month
    season = "summer" if month in (6,7,8) else "winter" if month in (12,1,2) else "spring" if month in (3,4,5) else "autumn"

    seasonal = config.get("seasonal_categories", {})
    off_season_key = f"{season}_cold"
    off_season_kw = set(kw.lower() for kw in seasonal.get(off_season_key, []))
    forbidden_brands = set(b.lower() for b in config.get("forbidden_brands", []))
    max_reviews = config.get("max_reviews", 300)

    # Event keywords for limiting event-based products
    EVENT_KEYWORDS = {
        'world cup', 'euro 2024', 'euro 2025', 'euro 2026', 'olympic', 'olympics',
        'jubilee', 'coronation', 'christmas', 'halloween', 'easter', 'valentine',
        'mother\'s day', 'father\'s day', 'black friday', 'prime day'
    }

    # Load user-rejected ASINs
    import pathlib
    rej_file = pathlib.Path(__file__).parent / "rejected_by_user.json"
    user_rejected = set()
    if rej_file.exists():
        try:
            user_rejected = set(json.loads(rej_file.read_text(encoding="utf-8")).keys())
        except: pass

    for p in products:
        name, category = p.get("name", ""), p.get("category", "")
        name_lower = name.lower()
        reviews = p.get("reviews", 0)
        asin = p.get("asin", "")

        # 0. 用户手动标记不考虑
        if asin and asin in user_rejected:
            rejected.append({"name": name[:60], "reason": "用户标记不考虑", "asin": asin}); continue

        # 1. 禁选品类/关键词
        result = is_forbidden(name, category)
        if isinstance(result, tuple):
            forbidden, reason = result
        else:
            forbidden, reason = result, ""
        if forbidden:
            rejected.append({"name": name[:60], "reason": f"禁选: {reason}", "asin": p.get("asin")}); continue

        # 2. 大品牌排除（配件豁免：如果同时出现配件关键词，说明是兼容配件不是品牌自营）
        ACCESSORY_KEYWORDS = {
            "case", "cover", "charger", "cable", "holder", "protector", "stand",
            "mount", "dock", "sleeve", "pouch", "strap", "band", "screen protector",
            "tempered glass", "skin", "decals", "sticker", "adapter", "hub",
            "compatible", "for ", "fits ", "replacement"
        }
        brand_hit = None
        for brand in forbidden_brands:
            if brand in name_lower:
                # Check if this is an accessory FOR the brand (not the brand's own product)
                is_accessory = any(kw in name_lower for kw in ACCESSORY_KEYWORDS)
                if not is_accessory:
                    brand_hit = brand; break
        if brand_hit:
            rejected.append({"name": name[:60], "reason": f"大牌: {brand_hit}", "asin": p.get("asin")}); continue

        # 3. 评论数范围（排除红海+排除无验证产品）
        max_reviews = config.get("max_reviews", 100)
        min_reviews = 3  # 最低3条评论，捕捉上升期产品
        if reviews > max_reviews:
            rejected.append({"name": name[:60], "reason": f"评论{reviews}>{max_reviews}(红海)", "asin": p.get("asin")}); continue
        # 新品榜和Movers & Shakers允许0评论
        if reviews < min_reviews and p.get("channel", "") not in ("new_releases", "movers_shakers"):
            rejected.append({"name": name[:60], "reason": f"评论{reviews}<{min_reviews}(无验证)", "asin": p.get("asin")}); continue

        # 3b. 评分过滤（排除退货风险品）
        min_rating = config.get("min_rating", 4.0)
        rating = p.get("rating", 0)
        if rating and rating < min_rating:
            rejected.append({"name": name[:60], "reason": f"评分{rating}<{min_rating}(退货风险)", "asin": p.get("asin")}); continue

        # 4. 价格区间
        price = p.get("price", 0)
        if price < config["price_range"]["min"] or price > config["price_range"]["max"]:
            rejected.append({"name": name[:60], "reason": f"£{price} 不在区间", "asin": p.get("asin")}); continue

        # 5. 利润率
        profit = calc_profit(price, category)
        p["profit_margin"] = profit["margin"]
        p["net_profit"] = profit["net_profit"]
        p["cost_breakdown"] = profit["breakdown"]
        if profit["margin"] < config["min_profit_margin"]:
            rejected.append({"name": name[:60], "reason": f"利润率{profit['margin']*100:.1f}%", "asin": p.get("asin")}); continue

        # 6. 过季产品标记（不排除，但降权）
        is_off_season = any(kw in name_lower for kw in off_season_kw)
        if is_off_season:
            p["off_season"] = True
        else:
            p["off_season"] = False

        passed.append(p)
    return passed, rejected


def limit_event_products(products, max_per_event=2):
    """Limit products from the same event to avoid domination.
    Returns filtered list with max N products per event type."""
    EVENT_KEYWORDS = {
        'world cup': 'world_cup',
        'euro 2024': 'euro', 'euro 2025': 'euro', 'euro 2026': 'euro',
        'olympic': 'olympics', 'olympics': 'olympics',
        'jubilee': 'royal', 'coronation': 'royal',
        'christmas': 'christmas', 'halloween': 'halloween',
        'easter': 'easter', 'valentine': 'valentine',
        'mother\'s day': 'mothers_day', 'father\'s day': 'fathers_day',
        'black friday': 'black_friday', 'prime day': 'prime_day'
    }

    event_groups = {}
    non_event = []

    for p in products:
        name_lower = p.get('name', '').lower()
        matched_event = None
        for keyword, event_type in EVENT_KEYWORDS.items():
            if keyword in name_lower:
                matched_event = event_type
                break

        if matched_event:
            event_groups.setdefault(matched_event, []).append(p)
        else:
            non_event.append(p)

    # Each event keeps max N highest-scored products
    limited = non_event[:]
    for event_type, items in event_groups.items():
        items.sort(key=lambda x: -x.get('score', 0))
        kept = items[:max_per_event]
        limited.extend(kept)
        if len(items) > max_per_event:
            print(f"  🎯 Event '{event_type}': kept {len(kept)}/{len(items)}", file=sys.stderr)

    return limited


def dedup_products(products):
    by_asin = {}
    result = []
    for p in products:
        asin = p.get("asin", "")
        if not asin: result.append(p); continue
        if asin in by_asin:
            existing = by_asin[asin]
            for src in p.get("sources", []):
                if src not in existing.get("sources", []):
                    existing.setdefault("sources", []).append(src)
            if p.get("channel") == "new_releases" and existing.get("channel") not in ("new_releases",):
                existing["channel"] = "new_releases"
                existing["channel_name"] = "Amazon新品榜"
            if p.get("channel") == "wished" and existing.get("channel") not in ("new_releases", "wished"):
                existing["channel"] = "wished"
                existing["channel_name"] = "Amazon心愿榜"
        else:
            by_asin[asin] = p
            result.append(p)
    return result


def load_history(days=7):
    hist_dir = BASE / "data" / "history"
    history = {}
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    for f in sorted(hist_dir.glob("*.json")):
        try:
            d = datetime.strptime(f.stem[:10], "%Y-%m-%d")
            if d >= cutoff:
                data = json.loads(f.read_text())
                for item in data:
                    key = item.get("asin") or item.get("name", "").lower().strip()
                    if key not in history: history[key] = []
                    history[key].append({"date": f.stem, "rank": item.get("rank"), "score": item.get("score", 0)})
        except (ValueError, json.JSONDecodeError): continue
    return history


def assign_channel_tags(p):
    """Assign channel_tags array based on product data."""
    sources = [s.lower() for s in p.get("sources", [])]
    channel = p.get("channel", "other")
    tags = [channel]

    if any("tiktok" in s for s in sources): tags.append("tiktok_verified")
    if any("hotukdeals" in s for s in sources): tags.append("hotukdeals")
    if any("temu" in s for s in sources): tags.append("temu_trending")
    if any("etsy" in s for s in sources): tags.append("etsy_trending")
    if any("youtube" in s for s in sources): tags.append("youtube_review")
    if p.get("google_trend") == "rising": tags.append("google_trends")
    if len(set(sources)) >= 2:
        p["is_multi"] = True
        tags.append("multi_source")

    # Event product tagging
    EVENT_KEYWORDS = {
        'world cup', 'euro', 'olympic', 'olympics', 'jubilee', 'coronation',
        'christmas', 'halloween', 'easter', 'valentine'
    }
    name_lower = p.get("name", "").lower()
    if any(kw in name_lower for kw in EVENT_KEYWORDS):
        tags.append("event_product")
        p["is_event"] = True
    else:
        p["is_event"] = False

    p["channel_tags"] = list(set(tags))
    return p


def main():
    now = datetime.now()
    scan_date = now.strftime("%Y-%m-%d")
    scan_time = now.strftime("%H:%M")
    scan_ts = now.strftime("%Y-%m-%d_%H%M")  # Timestamp for filenames
    config = json.loads((BASE / "config.json").read_text())

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  Product Radar v2 | {scan_date} {scan_time}", file=sys.stderr)
    print(f"  Sources: Amazon+TikTok+HotUKDeals+Temu+Etsy+YouTube+Google+Reddit", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    # 1. Amazon (New/BSR/Wished/Gifts)
    print("[1/8] Amazon UK (New+BSR+Wished+Gifts)...", file=sys.stderr)
    amazon_products = fetch_amazon(max_per_channel_type=5)  # 跟新默认值保持一致
    print(f"  Amazon: {len(amazon_products)} products", file=sys.stderr)

    # 1b. Keyword-driven scan (discovery + festival keywords) with dedicated Playwright
    print("\n[1b/8] Keyword-driven scan (discovery + festival)...", file=sys.stderr)
    # 超时用线程池而不是 SIGALRM（audit P1）。
    # signal.alarm 只有 Unix 有，Windows 上直接 AttributeError；
    # 而且 SIGALRM 只能在主线程注册，以后要并行扫描就会踩坑。
    #
    # 注意：超时后工作线程仍在后台跑（Python 没法强杀线程），
    # 但它是 daemon 线程，不会拖住进程退出，且结果会被丢弃。
    KEYWORD_SCAN_TIMEOUT = 120
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix='keyword-scan') as _pool:
        _future = _pool.submit(
            run_keyword_scan,
            max_discovery_kws=5, max_festival_kws=5, max_products_per_kw=10,
            max_reviews=config.get("max_reviews", 200),
        )
        try:
            keyword_products = _future.result(timeout=KEYWORD_SCAN_TIMEOUT)
            if keyword_products:
                amazon_products.extend(keyword_products)
                print(f"  Added {len(keyword_products)} keyword products → total {len(amazon_products)}", file=sys.stderr)
        except concurrent.futures.TimeoutError:
            print(f"  ⏰ 关键词扫描超时（>{KEYWORD_SCAN_TIMEOUT}s），跳过", file=sys.stderr)
            _future.cancel()
            _pool.shutdown(wait=False)
        except Exception as e:
            print(f"  ⚠️ 关键词扫描失败，跳过: {e}", file=sys.stderr)

    # 2. AnySearch trends (TikTok+HotUKDeals+Temu+Etsy+YouTube+Google+Reddit)
    print("\n[2/7] AnySearch 多源趋势分析...", file=sys.stderr)
    trend_data, trend_raw = fetch_trend_signals()
    top_cats = sorted(trend_data.get("category_scores", {}).items(), key=lambda x: -x[1])[:6]
    print(f"  Top categories:", file=sys.stderr)
    for cat, score in top_cats:
        cv = "✓" if cat in trend_data.get("cross_validated", {}) else " "
        print(f"    [{cv}] {cat}: {score}/100", file=sys.stderr)

    # 3. TikTok keyword matching
    print("\n[3/7] TikTok UK...", file=sys.stderr)
    tiktok_products = fetch_tiktok()
    tiktok_matched = match_keywords_to_products(tiktok_products, amazon_products, "TikTok趋势")
    print(f"  TikTok → {len(tiktok_matched)} products", file=sys.stderr)

    # ── Checkpoint save: save raw products even if later steps crash ──
    checkpoint = {
        "scan_date": scan_date, "scan_time": scan_time, "scan_ts": scan_ts,
        "stats": {"total_scanned": len(amazon_products), "passed": len(tiktok_matched), "sources": ["amazon","keyword","tiktok"]},
        "products": amazon_products,
    }
    try:
        (BASE / "data" / "channels" / f"{scan_ts}-raw.json").write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  💾 Checkpoint saved ({len(amazon_products)} products)", file=sys.stderr)
    except Exception as e:
        print(f"  ⚠️  Checkpoint save failed: {e}", file=sys.stderr)

    # 4. Google Trends (with error protection)
    print("\\n[4/7] Google Trends UK...", file=sys.stderr)
    try:
        gtrends_text = fetch_demand_signals()
        amazon_products = enrich_google_trends(amazon_products, gtrends_text)
        gt_count = sum(1 for p in amazon_products if p.get("google_trend") == "rising")
        print(f"  Google Trends → {gt_count} products", file=sys.stderr)
    except Exception as e:
        print(f"  ⚠️ Google Trends error (non-fatal): {e}", file=sys.stderr)
        gtrends_text = ""

    # 5. Reddit
    print("\\n[5/7] Reddit demand...", file=sys.stderr)
    try:
        reddit_text = fetch_reddit()
        amazon_products = enrich_reddit(amazon_products, reddit_text)
    except Exception as e:
        print(f"  ⚠️ Reddit error (non-fatal): {e}", file=sys.stderr)

    # 6. Enrich with AnySearch source signals
    print("\n[6/7] Enriching with trend signals...", file=sys.stderr)
    amazon_products = enrich_from_trend_data(amazon_products, trend_data)
    for src_tag in ["HotUKDeals热帖", "Temu热销", "Etsy趋势", "YouTube种草"]:
        cnt = sum(1 for p in amazon_products if src_tag in p.get("sources", []))
        if cnt: print(f"  {src_tag}: {cnt} products", file=sys.stderr)

    # Dedup
    products = dedup_products(amazon_products)
    print(f"  After dedup: {len(products)}", file=sys.stderr)

    # 7. Filter + Score
    print("\n[7/7] Filtering & Scoring...", file=sys.stderr)
    passed, rejected = filter_products(products, config)
    print(f"  Passed: {len(passed)} | Rejected: {len(rejected)}", file=sys.stderr)

    # 7a. Detail page verification (weight/dimensions via Product Information)
    #     2026-07-31 重建：原版 2026-07-24 丢失导致尺寸验证静默失效，
    #     重建版用 curl_cffi（sources.amazon_uk._curl_fetch），Scrapling 被 Amazon 空响应拦截。
    try:
        from detail_verifier import batch_verify
        passed, detail_rejected = batch_verify(passed, config)
        rejected.extend(detail_rejected)
    except Exception as e:
        print(f"  ⚠️ [7a] 详情页验证失败 (non-fatal): {e}", file=sys.stderr)

    history = load_history(days=7)

    # 7b. Market Intelligence (supply-demand + trend divergence)
    print("\n[7b] Market Intelligence...", file=sys.stderr)
    market = analyze_market(products, trend_data, history_days=3)
    sd_ratios = market["sd_ratios"]
    divergences = market["divergences"]
    if sd_ratios:
        top_sd = sorted(sd_ratios.items(), key=lambda x: -x[1]["ratio"])[:5]
        print(f"  Supply-Demand top categories:", file=sys.stderr)
        for cat, info in top_sd:
            print(f"    {info['label']} {cat}: ratio={info['ratio']} (demand={info['demand']} supply={info['supply']})", file=sys.stderr)
    if divergences:
        print(f"  Trend divergences: {len(divergences)} categories", file=sys.stderr)

    # Enrich products with market intelligence before scoring
    for p in passed:
        sd_bonus, sd_label, sd_info = get_product_sd_score(p, sd_ratios)
        p["sd_score"] = sd_bonus
        p["sd_label"] = sd_label
        p["sd_info"] = sd_info
        
        div_bonus, div_label, div_info = get_product_divergence_score(p, divergences)
        p["div_score"] = div_bonus
        p["div_label"] = div_label
        p["div_info"] = div_info

    # 7c. Gap Opportunity Detection (category-level gaps)
    print("\n[7c] Gap Opportunity Detection...", file=sys.stderr)
    gaps = analyze_gaps(trend_data, sd_ratios, products)
    if gaps:
        print(f"  🎯 {len(gaps)} gap opportunities found!", file=sys.stderr)
        for g in gaps[:3]:
            print(f"    {g['category']} → {g['gap_level']} (Amazon:{g['amazon_count']} products) Score:{g['score']}", file=sys.stderr)

    passed = score_all_products(passed, trend_data=trend_data, history=history)

    # Mark new vs repeat products based on 7-day history
    for p in passed:
        key = p.get("asin") or p.get("name", "").lower().strip()
        if key in history:
            p["is_new"] = False
            dates = [h["date"] for h in history[key]]
            p["first_seen"] = min(dates)[:10]  # YYYY-MM-DD
        else:
            p["is_new"] = True
            p["first_seen"] = scan_date

    # 7d. Limit event-based products (avoid single-event domination)
    print("\n[7d] Event Product Limiting...", file=sys.stderr)
    passed_before = len(passed)
    passed = limit_event_products(passed, max_per_event=2)
    print(f"  Before: {passed_before} → After: {len(passed)}", file=sys.stderr)

    # Assign channel tags
    for p in passed:
        assign_channel_tags(p)

    print(f"\n  Top 10:", file=sys.stderr)
    for p in passed[:10]:
        src_tags = ", ".join(p.get("sources", [])[:3])
        print(f"    [{p['score']:3d}] £{p['price']:.2f} {p['profit_margin']*100:.0f}% | {src_tags} | {p['name'][:45]}", file=sys.stderr)

    # Channel counts
    channel_counts = {}
    for p in passed:
        for ch in p.get("channel_tags", [p.get("channel", "other")]):
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

    stats = {
        "total_scanned": len(products),
        "passed_filter": len(passed),
        "rejected": len(rejected),
        "channels": channel_counts,
        "trend_categories": dict(top_cats),
        "supply_demand": {cat: info for cat, info in sorted(sd_ratios.items(), key=lambda x: -x[1]["ratio"])[:8]} if sd_ratios else {},
        "divergences": divergences if divergences else {},
        "gap_opportunities": len(gaps) if gaps else 0,
    }

    print(f"\n  Channels:", file=sys.stderr)
    for ch, cnt in sorted(channel_counts.items(), key=lambda x: -x[1]):
        print(f"    {ch}: {cnt}", file=sys.stderr)

    # Save (use scan_ts for unique filenames, scan_date for display)
    data = {
        "scan_date": scan_date, "scan_time": scan_time,
        "scan_ts": scan_ts,
        "stats": stats, "products": passed,
        "gaps": gaps if gaps else [],
        "trend_summary": {
            "top_categories": top_cats,
            "cross_validated": list(trend_data.get("cross_validated", {}).keys()),
            "demand_keywords": trend_data.get("demand_keywords", [])[:10],
            "season": trend_data.get("season", ""),
            "sources_scanned": list(trend_data.get("source_signals", {}).keys()),
        },
    }

    data_dir = BASE / "data" / "channels"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / f"{scan_ts}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (data_dir / f"{scan_ts}-rejected.json").write_text(json.dumps(rejected, ensure_ascii=False, indent=2), encoding="utf-8")
    (data_dir / f"{scan_ts}-trends.json").write_text(json.dumps(trend_data, ensure_ascii=False, indent=2), encoding="utf-8")

    hist_dir = BASE / "data" / "history"
    hist_dir.mkdir(parents=True, exist_ok=True)
    hist_data = [{"asin": p.get("asin",""), "name": p.get("name",""), "price": p.get("price",0),
                  "rank": p.get("rank"), "reviews": p.get("reviews"), "score": p.get("score",0),
                  "sources": p.get("sources",[]), "channel": p.get("channel","")} for p in passed]
    (hist_dir / f"{scan_ts}.json").write_text(json.dumps(hist_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # HTML output: only platform page (generate_platform.py handles this), skip per-scan v2

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  ✅ {len(passed)} scored products | {len(channel_counts)} channels", file=sys.stderr)
    print(f"  {'='*60}\n", file=sys.stderr)

    print(json.dumps({"date": scan_date, "scanned": len(products), "passed": len(passed),
                       "rejected": len(rejected), "channels": channel_counts,
                       "top_categories": dict(top_cats)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
