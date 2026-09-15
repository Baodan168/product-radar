#!/usr/bin/env python3
"""
Keyword Scanner — Three-source keyword-driven product discovery.

Sources:
1. Discovery keywords (from LLM trend analysis, saved as pending_keywords.json)
2. Festival keywords (from Festival Planner, filtered by sea freight deadline ≤30 days)
3. Regular radar scan (existing, in run_scan_v2.py)

This module handles sources 1 and 2: search Amazon UK for keywords and return products.
"""

import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent

# Import from existing modules
sys.path.insert(0, str(BASE))
from sources.amazon_uk import _curl_fetch, _parse_amazon_page, CATEGORY_VALIDATORS


def load_discovery_keywords():
    """Load keywords from the latest discovery JSON.
    
    Returns list of dicts: [{"keyword": "...", "keyword_cn": "...", "amazon_keyword": "...", "source": "discovery"}]
    """
    disc_dir = BASE / "data" / "discovery"
    if not disc_dir.exists():
        return []
    
    # Find the latest discovery JSON (not seasonal_keywords.json)
    files = sorted([f for f in disc_dir.glob("*.json") if "seasonal" not in f.name])
    if not files:
        return []
    
    latest = files[-1]
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    
    keywords = []
    for insight in data.get("insights", []):
        kw = insight.get("amazon_keyword") or insight.get("keyword", "")
        if kw:
            keywords.append({
                "keyword": kw,
                "keyword_cn": insight.get("keyword_cn", ""),
                "source": "discovery",
                "score": insight.get("signal_scores", {}).get("final", 0),
            })
    
    return keywords


def load_festival_keywords():
    """Load keywords from Festival Planner events within truck (卡航/快铁) freight window.
    
    Truck freight deadline = festival_date - (33 + 14) = festival_date - 47 days
    Lee's products are mostly light/small items, rarely use sea freight.
    Only include events where truck deadline is within 30 days from today.
    
    Returns list of dicts: [{"keyword": "...", "keyword_cn": "...", "source": "festival", "event": "...", "deadline": "..."}]
    """
    from festival_engine import load_festivals, get_deadlines, LOGISTICS_MODES
    
    festivals = load_festivals()
    if not festivals:
        return []
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    keywords = []
    seen_kws = set()
    
    for f in festivals:
        deadlines = get_deadlines(f)
        truck = deadlines.get("truck", {})
        days_left = truck.get("days_from_today", 999)
        
        # Only include events where truck deadline is approaching (0-30 days away)
        # Skip events too far away or already past deadline
        if days_left > 30 or days_left < 0:
            continue
        
        event_name = f.get("name", "")
        
        for product in f.get("products", []):
            # Use the Amazon keywords from the product
            for kw in product.get("keywords", [])[:2]:  # Top 2 keywords per product
                kw_lower = kw.lower().strip()
                if kw_lower not in seen_kws and len(kw_lower) >= 4:
                    seen_kws.add(kw_lower)
                    keywords.append({
                        "keyword": kw,
                        "keyword_cn": product.get("sku", ""),
                        "source": "festival",
                        "event": event_name,
                        "event_icon": f.get("icon", "📅"),
                        "deadline": truck.get("date", ""),
                        "days_left": days_left,
                    })
    
    # Limit to top 10 keywords to avoid too many searches
    return keywords[:10]


def _keyword_playwright_fetch(search_url, cloackchrome_path=None):
    """Fetch Amazon search page using a dedicated Playwright browser (not the shared singleton).
    Launches and closes per call — avoids the greenlet thread conflict in the shared CloakBrowser.
    Used for keyword searches (5-10 per scan), so overhead is acceptable.

    If sync_playwright fails (e.g. inside asyncio loop), falls back to a subprocess script.
    """
    import os
    if not cloackchrome_path:
        from sources.amazon_uk import CLOAKBROWSER_CHROME
        cloackchrome_path = CLOAKBROWSER_CHROME

    if not os.path.exists(cloackchrome_path):
        return ""

    # Primary: direct sync_playwright (works in cron/CLI, fails inside asyncio)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=cloackchrome_path, headless=True)
            try:
                ctx = browser.new_context(
                    locale='en-GB',
                    timezone_id='Europe/London',
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                )
                # Set GBP cookies so Amazon returns UK prices instead of CNY
                ctx.add_cookies([
                    {"name": "lc-main", "url": "https://www.amazon.co.uk", "value": "en_GB"},
                    {"name": "i18n-prefs", "url": "https://www.amazon.co.uk", "value": "GBP"},
                ])
                page = ctx.new_page()
                try:
                    page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
                    page.wait_for_timeout(3000)
                    html = page.content()
                    return html
                finally:
                    page.close()
            finally:
                browser.close()
    except Exception as e:
        err_str = str(e)
        # If asyncio loop error, fall through to subprocess approach
        if "asyncio" in err_str or "Sync API" in err_str:
            pass
        else:
            print(f"  dedicated playwright error: {err_str[:80]}", file=sys.stderr)
            return ""

    # Fallback: run in subprocess (bypasses asyncio context issue)
    import subprocess as sp
    import json
    try:
        script = (
            "import sys, json; sys.path.insert(0, '.'); "
            "from sources.amazon_uk import CLOAKBROWSER_CHROME; "
            "from playwright.sync_api import sync_playwright; "
            f"url = {json.dumps(search_url)}; "
            "with sync_playwright() as p: "
            "  b = p.chromium.launch(executable_path=CLOAKBROWSER_CHROME, headless=True); "
            "  try: "
            "    ctx = b.new_context(locale='en-GB', timezone_id='Europe/London', "
            "      user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'); "
            "    ctx.add_cookies(["
            "      {'name':'lc-main','url':'https://www.amazon.co.uk','value':'en_GB'},"
            "      {'name':'i18n-prefs','url':'https://www.amazon.co.uk','value':'GBP'},"
            "    ]); "
            "    p2 = ctx.new_page(); "
            "    try: "
            "      p2.goto(url, timeout=30000, wait_until='domcontentloaded'); "
            "      p2.wait_for_timeout(3000); "
            "      print(p2.content()) "
            "    finally: p2.close() "
            "  finally: b.close()"
        )
        result = sp.run(
            ["python3", "-c", script],
            capture_output=True, text=True, timeout=60,
            cwd=str(__import__('pathlib').Path(__file__).parent)
        )
        if result.stdout and len(result.stdout) > 500:
            return result.stdout
    except Exception as e:
        print(f"  subprocess playwright error: {e}", file=sys.stderr)

    return ""


def _keyword_curl_fetch(search_url):
    """Fetch Amazon search page with multiple fallback strategies.
    Lightweight -- meant for keyword searches (5-10 per scan), avoids the broken CloakBrowser singleton.
    """
    import subprocess as sp
    from sources.amazon_uk import _is_valid_response, USER_AGENT, GBP_COOKIES

    # Strategy 1: Direct curl with desktop + mobile UAs (search pages less aggressively blocked)
    ua_list = [
        USER_AGENT,
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.104 Mobile Safari/537.36",
    ]
    for ua in ua_list:
        try:
            result = sp.run(
                ["curl", "-s", "-L", "--compressed",
                 "--connect-timeout", "8", "--max-time", "20",
                 "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                 "-H", "Accept-Language: en-GB,en;q=0.9",
                 "-H", "Accept-Encoding: gzip, deflate, br",
                 "-H", "Cache-Control: no-cache",
                 "-H", "Pragma: no-cache",
                 "-H", f"User-Agent: {ua}",
                 "-b", GBP_COOKIES,
                 search_url],
                capture_output=True, text=True, timeout=30
            )
            if _is_valid_response(result.stdout):
                print(f"  curl OK (len={len(result.stdout)})", file=sys.stderr)
                return result.stdout
        except Exception:
            continue

    # Strategy 2: requests with browser-like headers
    try:
        import requests as req
        headers = {
            "User-Agent": ua_list[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        resp = req.get(search_url, headers=headers, timeout=20, allow_redirects=True)
        if resp.status_code == 200 and _is_valid_response(resp.text):
            print(f"  requests OK (len={len(resp.text)})", file=sys.stderr)
            return resp.text
    except Exception:
        pass

    return ""


def search_amazon_by_keyword(keyword, max_products=5):
    """Search Amazon UK for a keyword and return parsed products.

    Fallback chain:
    1. _curl_fetch → curl_cffi → ScraperAPI → CloakBrowser
    2. _keyword_playwright_fetch (dedicated browser, separate from singleton)
    3. BrowserAct (slow, different fingerprint)
    """
    search_url = f"https://www.amazon.co.uk/s?k={urllib.parse.quote(keyword)}"

    # Try 1: _curl_fetch (CloakBrowser with greenlet fallback now)
    html = _curl_fetch(search_url)
    if not html:
        # Try 2: dedicated Playwright (separate from the shared singleton)
        html = _keyword_playwright_fetch(search_url)

    if html:
        products = _parse_amazon_page(html, "Search", "keyword_search")
        if products:
            return products[:max_products]

    # Try 3: BrowserAct (different fingerprint, slow)
    try:
        from browseract_fetcher import search_amazon as ba_search
        products = ba_search(keyword, max_products=max_products, category="Search")
        if products:
            return products
    except Exception:
        pass

    return []


def _dedicated_browser_search(search_url, browser):
    """Search Amazon using a dedicated browser instance (not the shared singleton).
    Reuses the browser across calls — must be pre-warmed.
    
    Uses homepage search form submission (not direct s?k=) to bypass Amazon's
    search page blocking.
    """
    try:
        ctx = browser.new_context(
            locale='en-GB', timezone_id='Europe/London',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        )
        # Set GBP cookies so Amazon returns UK prices instead of CNY
        ctx.add_cookies([
            {"name": "lc-main", "url": "https://www.amazon.co.uk", "value": "en_GB"},
            {"name": "i18n-prefs", "url": "https://www.amazon.co.uk", "value": "GBP"},
        ])
        page = ctx.new_page()
        try:
            # Step 1: Navigate to homepage first (establishes session)
            page.goto('https://www.amazon.co.uk', timeout=30000, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)

            # Step 2: Extract keyword from search_url and submit via search form
            import urllib.parse as up
            parsed = up.urlparse(search_url)
            kw = up.parse_qs(parsed.query).get('k', [''])[0]

            if kw:
                # Fill search box and submit form (mimics real user behavior)
                page.evaluate(f'(k) => {{ const el = document.querySelector("[name=field-keywords]"); if(el) {{ el.value = k; }} }}', kw)
                page.wait_for_timeout(300)
                page.evaluate('() => { const f = document.querySelector("form[name=\'site-search\']"); if(f) f.submit(); }')
                page.wait_for_timeout(5000)
            else:
                # Fallback: direct navigation
                page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
                page.wait_for_timeout(3000)

            html = page.content()
            return html
        finally:
            page.close()
    except Exception as e:
        print(f"  browser search error: {e}", file=sys.stderr)
        return ""


def _keyword_cloak_fetch(search_url, browser):
    """Search Amazon using CloakBrowser — direct s?k= navigation, no form submission needed.
    Reuses the pre-warmed browser across calls.
    """
    try:
        ctx = browser.new_context(
            locale='en-GB', timezone_id='Europe/London',
        )
        # Set GBP cookies so Amazon returns UK prices instead of CNY
        ctx.add_cookies([
            {"name": "lc-main", "url": "https://www.amazon.co.uk", "value": "en_GB"},
            {"name": "i18n-prefs", "url": "https://www.amazon.co.uk", "value": "GBP"},
        ])
        page = ctx.new_page()
        try:
            page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            html = page.content()
            return html
        finally:
            page.close()
    except Exception as e:
        print(f"  cloak fetch error: {e}", file=sys.stderr)
        return ""


def run_keyword_scan(max_discovery_kws=5, max_festival_kws=5, max_products_per_kw=10, max_reviews=200):
    """Run keyword-based scan from discovery + festival sources.

    Launches a dedicated Playwright browser, warms it up, then searches all keywords.
    Avoids both greenlet conflict (fresh browser) and 503 (warmed session).

    Args:
        max_products_per_kw: Fetch more products per keyword to find low-competition ones
        max_reviews: Only keep products with reviews below this threshold (default 200)

    Returns list of products tagged with their keyword source.
    """
    # Load keywords from both sources
    disc_kws = load_discovery_keywords()[:max_discovery_kws]
    fest_kws = load_festival_keywords()[:max_festival_kws]

    # 2026-09-15: 节日词排前面。UK动态预算（_remaining(reserve=280)）只给关键词
    # 步骤71-80s，21次扫描里20次在末尾超时截断——垫底的永远是节日词（按截柜日
    # 排序，最后=截柜最远的事件，如bonfire scarf/halloween stickers连续4天被砍）。
    # 发现词明天会换新，节日词有硬窗口期，砍发现词尾部的损失小得多。
    all_kws = fest_kws + disc_kws
    if not all_kws:
        print("  ℹ️ No pending keywords from discovery or festival", file=sys.stderr)
        return []

    print(f"\n🔑 Keyword Scan: {len(disc_kws)} discovery + {len(fest_kws)} festival keywords", file=sys.stderr)

    # Try primary: Playwright sync API directly (works when no asyncio loop)
    browser = None
    try:
        try:
            from sources.amazon_uk import CLOAKBROWSER_CHROME
            from playwright.sync_api import sync_playwright
            p = sync_playwright().start()
            browser = p.chromium.launch(executable_path=CLOAKBROWSER_CHROME, headless=True)

            # Now search all keywords with the warmed browser
            all_products = []
            seen_asins = set()

            for kw_info in all_kws:
                keyword = kw_info["keyword"]
                source = kw_info["source"]

                print(f"  🔍 [{source}] {keyword}...", file=sys.stderr, end="")
                search_url = f"https://www.amazon.co.uk/s?k={urllib.parse.quote(keyword)}"

                html = _dedicated_browser_search(search_url, browser)
                if not html or len(html) < 2000:
                    print(" → blocked/empty", file=sys.stderr)
                    continue

                products = _parse_amazon_page(html, "Search", "keyword_search")
                if not products:
                    print(" → 0 parsed", file=sys.stderr)
                    continue

                # Filter: only keep products with reviews < max_reviews
                filtered = [p for p in products if p.get("reviews", 0) < max_reviews]

                # Tag products with keyword source info
                for p in filtered:
                    asin = p.get("asin", "")
                    if asin in seen_asins:
                        continue
                    seen_asins.add(asin)

                    p["keyword_source"] = source
                    p["matched_keyword"] = keyword
                    p["channel"] = "keyword_search"
                    p["channel_name"] = f"关键词搜索({source})"

                    if source == "festival":
                        p["festival_event"] = kw_info.get("event", "")
                        p["festival_icon"] = kw_info.get("event_icon", "📅")
                        p["festival_deadline"] = kw_info.get("deadline", "")
                        p["is_event"] = True
                        if "节日" not in p.get("sources", []):
                            p.setdefault("sources", []).append(f"📅 {kw_info.get('event', '节日')}")
                    else:
                        if "趋势发现" not in p.get("sources", []):
                            p.setdefault("sources", []).append("趋势发现")

                    all_products.append(p)

                kept = len(filtered)
                total = len(products)
                print(f" → {total} found, {kept} kept", file=sys.stderr)

            print(f"  ✅ Keyword scan total: {len(all_products)} products", file=sys.stderr)
            return all_products

        except Exception as e:
            err_str = str(e)
            print(f"  ⚠️ Keyword scan browser failed ({err_str[:80]})", file=sys.stderr)

        # Fallback 1: re-run in subprocess (isolated from asyncio context)
        print("  ↻ Retrying keyword scan in subprocess (isolated from asyncio)...", file=sys.stderr)
        sub_result = _run_keyword_scan_subprocess(max_discovery_kws, max_festival_kws,
                                                  max_products_per_kw, max_reviews)
        if sub_result:
            return sub_result

        # Fallback 2: per-keyword subprocess Playwright → curl
        print("  ↻ Falling back to per-keyword search (subprocess playwright → curl)...", file=sys.stderr)
        all_products = []
        seen_asins = set()
        for kw_info in all_kws:
            keyword = kw_info["keyword"]
            source = kw_info["source"]
            search_url = f"https://www.amazon.co.uk/s?k={urllib.parse.quote(keyword)}"

            # Strategy 1: subprocess Playwright (bypasses asyncio conflict)
            html = ""
            print(f"  🔍 [{source}] {keyword} (playwright)...", file=sys.stderr, end="")
            html = _keyword_playwright_fetch(search_url)

            # Strategy 2: curl fallback
            if not html or len(html) < 2000:
                print("(subproc failed) → curl...", file=sys.stderr, end="")
                html = _keyword_curl_fetch(search_url)

            if not html or len(html) < 2000:
                print(" → blocked/empty", file=sys.stderr)
                continue
            products = _parse_amazon_page(html, "Search", "keyword_search")
            if not products:
                print(" → 0 parsed", file=sys.stderr)
                continue
            filtered = [p for p in products if p.get("reviews", 0) < max_reviews]
            for p in filtered:
                asin = p.get("asin", "")
                if asin in seen_asins:
                    continue
                seen_asins.add(asin)
                p["keyword_source"] = source
                p["matched_keyword"] = keyword
                p["channel"] = "keyword_search"
                p["channel_name"] = f"关键词搜索({source})"
                if source == "festival":
                    p["festival_event"] = kw_info.get("event", "")
                    p["festival_icon"] = kw_info.get("event_icon", "📅")
                    p["festival_deadline"] = kw_info.get("deadline", "")
                    p["is_event"] = True
                    if "节日" not in p.get("sources", []):
                        p.setdefault("sources", []).append(f"📅 {kw_info.get('event', '节日')}")
                else:
                    if "趋势发现" not in p.get("sources", []):
                        p.setdefault("sources", []).append("趋势发现")
                all_products.append(p)
            kept = len(filtered)
            total = len(products)
            print(f" → {total} found, {kept} kept", file=sys.stderr)
        if all_products:
            print(f"  ✅ Keyword scan (per-keyword fallback) total: {len(all_products)} products", file=sys.stderr)
        else:
            print(f"  ℹ️ No products found via fallback", file=sys.stderr)
        return all_products

    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass


def _run_keyword_scan_subprocess(max_discovery_kws=5, max_festival_kws=5,
                                  max_products_per_kw=10, max_reviews=200):
    """Run the full keyword scan in a subprocess to bypass asyncio context.

    run_scan_v2.py sets up an asyncio event loop (via BrowserAct/curl_cffi)
    which crashes both playwright.sync_api and cloakbrowser.launch().
    Running in a subprocess gives a clean Python process with no event loop.
    """
    import json, subprocess, sys
    script = (
        "import sys, json; sys.path.insert(0, %s); "
        "from keyword_scanner import run_keyword_scan; "
        "r = run_keyword_scan(%d, %d, %d, %d); "
        "print(json.dumps(r))"
    ) % (json.dumps(str(BASE)), max_discovery_kws, max_festival_kws,
         max_products_per_kw, max_reviews)

    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=300,
            cwd=str(BASE)
        )
        if result.returncode != 0:
            err = result.stderr.strip() or f"exit code {result.returncode}"
            print(f"  ⚠️ Subprocess keyword scan failed: {err[:120]}", file=sys.stderr)
            return []
        if not result.stdout or len(result.stdout) < 20:
            print("  ℹ️ Subprocess keyword scan returned empty", file=sys.stderr)
            return []
        products = json.loads(result.stdout)
        if products:
            print(f"  ✅ Subprocess keyword scan: {len(products)} products", file=sys.stderr)
        return products
    except subprocess.TimeoutExpired:
        print("  ⏰ Subprocess keyword scan timed out (>300s)", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  ⚠️ Subprocess keyword scan error: {e}", file=sys.stderr)
        return []


if __name__ == "__main__":
    print("=== Keyword Scanner Test ===")
    
    disc_kws = load_discovery_keywords()
    print(f"\n📋 Discovery keywords: {len(disc_kws)}")
    for kw in disc_kws[:3]:
        print(f"  - {kw['keyword']} (score: {kw.get('score', 0)})")
    
    fest_kws = load_festival_keywords()
    print(f"\n📅 Festival keywords (sea deadline ≤30d): {len(fest_kws)}")
    for kw in fest_kws[:5]:
        print(f"  - {kw['keyword']} ({kw['event']}, deadline: {kw['deadline']}, {kw['days_left']}d)")
    
    if "--run" in sys.argv:
        products = run_keyword_scan()
        print(f"\n📊 Found {len(products)} products")
        for p in products[:5]:
            print(f"  [{p.get('keyword_source', '?')}] £{p['price']} | {p['name'][:60]}")
