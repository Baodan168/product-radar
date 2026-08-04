#!/usr/bin/env python3
"""
BrowserAct Fetcher — Wrapper for BrowserAct CLI to search Amazon UK.

Provides structured product data via BrowserAct's Chrome mode.
Falls back gracefully if BrowserAct is unavailable.

Usage:
    from browseract_fetcher import search_amazon
    products = search_amazon("wireless mouse", max_products=5)
"""

import json
import re
import subprocess
import sys
import time
import threading
from pathlib import Path

BROWSER_ID = "chrome_local_103642719185797272"
SESSION_PREFIX = "radar"
TIMEOUT_NAV = 10
TIMEOUT_EVAL = 8
TIMEOUT_CLICK = 5
MAX_RETRIES = 0  # 失败即弃：BrowserAct 不稳定时重试会把 cron 600s 预算拖爆（2026-08-03 实测 5 通道 × 重试 ≈ 500s）
MAX_CONCURRENT = 6  # Max concurrent Chrome sessions

# Semaphore for concurrency control (queue with longer timeout instead of skip)
_semaphore = threading.Semaphore(MAX_CONCURRENT)

# JS to extract products from Amazon search/category pages
EXTRACT_JS = r"""(() => {
  const items = [];
  const blocks = document.querySelectorAll("[data-component-type=s-search-result]");
  blocks.forEach(el => {
    const asin = el.getAttribute("data-asin") || "";
    if (!asin) return;
    
    const h2 = el.querySelector("h2");
    const title = h2 ? h2.textContent.trim() : "";
    if (!title) return;
    
    // Price: try multiple selectors
    let price = 0;
    const priceEl = el.querySelector(".a-price .a-offscreen");
    if (priceEl) {
      const m = priceEl.textContent.match(/[\d.]+/);
      if (m) price = parseFloat(m[0]);
    }
    if (!price) {
      const whole = el.querySelector(".a-price-whole");
      const frac = el.querySelector(".a-price-fraction");
      if (whole) {
        const w = whole.textContent.replace(/[^\d]/g, "");
        const f = frac ? frac.textContent.replace(/[^\d]/g, "") : "00";
        price = parseFloat(w + "." + f);
      }
    }
    
    // Rating
    let rating = 0;
    const ratingEl = el.querySelector("[aria-label*='out of']");
    if (ratingEl) {
      const m = ratingEl.getAttribute("aria-label").match(/([\d.]+)\s*out/);
      if (m) rating = parseFloat(m[1]);
    }
    
    // Reviews
    let reviews = 0;
    const reviewEl = el.querySelector("[aria-label*='ratings']");
    if (reviewEl) {
      const txt = reviewEl.textContent.replace(/[(),]/g, "").trim();
      if (txt.endsWith("K")) reviews = Math.round(parseFloat(txt) * 1000);
      else { const n = parseInt(txt); if (!isNaN(n)) reviews = n; }
    }
    
    // Image
    let imgUrl = "";
    const img = el.querySelector("img.s-image");
    if (img) imgUrl = img.src;
    
    if (title && price > 0) {
      // Auto-detect CNY and convert to GBP (Amazon shows CNY for Chinese IP)
      // ¥ symbol or prices > 100 on Amazon UK usually means CNY
      let gbpPrice = price;
      const priceText = priceEl ? priceEl.textContent : '';
      if (priceText.includes('¥') || priceText.includes('￥') || (price > 50 && !priceText.includes('£'))) {
        gbpPrice = Math.round(price / 9.2 * 100) / 100;  // CNY → GBP rate 9.2 (fixed)
      }
      items.push({
        asin: asin,
        name: title.substring(0, 120),
        price: gbpPrice,
        reviews: reviews,
        rating: rating,
        image_url: imgUrl
      });
    }
  });
  return JSON.stringify(items);
})()"""


def _run_browseract(args, timeout=15, stdin_data=None):
    """Run a browseract CLI command, return (stdout, returncode)."""
    cmd = ["browser-act"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=stdin_data,
        )
        return result.stdout, result.returncode
    except subprocess.TimeoutExpired:
        return "", 1
    except FileNotFoundError:
        return "", 1


def _cleanup_session(session):
    """Force close a BrowserAct session."""
    try:
        _run_browseract(["session", "close", session], timeout=5)
    except Exception:
        pass


def _cleanup_stale_sessions():
    """Clean up any stale radar sessions."""
    try:
        stdout, rc = _run_browseract(["session", "list"], timeout=5)
        if rc == 0 and stdout:
            for line in stdout.strip().split('\n'):
                if SESSION_PREFIX in line or 'amazon_' in line or 'page_' in line:
                    parts = line.split()
                    session_name = parts[0] if parts else ''
                    if session_name and '=' in session_name:
                        session_name = session_name.split('=')[1] if '=' in session_name else session_name
                    # Extract session name from "session_name=xxx" format
                    for part in parts:
                        if part.startswith('session_name='):
                            session_name = part.split('=')[1]
                            break
                    if session_name:
                        _cleanup_session(session_name)
    except Exception:
        pass

# Clean stale sessions on import
_cleanup_stale_sessions()


def search_amazon(keyword, max_products=5, category="Search", retry=0):
    """Search Amazon UK via BrowserAct, return products in radar-compatible format.
    
    Returns list of dicts with keys matching _parse_amazon_page output.
    Returns empty list on any failure (caller should fallback).
    """
    import urllib.parse
    
    session = f"{SESSION_PREFIX}_{hash(keyword) % 10000}_{int(time.time()) % 1000}"
    search_url = f"https://www.amazon.co.uk/s?k={urllib.parse.quote(keyword)}"
    
    # Acquire semaphore for concurrency control (wait up to 2 min instead of skipping)
    acquired = _semaphore.acquire(timeout=120)
    if not acquired:
        print(f"  ⚠️ BrowserAct排队超时，跳过 '{keyword}'", file=sys.stderr)
        return []
    
    try:
        # 1. Open search page
        _, rc = _run_browseract(
            ["--session", session, "browser", "open", BROWSER_ID, search_url],
            timeout=TIMEOUT_NAV,
        )
        if rc != 0:
            if retry < MAX_RETRIES:
                print(f"  ⚠️ BrowserAct open failed for '{keyword}', retry {retry+1}...", file=sys.stderr)
                _cleanup_session(session)
                time.sleep(1)
                return search_amazon(keyword, max_products, category, retry + 1)
            return []
        
        # 2. Accept cookies (if present, ignore failure)
        _run_browseract(["--session", session, "click", "8"], timeout=TIMEOUT_CLICK)
        
        # 3. Extract products via JS eval
        stdout, rc = _run_browseract(
            ["--session", session, "eval", "--stdin"],
            timeout=TIMEOUT_EVAL,
            stdin_data=EXTRACT_JS,
        )
        if rc != 0 or not stdout.strip():
            if retry < MAX_RETRIES:
                print(f"  ⚠️ BrowserAct eval failed for '{keyword}', retry {retry+1}...", file=sys.stderr)
                _cleanup_session(session)
                time.sleep(1)
                return search_amazon(keyword, max_products, category, retry + 1)
            return []
        
        raw_items = json.loads(stdout)
        
        # 4. Convert to radar-compatible format
        products = []
        for i, item in enumerate(raw_items[:max_products]):
            reviews = item.get("reviews", 0)
            rating = item.get("rating", 0)
            products.append({
                "asin": item["asin"],
                "name": item["name"],
                "price": item["price"],
                "reviews": reviews,
                "rating": rating,
                "rank": i + 1,
                "category": category,
                "channel": "keyword_search",
                "channel_name": "关键词搜索(BrowserAct)",
                "review_info": f"{reviews} reviews, {rating}★" if rating else f"{reviews} reviews",
                "amazon_url": f"https://www.amazon.co.uk/dp/{item['asin']}",
                "image_url": item.get("image_url", ""),
            })
        
        return products
    
    except (json.JSONDecodeError, KeyError, Exception) as e:
        if retry < MAX_RETRIES:
            print(f"  ⚠️ BrowserAct error for '{keyword}': {e}, retry {retry+1}...", file=sys.stderr)
            time.sleep(1)
            return search_amazon(keyword, max_products, category, retry + 1)
        print(f"  ⚠️ BrowserAct failed for '{keyword}': {e}", file=sys.stderr)
        return []
    
    finally:
        # Always close session
        _cleanup_session(session)
        if acquired:
            _semaphore.release()


def fetch_page_html(url, retry=0):
    """Fetch any page HTML via BrowserAct (for category pages).
    
    Returns HTML string, or empty string on failure.
    """
    import hashlib
    session = f"page_{hashlib.md5(url.encode()).hexdigest()[:8]}_{int(time.time()) % 1000}"
    
    acquired = _semaphore.acquire(timeout=120)
    if not acquired:
        print(f"  ⚠️ BrowserAct排队超时，跳过页面拉取", file=sys.stderr)
        return ""
    
    try:
        # Open page
        _, rc = _run_browseract(
            ["--session", session, "browser", "open", BROWSER_ID, url],
            timeout=TIMEOUT_NAV,
        )
        if rc != 0:
            if retry < MAX_RETRIES:
                _cleanup_session(session)
                time.sleep(1)
                return fetch_page_html(url, retry + 1)
            return ""
        
        # Accept cookies
        _run_browseract(["--session", session, "click", "8"], timeout=TIMEOUT_CLICK)
        
        # Get page HTML
        stdout, rc = _run_browseract(
            ["--session", session, "eval", "--stdin"],
            timeout=TIMEOUT_EVAL,
            stdin_data="document.documentElement.outerHTML",
        )
        
        if rc == 0 and stdout and len(stdout) > 1000:
            html = stdout.strip()
            if html.startswith('"') and html.endswith('"'):
                html = json.loads(html)
            return html
        
        if retry < MAX_RETRIES:
            _cleanup_session(session)
            time.sleep(1)
            return fetch_page_html(url, retry + 1)
        return ""
    
    except Exception as e:
        if retry < MAX_RETRIES:
            time.sleep(1)
            return fetch_page_html(url, retry + 1)
        print(f"  ⚠️ BrowserAct page fetch failed: {e}", file=sys.stderr)
        return ""
    
    finally:
        _cleanup_session(session)
        if acquired:
            _semaphore.release()


def is_available():
    """Check if BrowserAct CLI and Chrome browser are available."""
    try:
        stdout, rc = _run_browseract(["--version"], timeout=5)
        if rc != 0:
            return False
        stdout, rc = _run_browseract(["browser", "list"], timeout=5)
        return BROWSER_ID in stdout
    except Exception:
        return False


if __name__ == "__main__":
    print("=== BrowserAct Fetcher Test ===")
    print(f"Available: {is_available()}")
    print(f"Max concurrent: {MAX_CONCURRENT}")
    print(f"Max retries: {MAX_RETRIES}")
    
    if "--test" in sys.argv:
        keyword = sys.argv[sys.argv.index("--test") + 1] if len(sys.argv) > sys.argv.index("--test") + 1 else "wireless mouse"
        print(f"\nSearching: {keyword}")
        products = search_amazon(keyword, max_products=5)
        print(f"Found: {len(products)} products")
        for p in products:
            print(f"  £{p['price']:.2f} | {p['name'][:60]} | {p['reviews']} reviews")
