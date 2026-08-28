#!/usr/bin/env python3
"""
Season Engine — UK seasonal event prediction for product sourcing.

Built-in calendar of UK consumer events (Jan-Dec) with:
- Event dates and recommended product categories
- Sourcing deadlines (air freight: -45 days, sea freight: -75 days)
- Seasonal search keyword generation

Usage:
    python3 season_engine.py                  # upcoming events (90 days)
    python3 season_engine.py --days 120       # next 120 days
    python3 season_engine.py --keywords       # current seasonal keywords
    python3 season_engine.py --json           # JSON output
"""
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent
CONFIG = json.loads((BASE / "config.json").read_text())

# ── UK Seasonal Events Calendar

# 2026-08-28 模块常量：月度季节关键词（从函数中提取，供 festival_engine 复用）
# 基于 Amazon UK bestseller + Argos Outdoor Living Report 2026 + John Lewis 趋势
MONTHLY_SEASONAL_KEYWORDS = {
    1: [  # 深冬 + 节后清理 + 新年计划
        "storage organiser", "desk accessories", "meal prep containers",
        "cleaning tools", "kitchen gadgets new year", "thermal gloves",
        "heated blanket", "door draft stopper", "winter warmers"],
    2: [  # 初春准备 + 情人节
        "valentine gift ideas", "romantic gift", "travel accessories",
        "decorative items", "gift packaging", "garden storage",
        "outdoor furniture covers", "window boxes"],
    3: [  # 春季 + 母亲节 + BST开始
        "spring cleaning tools", "garden tools", "kitchen gadgets",
        "home decor", "storage solutions", "mothers day gift",
        "plant pots", "garden gloves", "lawn care starter kit"],
    4: [  # 春季高峰 + 复活节
        "garden accessories", "easter decoration", "outdoor tools",
        "kitchen gadgets", "party supplies", "cleaning supplies",
        "bird feeder", "wildlife friendly garden", "herb growing kit"],
    5: [  # 初夏 + 母亲节周末 + Chelsea花展
        "garden tools", "BBQ accessories", "garden decor",
        "plant pots", "picnic items", "outdoor cushions",
        "garden lighting", "outdoor storage box", "patio heater cover"],
    6: [  # 夏季 + 父亲节 + 学校假期准备
        "travel accessories", "car cleaning", "outdoor gadgets",
        "water bottle", "picnic set", "camping accessories",
        "fathers day gift", "garden hose", "outdoor rug"],
    7: [  # 盛夏 + Prime Day
        "outdoor accessories", "BBQ tools", "travel gadgets",
        "car accessories", "camping gear", "beach accessories",
        "prime day deals", "portable fan", "shade sail"],
    8: [  # 夏末 + 返校季
        "travel accessories", "back to school stationery", "lunch box",
        "desk organiser", "storage", "outdoor cooling",
        "garden storage box", "outdoor cushions storage"],
    9: [  # 秋季 + 返校后 + 花园整理
        "kitchen gadgets", "autumn decor", "desk accessories",
        "storage organiser", "candles", "university essentials",
        "leaf blower accessory", "garden tool organiser"],
    10: [  # 深秋 + 万圣节 + 花园越冬准备
        "halloween decoration", "autumn garden tools", "party supplies",
        "candles", "bird feeder", "bird accessories",
        "greenhouse heater", "plant covers", "garden waste bags"],
    11: [  # 初冬 + 黑色星期五 + 圣诞准备
        "christmas decoration", "gift ideas", "tinsel garlands",
        "party supplies", "kitchen gadgets", "blanket throw",
        "black friday deals", "outdoor christmas lighting", "christmas tree accessories"],
    12: [  # 深冬 + 圣诞 + 新年派对
        "christmas gifts", "party supplies", "storage organiser",
        "kitchen gadgets", "travel accessories", "home decor",
        "heated throws", "winter garden care", "fire pit accessories"],
}

# 2026-08-28 北半球季节映射 + 47天空运倒计时
SEASONS = {
    "spring": {"label": "春季", "en": "Spring", "icon": "🌸", "months": (3, 4, 5), "color": "var(--oa-green)"},
    "summer": {"label": "夏季", "en": "Summer", "icon": "☀️", "months": (6, 7, 8), "color": "var(--oa-orange)"},
    "autumn": {"label": "秋季", "en": "Autumn", "icon": "🍂", "months": (9, 10, 11), "color": "#b45309"},
    "winter": {"label": "冬季", "en": "Winter", "icon": "❄️", "months": (12, 1, 2), "color": "var(--oa-blue)"},
}

SEASON_AIR_FREIGHT_LEAD = 47  # 空运备货提前天数

# 区域气候标签：UK全境温带海洋性气候，无南北差异
SEASON_REGION_TAGS = {
    "spring": {"months": (3, 4, 5), "north": "标准春(3-5月)", "south": "标准春(3-5月)"},
    "summer": {"months": (6, 7, 8), "north": "标准夏(6-8月)", "south": "标准夏(6-8月)"},
    "autumn": {"months": (9, 10, 11), "north": "标准秋(9-11月)", "south": "标准秋(9-11月)"},
    "winter": {"months": (12, 1, 2), "north": "标准冬(12-2月)", "south": "标准冬(12-2月)"},
}


# ── UK Seasonal Events Calendar ───────────────────────────────────
# Each event: name, month, day (approx), categories, year_override for floating dates
# Fixed dates use (month, day). Floating dates use best-guess for current year.
# For floating events, we store the typical month/week range and pick a plausible date.

UK_EVENTS = [
    # January
    {
        "event_name": "New Year / January Declutter",
        "month": 1, "day": 2,
        "recommended_categories": ["storage", "organiser", "desk accessories", "meal prep"],
        "notes": "Post-Christmas returns, gift card redemptions, resolutions",
    },
    {
        "event_name": "Veganuary / Health Kick",
        "month": 1, "day": 5,
        "recommended_categories": ["kitchen gadgets", "meal prep", "storage containers"],
        "notes": "Healthy eating drives kitchen accessory sales",
    },

    # February
    {
        "event_name": "Valentine's Day",
        "month": 2, "day": 14,
        "recommended_categories": ["gift packaging", "decorative items", "travel accessories", "candle holders"],
        "notes": "UK Valentine's £1B+ market. Avoid cosmetics/perfume (forbidden)",
    },
    {
        "event_name": "Half Term (Feb)",
        "month": 2, "day": 17,
        "recommended_categories": ["outdoor accessories", "craft supplies", "car accessories"],
        "notes": "Family travel and activity products",
    },

    # March
    {
        "event_name": "Mothering Sunday (UK)",
        "month": 3, "day": 22,  # Varies late March (2026: approx Mar 22)
        "recommended_categories": ["kitchen gadgets", "garden accessories", "home decor", "gift sets"],
        "notes": "UK Mother's Day ≠ US. Different date!",
    },
    {
        "event_name": "Spring Cleaning",
        "month": 3, "day": 15,
        "recommended_categories": ["cleaning tools", "storage", "organisers", "bathroom accessories"],
        "notes": "Spring refresh mindset drives cleaning product sales",
    },
    {
        "event_name": "British Summer Time Begins",
        "month": 3, "day": 29,  # Last Sunday of March
        "recommended_categories": ["garden tools", "garden decor", "plant pots"],
        "notes": "Clocks go forward, evenings get lighter",
    },

    # April
    {
        "event_name": "Easter Weekend",
        "month": 4, "day": 5,  # Varies (2026: approx Apr 3-6)
        "recommended_categories": ["garden tools", "outdoor accessories", "kitchen gadgets",
                                    "party supplies", "Easter decorations"],
        "notes": "4-day Bank Holiday weekend drives at-home entertaining",
    },
    {
        "event_name": "Spring Gardening Peak",
        "month": 4, "day": 15,
        "recommended_categories": ["garden tools", "plant pots", "seed kits", "garden decor", "bird feeders"],
        "notes": "Garden product demand starts ramping up",
    },

    # May
    {
        "event_name": "Early May Bank Holiday",
        "month": 5, "day": 4,
        "recommended_categories": ["garden tools", "BBQ accessories", "garden decor", "picnic items"],
        "notes": "3-day weekend, garden/BBQ season kicks off",
    },
    {
        "event_name": "Chelsea Flower Show",
        "month": 5, "day": 19,
        "recommended_categories": ["garden tools", "plant pots", "garden decor", "bird accessories"],
        "notes": "RHS Chelsea drives massive garden product interest",
    },
    {
        "event_name": "Spring Bank Holiday",
        "month": 5, "day": 25,
        "recommended_categories": ["outdoor accessories", "travel items", "car accessories", "BBQ"],
        "notes": "3-day weekend, outdoor entertaining",
    },

    # June
    {
        "event_name": "Summer Begins / School Holiday Prep",
        "month": 6, "day": 1,
        "recommended_categories": ["travel accessories", "car cleaning", "outdoor gadgets",
                                    "picnic items", "water bottles"],
        "notes": "Travel prep and outdoor activity products",
    },
    {
        "event_name": "Father's Day (UK)",
        "month": 6, "day": 21,  # Third Sunday (2026: Jun 21)
        "recommended_categories": ["car accessories", "DIY tools", "BBQ accessories", "gadget gifts"],
        "notes": "Gift-giving for dad — tools, gadgets, car accessories",
    },
    {
        "event_name": "Glastonbury / Festival Season",
        "month": 6, "day": 24,
        "recommended_categories": ["camping accessories", "outdoor gear", "festival accessories", "travel accessories"],
        "notes": "Festival season drives camping and outdoor purchases",
    },

    # July
    {
        "event_name": "Amazon Prime Day",
        "month": 7, "day": 15,  # Usually mid-July
        "recommended_categories": ["everything — best sellers", "kitchen", "home", "tech accessories"],
        "notes": "Biggest non-Q4 sales event. Stock FBA by early July!",
    },
    {
        "event_name": "Summer Holidays Start",
        "month": 7, "day": 20,
        "recommended_categories": ["outdoor toys", "travel accessories", "car accessories",
                                    "camping", "picnic", "beach"],
        "notes": "School summer holidays begin — family activity products peak",
    },

    # August
    {
        "event_name": "Peak Summer / Holiday Season",
        "month": 8, "day": 1,
        "recommended_categories": ["travel accessories", "beach items", "car accessories",
                                    "outdoor cooling", "sun protection"],
        "notes": "Peak travel and outdoor product demand",
    },
    {
        "event_name": "Summer Bank Holiday",
        "month": 8, "day": 31,  # Last Monday of August
        "recommended_categories": ["outdoor accessories", "BBQ", "garden", "party supplies"],
        "notes": "Last outdoor hurrah of the year",
    },
    {
        "event_name": "Back to School",
        "month": 8, "day": 20,
        "recommended_categories": ["stationery", "desk organisers", "lunch boxes",
                                    "storage", "pencil cases"],
        "notes": "Major UK shopping event — back to school drives stationery/storage",
    },

    # September
    {
        "event_name": "Autumn Prep",
        "month": 9, "day": 1,
        "recommended_categories": ["kitchen gadgets", "autumn decor", "storage",
                                    "desk accessories", "candles"],
        "notes": "Routine returns, autumn nesting mindset",
    },
    {
        "event_name": "University Move-In",
        "month": 9, "day": 15,
        "recommended_categories": ["storage", "kitchen gadgets", "desk accessories",
                                    "bedding", "cleaning supplies"],
        "notes": "Freshers week — students buying essentials for uni accommodation",
    },

    # October
    {
        "event_name": "Halloween",
        "month": 10, "day": 31,
        "recommended_categories": ["Halloween decorations", "party supplies",
                                    "candles", "outdoor decor"],
        "notes": "UK Halloween growing. Focus on party/decoration items (not costumes/toys)",
    },
    {
        "event_name": "Autumn Gardening",
        "month": 10, "day": 10,
        "recommended_categories": ["garden tools", "leaf clearance", "compost bins",
                                    "bird feeders", "garden decor"],
        "notes": "Autumn garden prep — leaf tools, bird feeding, winter prep",
    },

    # November
    {
        "event_name": "Bonfire Night",
        "month": 11, "day": 5,
        "recommended_categories": ["outdoor accessories", "blankets", "flasks",
                                    "party supplies", "blankets"],
        "notes": "Nov 5 — outdoor event accessories, warm items",
    },
    {
        "event_name": "Black Friday / Cyber Monday",
        "month": 11, "day": 27,  # Last Friday of Nov (2026: Nov 27)
        "recommended_categories": ["EVERYTHING — best sellers", "kitchen", "home",
                                    "storage", "gadgets", "gifts"],
        "notes": "BIGGEST sales month. FBA gets congested — ship by early October!",
    },
    {
        "event_name": "Christmas Prep Begins",
        "month": 11, "day": 1,
        "recommended_categories": ["Christmas decorations", "gift items", "party supplies",
                                    "kitchen gadgets", "candles", "tinsel garlands"],
        "notes": "Christmas shopping season starts. FBA extremely congested.",
    },

    # December
    {
        "event_name": "Christmas",
        "month": 12, "day": 25,
        "recommended_categories": ["gift items", "party supplies", "Christmas decorations",
                                    "kitchen gadgets", "travel accessories"],
        "notes": "Last order dates Dec 18-20. Stock by October!",
    },
    {
        "event_name": "Boxing Day / Post-Christmas",
        "month": 12, "day": 26,
        "recommended_categories": ["storage", "organisers", "sale items", "home refresh"],
        "notes": "Boxing Day sales + returns period",
    },
    {
        "event_name": "New Year's Eve",
        "month": 12, "day": 31,
        "recommended_categories": ["party supplies", "decorations", "kitchen gadgets"],
        "notes": "NYE entertaining",
    },
]


def _build_event_date(event, reference_year):
    """Build a datetime for the event in the reference year.
    
    For events that have passed this year, rolls to next year.
    """
    month = event["month"]
    day = event["day"]

    # Handle month overflow (e.g., month=13 for events that need next-year wrap)
    try:
        dt = datetime(reference_year, month, day)
    except ValueError:
        # Invalid day (e.g., Feb 30), fall back to last day of month
        if month == 2:
            dt = datetime(reference_year, 2, 28)
        elif month in (4, 6, 9, 11):
            dt = datetime(reference_year, month, 30)
        else:
            dt = datetime(reference_year, month, 31)

    return dt


def get_upcoming_events(days_ahead=90):
    """Get upcoming UK seasonal events within the specified window.

    Args:
        days_ahead: how many days ahead to look (default 90)

    Returns:
        list of dicts: [{
            event_name, date, days_until, recommended_categories,
            sourcing_deadline_air, sourcing_deadline_sea, notes
        }]
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff = today + timedelta(days=days_ahead)

    upcoming = []

    for event in UK_EVENTS:
        # Try current year, then next year
        for year_offset in range(2):
            event_date = _build_event_date(event, today.year + year_offset)

            if event_date < today:
                continue
            if event_date > cutoff:
                break

            days_until = (event_date - today).days

            # Sourcing deadlines (aligned with uk-festival-planner + festival_engine.py)
            # Air: production(3)+transit(13)=16d, Truck: 3+30=33d, Sea: 3+60=63d
            # Buffer: +14d (FBA receiving + safety)
            air_deadline = event_date - timedelta(days=16 + 14)
            rail_deadline = event_date - timedelta(days=33 + 14)
            sea_deadline = event_date - timedelta(days=63 + 14)

            # Status — best available option
            if air_deadline < today:
                sourcing_urgency = "OVERDUE"  # All options expired
            elif rail_deadline < today:
                sourcing_urgency = "AIR_ONLY"  # Only air freight viable
            elif sea_deadline < today:
                sourcing_urgency = "RAIL_OR_AIR"  # Sea missed, rail still OK
            elif (air_deadline - today).days <= 7:
                sourcing_urgency = "URGENT"  # Air deadline approaching
            else:
                sourcing_urgency = "OK"

            upcoming.append({
                "event_name": event["event_name"],
                "date": event_date.strftime("%Y-%m-%d"),
                "days_until": days_until,
                "recommended_categories": event["recommended_categories"],
                "sourcing_deadline_air": air_deadline.strftime("%Y-%m-%d"),
                "sourcing_deadline_rail": rail_deadline.strftime("%Y-%m-%d"),
                "sourcing_deadline_sea": sea_deadline.strftime("%Y-%m-%d"),
                "sourcing_urgency": sourcing_urgency,
                "notes": event.get("notes", ""),
            })
            break  # Don't add the same event for next year

    upcoming.sort(key=lambda x: x["days_until"])
    
    # Merge Festival Planner events (primary source, more complete)
    try:
        from festival_engine import load_festivals, get_deadlines
        festivals = load_festivals()
        existing_dates = {(e["date"], e["event_name"]) for e in upcoming}
        
        for f in festivals:
            f_date_str = f.get("date", "")
            if not f_date_str:
                continue
            f_date = datetime.strptime(f_date_str, "%Y-%m-%d")
            if f_date < today or f_date > cutoff:
                continue
            
            # Skip if already in upcoming (from UK_EVENTS)
            if (f_date_str, f.get("name", "")) in existing_dates:
                continue
            
            deadlines = get_deadlines(f)
            days_until = (f_date - today).days
            
            # Determine urgency from sea deadline
            sea_days = deadlines.get("sea", {}).get("days_from_today", 999)
            if sea_days < 0:
                sourcing_urgency = "OVERDUE"
            elif sea_days <= 7:
                sourcing_urgency = "URGENT"
            else:
                sourcing_urgency = "OK"
            
            upcoming.append({
                "event_name": f"{f.get('icon', '📅')} {f.get('name', '')}",
                "date": f_date_str,
                "days_until": days_until,
                "recommended_categories": [p.get("category", "") for p in f.get("products", [])[:3]],
                "sourcing_deadline_air": deadlines.get("air", {}).get("date", ""),
                "sourcing_deadline_rail": deadlines.get("truck", {}).get("date", ""),
                "sourcing_deadline_sea": deadlines.get("sea", {}).get("date", ""),
                "sourcing_urgency": sourcing_urgency,
                "notes": f"Importance: {f.get('importance', 'B')} | {len(f.get('products', []))} SKUs",
                "source": "festival_planner",
            })
        
        upcoming.sort(key=lambda x: x["days_until"])
    except Exception as e:
        print(f"  ⚠️ Festival Planner merge failed: {e}", file=sys.stderr)
    
    return upcoming


def get_seasonal_keywords():
    """Return search keywords relevant to the current season.

    Based on the current month and upcoming events in the next 30 days.
    Returns list of keyword strings suitable for Amazon UK / AnySearch.
    """
    today = datetime.now()
    month = today.month

    # 2026-08-28 全面升级：基于 Amazon UK bestseller + Argos Outdoor Living Report 2026 + John Lewis趋势
    # 每月从5词扩到8-10词，覆盖 UK 实销品类（暖冬/圣诞/花园越冬）
    # 气候标注：ALL=英国全国（无南北差异，全境温带海洋性气候）
    from season_engine import MONTHLY_SEASONAL_KEYWORDS as _MSK  # lazy load from module constant below
    keywords = list(_MSK.get(month, ["kitchen accessories", "home gadgets"]))

    # Add upcoming event keywords
    upcoming = get_upcoming_events(days_ahead=30)
    for event in upcoming:
        for cat in event["recommended_categories"]:
            if cat not in keywords and cat != "everything — best sellers":
                keywords.append(cat.lower())

    # Deduplicate, preserving order
    seen = set()
    unique = []
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique.append(kw)

    return unique


def _season_of(month: int) -> str:
    """月份 → 季节key（北半球）。非法月份返回空串。"""
    for key, info in SEASONS.items():
        if month in info["months"]:
            return key
    return ""


def _current_season_key() -> str:
    return _season_of(datetime.now().month)


def get_seasonal_sourcing_alert():
    """返回当前季节的备货倒计时信息。
    
    按季节首日计算：如果当前在季节内，算下一个季节的倒计时；
    如果在季节交替前47天内，当前季节品已进入"最后空运窗口"。
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month = today.month
    
    # 北半球季节映射
    _season_map = {3: "spring", 4: "spring", 5: "spring",
                   6: "summer", 7: "summer", 8: "summer",
                   9: "autumn", 10: "autumn", 11: "autumn",
                   12: "winter", 1: "winter", 2: "winter"}
    _season_months = {"spring": (3, 4, 5), "summer": (6, 7, 8),
                      "autumn": (9, 10, 11), "winter": (12, 1, 2)}
    _season_order = ["spring", "summer", "autumn", "winter"]
    
    cur_season = _season_map.get(month)
    if cur_season:
        cur_idx = _season_order.index(cur_season)
        next_season = _season_order[(cur_idx + 1) % 4]
    else:
        next_season = "spring"
    
    next_months = _season_months[next_season]
    next_month_1st = next_months[0]
    
    # 计算下一季节首日
    if next_month_1st == 3 and month >= 11:
        year = today.year + 1
    elif next_month_1st > month:
        year = today.year
    else:
        year = today.year + 1
    
    season_start = datetime(year, next_month_1st, 1)
    air_deadline = season_start - timedelta(days=SEASON_AIR_FREIGHT_LEAD)
    days_to_deadline = (air_deadline - today).days
    
    # 紧急度判断
    if days_to_deadline < 0:
        urgency = "OVERDUE"
    elif days_to_deadline <= 14:
        urgency = "URGENT"
    elif days_to_deadline <= 30:
        urgency = "AIR_ONLY"
    elif days_to_deadline <= 47:
        urgency = "PLAN"
    else:
        urgency = "OK"
    
    return {
        "current_season": cur_season,
        "next_season": next_season,
        "season_start": season_start.strftime("%Y-%m-%d"),
        "air_deadline": air_deadline.strftime("%Y-%m-%d"),
        "days_to_deadline": days_to_deadline,
        "urgency": urgency,
    }



    output_json = "--json" in sys.argv

    # Parse --days N
    days = 90
    for i, arg in enumerate(sys.argv):
        if arg == "--days" and i + 1 < len(sys.argv):
            try:
                days = int(sys.argv[i + 1])
            except ValueError:
                pass

    if "--keywords" in sys.argv:
        keywords = get_seasonal_keywords()
        if output_json:
            print(json.dumps(keywords, indent=2))
        else:
            print("=== Current Seasonal Keywords ===")
            for i, kw in enumerate(keywords, 1):
                print(f"  {i}. {kw}")
            print(f"\n  Total: {len(keywords)} keywords")
    else:
        events = get_upcoming_events(days_ahead=days)

        if output_json:
            print(json.dumps(events, indent=2, ensure_ascii=False))
        else:
            print(f"=== Upcoming UK Events (next {days} days) ===\n")
            if not events:
                print("  No events found in this window.")
            for e in events:
                urgency_icon = {
                    "OK": "✅", "URGENT": "⚠️", "AIR_ONLY": "🟡", "OVERDUE": "🔴"
                }.get(e["sourcing_urgency"], "")
                print(f"  {e['date']}  ({e['days_until']}d away)  {e['event_name']}  {urgency_icon}")
                print(f"    Categories: {', '.join(e['recommended_categories'][:4])}")
                print(f"    Sourcing: air={e['sourcing_deadline_air']} sea={e['sourcing_deadline_sea']} "
                      f"[{e['sourcing_urgency']}]")
                if e.get("notes"):
                    print(f"    Note: {e['notes']}")
                print()

            print(f"\n--- Current Seasonal Keywords ---")
            for kw in get_seasonal_keywords()[:10]:
                print(f"  • {kw}")
