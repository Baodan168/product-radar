#!/usr/bin/env python3
"""Amazon UK data fetcher v2 - New Releases + BSR with channel tagging"""
import json, subprocess, re, sys, random, os, threading, time, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent.parent
CONFIG = json.loads((BASE / "config.json").read_text())

# Amazon UK URLs with channel type
AMAZON_URLS = {
    # === NEW RELEASES ===
    "Kitchen|new_releases": "https://www.amazon.co.uk/gp/new-releases/kitchen/",
    "Garden|new_releases": "https://www.amazon.co.uk/gp/new-releases/garden/",
    "DIY|new_releases": "https://www.amazon.co.uk/gp/new-releases/diy/",
    "Sports|new_releases": "https://www.amazon.co.uk/gp/new-releases/sports/",
    "Bathroom|new_releases": "https://www.amazon.co.uk/gp/new-releases/bathroom/",
    "Cleaning|new_releases": "https://www.amazon.co.uk/gp/new-releases/cleaning/",
    "Office|new_releases": "https://www.amazon.co.uk/gp/new-releases/stationery-office/",
    "Lighting|new_releases": "https://www.amazon.co.uk/gp/new-releases/lighting/",
    "Storage|new_releases": "https://www.amazon.co.uk/gp/new-releases/kitchen/storage-accessories/",
    "Crafts|new_releases": "https://www.amazon.co.uk/gp/new-releases/diy-craft-tools/",
    "Bedding|new_releases": "https://www.amazon.co.uk/gp/new-releases/bedding/",
    "Pets|new_releases": "https://www.amazon.co.uk/gp/new-releases/pet-supplies/",
    "Home|new_releases": "https://www.amazon.co.uk/gp/new-releases/home/",
    "Phone|new_releases": "https://www.amazon.co.uk/gp/new-releases/mobile-phone-accessories/",
    "Tech|new_releases": "https://www.amazon.co.uk/gp/new-releases/computers-accessories/",
    "Travel|new_releases": "https://www.amazon.co.uk/gp/new-releases/sport-leisure/travel-accessories/",
    "Party|new_releases": "https://www.amazon.co.uk/gp/new-releases/party-supplies-balloons/",
    # === BESTSELLERS (BSR) ===
    "Kitchen|bsr": "https://www.amazon.co.uk/gp/bestsellers/kitchen/",
    "Garden|bsr": "https://www.amazon.co.uk/gp/bestsellers/garden/",
    "DIY|bsr": "https://www.amazon.co.uk/gp/bestsellers/diy/",
    "Sports|bsr": "https://www.amazon.co.uk/gp/bestsellers/sports/",
    "Home|bsr": "https://www.amazon.co.uk/gp/bestsellers/home/",
    "Crafts|bsr": "https://www.amazon.co.uk/gp/bestsellers/diy-craft-tools/",
    "Office|bsr": "https://www.amazon.co.uk/gp/bestsellers/stationery-office/",
    "Bathroom|bsr": "https://www.amazon.co.uk/gp/bestsellers/bathroom/",
    "Cleaning|bsr": "https://www.amazon.co.uk/gp/bestsellers/cleaning/",
    "Lighting|bsr": "https://www.amazon.co.uk/gp/bestsellers/lighting/",
    "Bedding|bsr": "https://www.amazon.co.uk/gp/bestsellers/bedding/",
    "Pets|bsr": "https://www.amazon.co.uk/gp/bestsellers/pet-supplies/",
    "Phone|bsr": "https://www.amazon.co.uk/gp/bestsellers/mobile-phone-accessories/",
    "Tech|bsr": "https://www.amazon.co.uk/gp/bestsellers/computers-accessories/",
    # === MOST WISHED FOR (需求信号) ===
    "Kitchen|wished": "https://www.amazon.co.uk/gp/most-wished-for/kitchen/",
    "Garden|wished": "https://www.amazon.co.uk/gp/most-wished-for/garden/",
    "DIY|wished": "https://www.amazon.co.uk/gp/most-wished-for/diy/",
    "Sports|wished": "https://www.amazon.co.uk/gp/most-wished-for/sports/",
    "Home|wished": "https://www.amazon.co.uk/gp/most-wished-for/home/",
    "Pets|wished": "https://www.amazon.co.uk/gp/most-wished-for/pet-supplies/",
    "Office|wished": "https://www.amazon.co.uk/gp/most-wished-for/stationery-office/",
    "Phone|wished": "https://www.amazon.co.uk/gp/most-wished-for/mobile-phone-accessories/",
    # === GIFT IDEAS (送礼需求) ===
    "Kitchen|gifts": "https://www.amazon.co.uk/gp/gifts/kitchen/",
    "Garden|gifts": "https://www.amazon.co.uk/gp/gifts/garden/",
    "DIY|gifts": "https://www.amazon.co.uk/gp/gifts/diy/",
    "Home|gifts": "https://www.amazon.co.uk/gp/gifts/home/",
    # === MOVERS & SHAKERS (排名飙升) ===
    "Kitchen|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/kitchen/",
    "Garden|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/garden/",
    "DIY|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/diy/",
    "Sports|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/sports/",
    "Home|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/home/",
    "Pets|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/pet-supplies/",
    "Office|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/stationery-office/",
    "Bathroom|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/bathroom/",
    "Lighting|movers_shakers": "https://www.amazon.co.uk/gp/movers-and-shakers/lighting/",
}

GBP_COOKIES = "lc-main=en_GB; i18n-prefs=GBP"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

CHANNEL_NAMES = {
    "new_releases": "Amazon新品榜",
    "bsr": "Amazon畅销榜",
    "wished": "Amazon心愿榜",
    "gifts": "Amazon送礼榜",
    "movers_shakers": "Amazon飙升榜",
}

# Category validation keywords — product name must contain at least one
CATEGORY_VALIDATORS = {
    "Kitchen": ["kitchen", "cooking", "baking", "utensil", "gadget", "spice", "mug", "cup", "pan", "pot", "chop", "peel", "slice", "grater", "measuring", "timer", "tray", "bowl", "plate", "coffee", "tea", "stove", "oven", "dish", "cutlery", "ladle", "whisk", "tongs", "colander", "sieve"],
    "Garden": ["garden", "outdoor", "plant", "flower", "patio", "bbq", "grill", "solar", "bird", "hose", "watering", "lawn", "hedge", "seed", "pot", "soil", "compost", "fence", "decking", "terrace", "planter", "trellis"],
    "DIY": ["diy", "tool", "drill", "screw", "nail", "hammer", "wrench", "pliers", "tape measure", "level", "saw", "clamp", "socket", "hex", "torx", "breaker", "spanner", "ratchet", "chisel", "sandpaper", "paint roller"],
    "Sports": ["sport", "fitness", "yoga", "gym", "exercise", "resistance", "mat", "dumbbell", "kettlebell", "band", "jump rope", "grip", "foam roller", "running", "cycling", "swimming", "camping", "hiking", "ball", "racket"],
    "Bathroom": ["bathroom", "shower", "toilet", "towel", "soap", "mirror", "bath", "shaver", "razor", "hook", "organiser", "dispenser", "toothbrush", "tumbler", "mat", "rail", "caddy"],
    "Cleaning": ["clean", "mop", "duster", "brush", "sponge", "vacuum", "cloth", "wipe", "stain", "lint", "scrub", "squeegee", "broom", "dustpan", "bucket"],
    "Office": ["desk", "office", "stationery", "pen", "notebook", "organiser", "laptop", "mouse", "keyboard", "monitor", "stand", "file", "folder", "stapler", "clip", "marker", "highlighter", "diary", "planner"],
    "Lighting": ["led", "light", "lamp", "night light", "strip", "fairy", "solar light", "bulb", "lantern", "chandelier", "spotlight", "dimmer"],
    "Storage": ["storage", "organiser", "box", "basket", "shelf", "drawer", "container", "bag", "pouch", "rack", "crate", "bin", "caddy"],
    "Crafts": ["craft", "art", "paint", "brush", "sticker", "tape", "sewing", "knit", "crochet", "needle", "thread", "fabric", "scissors", "bead", "ribbon", "washi", "vinyl", "resin", "mould"],
    "Bedding": ["bedding", "pillow", "blanket", "sheet", "duvet", "cushion", "throw", "mattress", "sleep", "quilt", "comforter"],
    "Pets": ["pet", "dog", "cat", "collar", "leash", "bed", "grooming", "litter", "feeder", "aquarium", "fish", "hamster", "rabbit", "puppy", "kitten", "paw", "chew", "scratch"],
    "Home": ["home", "decor", "wall", "candle", "vase", "frame", "mirror", "clock", "hook", "hanger", "doormat", "curtain", "blind", "rug", "carpet"],
    "Phone": ["phone", "mobile", "iphone", "samsung galaxy", "case", "screen protector", "tempered glass", "sim card", "earphone", "earbuds", "headphone", "pop socket", "magsafe"],
    "Tech": ["laptop", "computer", "tablet", "keyboard", "mouse", "webcam", "usb", "hub", "docking", "monitor", "ethernet", "wifi", "bluetooth", "speaker", "headset", "micro sd", "memory card", "cable", "adapter"],
    "Travel": ["travel", "luggage", "suitcase", "packing", "passport", "luggage tag", "neck pillow", "eye mask", "toiletry", "travel adapter", "compression", "organiser bag"],
    "Party": ["party", "balloon", "birthday", "banner", "confetti", "bunting", "decoration", "disposable", "plates", "napkin", "cupcake", "candle"],
}


def _load_scraperapi_key():
    """Load ScraperAPI key: env var first, then ~/.hermes/scraperapi_key.txt"""
    key = os.environ.get("SCRAPER_API_KEY", "")
    if key:
        return key
    key_file = Path.home() / ".hermes" / "scraperapi_key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    return ""

SCRAPER_API_KEY = _load_scraperapi_key()

def _is_valid_response(html):
    """Check if Amazon response contains real product data."""
    if not html:
        return False
    low = html.lower()
    if "captcha" in low or "api-services-support@amazon" in low:
        return False
    if "data-asin" not in html:
        return False
    return True

CLOAKBROWSER_CHROME = '/home/lee/.cloakbrowser/chromium-146.0.7680.177.5/chrome'

# ── 12-hour cache ────────────────────────────────────────────────
CACHE_FILE = BASE / "data" / "amazon_cache.json"
CACHE_TTL = 12 * 3600  # 12 hours

def _load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}

def _save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache))

def _check_cache(url):
    cache = _load_cache()
    entry = cache.get(url)
    if entry:
        age = time.time() - entry["t"]
        if age < CACHE_TTL:
            print(f"  cache HIT ({age/3600:.0f}h old): {url.split('/')[-2]}", file=sys.stderr)
            return entry["h"]
    return None

def _set_cache(url, html):
    cache = _load_cache()
    cache[url] = {"t": time.time(), "h": html}
    _save_cache(cache)

# ── Browser：每个线程各持一个（不是全局单例）──────────────────
# Playwright 的 sync API 绑定创建它的线程/greenlet，跨线程复用必抛
# "Cannot switch to a different thread"。原来是全局单例 + 一把锁 —— 锁只挡住
# 并发，挡不住「不是同一个线程」，于是线程池里每次调用都抛错、退化成新建独立
# 实例。日志里连刷几十条 "singleton error → fallback → dedicated instance"
# 就是这么来的：32 个产品 32 次冷启动，详情页验证因此成了整条链路最慢的一步。
# thread-local 之后每个线程只启一次，池里 3 个线程总共 3 次。
# 同样的结论 keyword_scanner.py 早就得出过（见那里的 "avoids the greenlet
# thread conflict in the shared CloakBrowser"），只是没回头改这里。
_tls = threading.local()
_amazon_fetch_lock = threading.Lock()
# BrowserAct 熔断：连续 2 次失败后本批次跳过（不稳定时省预算，2026-08-03）
_browseract_circuit_open = False
_browseract_consec_fail = 0

def _get_browser():
    if getattr(_tls, 'ctx', None) is None:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        browser = p.chromium.launch(executable_path=CLOAKBROWSER_CHROME, headless=True)
        _tls.pw = p
        _tls.browser = browser
        _tls.ctx = browser.new_context(
            locale='en-GB',
            timezone_id='Europe/London',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        )
        print(f"  🚀 CloakBrowser launched (thread {threading.current_thread().name})",
              file=sys.stderr)
    return _tls.browser, _tls.ctx


def close_thread_browser():
    """关掉当前线程持有的 browser。线程退出前调用，不调用则等进程结束由 OS 收。"""
    for attr, closer in (('ctx', 'close'), ('browser', 'close'), ('pw', 'stop')):
        obj = getattr(_tls, attr, None)
        if obj is not None:
            try:
                getattr(obj, closer)()
            except Exception:
                pass
            setattr(_tls, attr, None)

def _cloakbrowser_fetch(url):
    """Fetch a page using CloakBrowser — 复用本线程的 browser。
    出错时退化成一次性独立实例。
    """
    if not os.path.exists(CLOAKBROWSER_CHROME):
        return ""

    # 这里原来套了一把全局锁。thread-local 之后每个线程有自己的 browser，
    # 再串行化只会把并发白白丢掉 —— 锁挡的是并发，而当初要挡的是跨线程，
    # 那本来就不是锁能解决的问题。
    try:
        browser, ctx = _get_browser()
        page = ctx.new_page()
        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)

            # Accept cookies if present
            try:
                accept = page.query_selector('#sp-cc-accept')
                if accept:
                    accept.click()
                    page.wait_for_timeout(500)
            except Exception:
                pass

            html = page.content()
            if len(html) > 1000:
                return html
            # Short response may be a 503 / captcha — fall through to fresh instance
        finally:
            page.close()
    except Exception as e:
        err_str = str(e)
        print(f"  CloakBrowser thread-local error: {err_str[:80]}", file=sys.stderr)
        # 本线程的 browser 可能已经坏了，丢掉，下次调用会重建
        close_thread_browser()
        if "greenlet" in err_str or "Cannot switch" in err_str or "different thread" in err_str:
            pass  # fall through
        else:
            return ""

    # Fallback: dedicated fresh browser instance (avoids greenlet thread conflict)
    print("  CloakBrowser fallback → dedicated instance", file=sys.stderr)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CLOAKBROWSER_CHROME, headless=True,
                                        args=['--disable-blink-features=AutomationControlled'])
            try:
                ctx = browser.new_context(
                    locale='en-GB', timezone_id='Europe/London',
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                )
                page = ctx.new_page()
                try:
                    page.goto(url, timeout=30000, wait_until='domcontentloaded')
                    page.wait_for_timeout(3000)
                    html = page.content()
                    return html
                finally:
                    page.close()
            finally:
                browser.close()
    except Exception as e:
        print(f"  CloakBrowser dedicated fallback error: {e}", file=sys.stderr)
        return ""


CLOUDFLARE_WORKER_URL = "https://amazon-uk-proxy.liyuhong66.workers.dev/"

def _curl_fetch(url):
    """Fetch a page with curl, forcing GBP. Falls back to curl_cffi → CloakBrowser → BrowserAct."""
    # Try direct request first (fast, but usually blocked)
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "--compressed",
             "--connect-timeout", "10", "--max-time", "30",
             "-H", f"User-Agent: {USER_AGENT}",
             "-H", "Accept-Language: en-GB,en;q=0.9",
             "-b", GBP_COOKIES,
             url],
            capture_output=True, text=True, timeout=45
        )
        if _is_valid_response(result.stdout):
            return result.stdout
    except Exception as e:
        pass

    # Try curl_cffi with TLS fingerprint impersonation
    try:
        from curl_cffi import requests as cffi_req
        cffi_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        }
        resp = cffi_req.get(url, impersonate="chrome", headers=cffi_headers, timeout=15)
        if resp.status_code == 200 and _is_valid_response(resp.text):
            print(f"  curl_cffi OK (len={len(resp.text)})", file=sys.stderr)
            return resp.text
    except ImportError:
        pass  # curl_cffi not installed
    except Exception as e:
        print(f"  curl_cffi error: {e}", file=sys.stderr)

    # Try ScraperAPI (if quota available — resets monthly on 1st)
    scraper_key = os.environ.get("SCRAPER_APIKEY", "") or os.environ.get("SCRAPER_API_KEY", "")
    if scraper_key:
        try:
            quoted = urllib.parse.quote(url)
            scraper_url = f"http://api.scraperapi.com?api_key={scraper_key}&url={quoted}&country_code=gb"
            result = subprocess.run(
                ["curl", "-s", "-L", "--max-time", "20",
                 "-H", f"User-Agent: {USER_AGENT}",
                 "-H", "Accept-Language: en-GB,en;q=0.9",
                 scraper_url],
                capture_output=True, text=True, timeout=30
            )
            if _is_valid_response(result.stdout):
                print(f"  ScraperAPI OK (len={len(result.stdout)})", file=sys.stderr)
                return result.stdout
        except Exception as e:
            print(f"  ScraperAPI error: {e}", file=sys.stderr)

    # Primary: CloakBrowser (Playwright with stealth Chrome) — reliable
    # Skip dead layers: ScraperAPI (quota exhausted), CF Worker (network unreachable), BrowserAct (broken)
    try:
        html = _cloakbrowser_fetch(url)
        if html and _is_valid_response(html):
            print(f"  CloakBrowser OK (len={len(html)})", file=sys.stderr)
            return html
    except Exception as e:
        print(f"  CloakBrowser fallback error: {e}", file=sys.stderr)

    # Last resort: search fallback via BrowserAct (slow but different fingerprint)
    try:
        from browseract_fetcher import is_available, fetch_page_html
        if is_available():
            html = fetch_page_html(url)
            if html and _is_valid_response(html):
                print(f"  BrowserAct OK (len={len(html)})", file=sys.stderr)
                return html
    except Exception as e:
        print(f"  BrowserAct fallback error: {e}", file=sys.stderr)

    return ""


def _parse_amazon_page(html, category, channel_type):
    """Parse Amazon page HTML for products."""
    products = []
    if not html or len(html) < 1000:
        return products

    import html as htmlmod

    # Split HTML by data-asin blocks for per-product extraction
    blocks = re.split(r'data-asin="([A-Z0-9]{10})"', html)

    seen_asins = set()
    for i in range(1, len(blocks) - 1, 2):
        asin = blocks[i]
        block = blocks[i + 1]

        if asin in seen_asins or not asin:
            continue
        seen_asins.add(asin)

        # Extract title from <img alt="..."> in this block
        title_match = re.search(r'<img[^>]*alt="([^"]{15,300})"', block)
        title = htmlmod.unescape(title_match.group(1)).strip() if title_match else ""
        title = re.sub(r'\s+', ' ', title).strip()

        # Extract image URL from <img src="...amazon.com/images/I/..."> in this block
        # Exclude .js files — they also contain /images/I/ in the path
        img_url = ""
        img_match = re.search(r'<img[^>]*src="(https?://[^"]*amazon\.com/images/I/[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', block, re.I)
        if not img_match:
            img_match = re.search(r'<img[^>]*src="(https?://[^"]*amazon\.com/images/I/[^"]+_AC_[^"]*)"', block)
        if img_match:
            img_url = img_match.group(1)

        # Extract price — handle multiple formats (CloakBrowser returns different HTML)
        price = 0
        # Format 1: £ symbol (old HTML)
        price_match = re.search(r'[££]([\d,.]+)', block)
        # Format 2: data-csa-c-price-to-pay attribute
        if not price_match:
            price_match = re.search(r'data-csa-c-price-to-pay="([\d.]+)"', block)
        # Format 3: a-offscreen span
        if not price_match:
            price_match = re.search(r'class="a-offscreen"[^>]*>([££][\d.]+)', block)
        # Format 4: a-price-whole + a-price-fraction
        if not price_match:
            whole = re.search(r'class="a-price-whole"[^>]*>([\d]+)', block)
            frac = re.search(r'class="a-price-fraction"[^>]*>([\d]+)', block)
            if whole and frac:
                price = float(f"{whole.group(1)}.{frac.group(1)}")
                # If the price symbol indicates non-GBP, convert roughly
                sym_match = re.search(r'class="a-price-symbol"[^>]*>(\w+)', block)
                if sym_match and sym_match.group(1) not in ('£', 'GBP'):
                    # Rough GBP conversion: 1 GBP ≈ 9 CNY ≈ 1.3 USD ≈ 1.2 EUR ≈ 0.85 CHF
                    rates = {'CNY': 9.0, 'USD': 1.3, 'EUR': 1.2, 'CHF': 0.85}
                    rate = rates.get(sym_match.group(1), 9.0)
                    price = round(price / rate, 2)
        if price_match:
            price_str = price_match.group(1).replace('£', '').replace(',', '').strip()
            try:
                price = float(price_str)
            except ValueError:
                price = 0

        # Extract review count in this block
        review_match = re.search(r'>(\d[\d,]*)</span>\s*</a>', block)
        if not review_match:
            review_match = re.search(r'(\d[\d,]+)\s*(?:ratings?|reviews?)', block, re.I)
        review_count = int(review_match.group(1).replace(",", "")) if review_match else 0

        # Extract rating in this block
        rating_match = re.search(r'(\d+\.?\d?)\s*out of\s*5', block)
        rating = float(rating_match.group(1)) if rating_match else 0

        if title and price > 0:
            # Validate category: skip products whose name doesn't match the page category
            title_lower = title.lower()
            validators = CATEGORY_VALIDATORS.get(category, [])
            if validators and not any(kw in title_lower for kw in validators):
                continue  # Skip cross-category contamination

            products.append({
                "asin": asin,
                "name": title[:120],
                "price": price,
                "reviews": review_count,
                "rating": rating,
                "rank": len(products) + 1,
                "category": category,
                "channel": channel_type,
                "channel_name": CHANNEL_NAMES.get(channel_type, channel_type),
                "review_info": f"{review_count} reviews, {rating}★" if rating else f"{review_count} reviews",
                "amazon_url": f"https://www.amazon.co.uk/dp/{asin}",
                "image_url": img_url,
            })

    return products


def fetch(max_per_channel_type=5):
    """Fetch Amazon UK data from New Releases and BSR."""
    all_products = []
    seen_asins = set()

    # Category rotation per channel type
    rotation_file = BASE / "data" / "last_categories_v2.json"
    last_cats = {}
    if rotation_file.exists():
        try:
            last_cats = json.loads(rotation_file.read_text())
        except Exception:
            pass

    # Group URLs by channel type
    by_channel = {}
    for key, url in AMAZON_URLS.items():
        cat, ch = key.split("|")
        by_channel.setdefault(ch, []).append((cat, url))

    selected_keys = []
    for channel_type, entries in by_channel.items():
        last = last_cats.get(channel_type, [])
        uncovered = [e for e in entries if e[0] not in last]
        if len(uncovered) >= max_per_channel_type:
            picked = random.sample(uncovered, max_per_channel_type)
        else:
            picked = uncovered[:]
            remaining = [e for e in entries if e[0] not in [p[0] for p in picked]]
            picked.extend(random.sample(remaining, min(max_per_channel_type - len(picked), len(remaining))))

        for cat, url in picked:
            selected_keys.append((cat, channel_type, url))
        last_cats[channel_type] = [p[0] for p in picked]

    # Save rotation
    rotation_file.parent.mkdir(parents=True, exist_ok=True)
    rotation_file.write_text(json.dumps(last_cats))

    # Search fallback for categories that return empty (CAPTCHA workaround)
    SEARCH_FALLBACKS = {
        'Garden': 'garden tools accessories',
        'Office': 'office supplies stationery',
        'Home': 'home accessories gadgets',
        'Crafts': 'crafts supplies tools',
        'Phone': 'phone accessories',
        'Travel': 'travel accessories',
        'Bathroom': 'bathroom accessories',
        'Cleaning': 'cleaning supplies tools',
        'Storage': 'storage organizers',
        'Tech': 'tech accessories gadgets',
        'Bedding': 'bedding pillows duvet',
        'Party': 'party supplies decorations',
    }

    # Fetch URLs with rate limiting — serialized via lock + cache
    def _fetch_one(item):
        global _browseract_circuit_open, _browseract_consec_fail
        category, channel_type, url = item

        # Serialize: only one Amazon request at a time (true sequential delay)
        with _amazon_fetch_lock:
            # Check 12h cache first
            cached = _check_cache(url)
            if cached is not None:
                products = _parse_amazon_page(cached, category, channel_type)
                new_count = len(products)
                print(f"  cached {category}/{channel_type}: {new_count} products", file=sys.stderr)
                return (category, channel_type, products)

            # Random delay 2-5 seconds between each real request
            time.sleep(random.uniform(2, 5))

            html = _curl_fetch(url)
            if not html:
                print(f"  warn {category}/{channel_type}: empty", file=sys.stderr)
                # Try search fallback with delay
                search_query = SEARCH_FALLBACKS.get(category)
                if search_query and not _browseract_circuit_open:
                    time.sleep(3)  # Extra delay before BrowserAct
                    from browseract_fetcher import search_amazon
                    search_products = search_amazon(search_query, max_products=max_per_channel_type, category=category)
                    if search_products:
                        _browseract_consec_fail = 0
                        for p in search_products:
                            p['channel'] = channel_type
                            p['channel_name'] = CHANNEL_NAMES.get(channel_type, channel_type)
                        print(f"  ok {category}/{channel_type}: {len(search_products)} from search fallback", file=sys.stderr)
                        return (category, channel_type, search_products)
                    else:
                        # BrowserAct 失败——计数熔断，连续 2 次失败后本批次不再调用
                        _browseract_consec_fail += 1
                        if _browseract_consec_fail >= 2:
                            _browseract_circuit_open = True
                            print("  🔌 BrowserAct 连续失败，熔断本批次", file=sys.stderr)
                return (category, channel_type, [])

            # Save successful fetch to cache
            _set_cache(url, html)
            products = _parse_amazon_page(html, category, channel_type)
            new_count = len(products)
            print(f"  ok {category}/{channel_type}: {new_count} new", file=sys.stderr)
            return (category, channel_type, products)

    # Sequential fetch (no threading — Playwright greenlets are not thread-safe)
    def _fetch_seq(items):
        results = []
        for item in items:
            category, channel_type, products = _fetch_one(item)
            for p in products:
                if p["asin"] not in seen_asins:
                    seen_asins.add(p["asin"])
                    all_products.append(p)
            results.append((category, channel_type, products))
        return results

    _fetch_seq(selected_keys)

    # Summary by channel
    for ch in CHANNEL_NAMES:
        count = sum(1 for p in all_products if p["channel"] == ch)
        print(f"  {CHANNEL_NAMES[ch]}: {count} products", file=sys.stderr)

    print(f"  Amazon UK total: {len(all_products)} products", file=sys.stderr)
    return all_products
