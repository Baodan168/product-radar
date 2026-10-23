#!/usr/bin/env python3
"""Patch UK festival_engine.py to add season panel functionality."""

content = open('/home/lee/product-radar/festival_engine.py').read()

# 1. Fix generate_season_panel - rewrite the whole function cleanly
import re

# Remove any existing broken version
pattern = r'def generate_season_panel\(festivals\):.*?(?=\n\ndef |\nclass |$)'
content = re.sub(pattern, '', content, flags=re.DOTALL)

# Add clean function after _current_season_key
old_marker = 'def _current_season_key() -> str:\n    return _season_of(datetime.now().month)'

new_func_lines = [
    '',
    '',
    'def generate_season_panel(festivals):',
    '    """Generate season panel with buttons and recommendation cards."""',
    '    from season_engine import MONTHLY_SEASONAL_KEYWORDS, get_seasonal_sourcing_alert, SEASON_REGION_TAGS',
    '',
    '    event_month = {}',
    '    for f in festivals:',
    '        try:',
    '            event_month[f.get(\'id\', \'\')] = int(f[\'date\'][5:7])',
    '        except (ValueError, TypeError, IndexError):',
    '            continue',
    '    season_data = {}',
    '    for key, info in SEASONS.items():',
    '        kws, seen = [], set()',
    '        for m in info["months"]:',
    '            for kw in MONTHLY_SEASONAL_KEYWORDS.get(m, []):',
    '                k = kw.lower().strip()',
    '                if k not in seen:',
    '                    seen.add(k)',
    '                    kws.append(kw)',
    '        cnt = sum(1 for mid, m in event_month.items() if m in info["months"])',
    '        season_data[key] = {"kws": kws, "events": cnt}',
    '',
    '    cur = _current_season_key()',
    '    alert = get_seasonal_sourcing_alert()',
    '    urgency_icon = {"OK": "\\u2705", "PLAN": "\\ud83d\\udccb", "AIR_ONLY": "\\ud83d\\udfe1", "URGENT": "\\u26a0\\ufe0f", "OVERDUE": "\\ud83d\\udd34"}.get(alert["urgency"], "")',
    '    next_season_label = SEASONS.get(alert["next_season"], {}).get("label", alert["next_season"])',
    '    next_season_icon = SEASONS.get(alert["next_season"], {}).get("icon", "")',
    '    deadline_text = ""',
    '    if alert["days_to_deadline"] < 0:',
    '        deadline_text = f\'{next_season_icon} {next_season_label}\\u7a7a\\u8fd0\\u622a\\u6b62\\u5df2\\u8fc7\\uff08{alert["air_deadline"]}\\uff09\\uff0c\\u4ec5\\u9650\\u73b0\\u8d27/\\u5feb\\u94c1\'',
    '    else:',
    '        deadline_text = f\'{next_season_icon} {next_season_label}\\u7a7a\\u8fd0\\u622a\\u6b62: {alert["air_deadline"]}\\uff08\\u8fd8\\u5269 {alert["days_to_deadline"]} \\u5929\\uff09{urgency_icon}\'',
    '',
    '    btns = []',
    '    for key, info in SEASONS.items():',
    '        active = \' season-btn-active\' if key == cur else \'\'',
    '        btns.append(',
    '            f\'<button class="season-btn{active}" data-season="{key}" \',
    '            f\'onclick="setSeason(this, \\'{key}\\')">\'>\',
    '            f\'{info["icon"]} {info["label"]}({info["months"][0]}-{info["months"][-1]}\\u6708)</button>\'',
    '        )',
    '    season_nav = f\'<div class="season-nav">{" ".join(btns)}</div>\'',
    '',
    '    panels = []',
    '    panel_js = []',
    '    for key, info in SEASONS.items():',
    '        d = season_data[key]',
    '        kws_html = "".join(f\'<span class="season-kw">{htmlmod.escape(k)}</span>\' for k in d["kws"])',
    '        cur_mark = \' <span class="season-cur-tag">\\u5f53\\u524d</span>\' if key == cur else \'\'',
    '        region = SEASON_REGION_TAGS.get(key, {})',
    '        region_n = region.get("north", "")',
    '        region_s = region.get("south", "")',
    '        display_style = "block" if key == cur else "none"',
    '        deadline_div = ""',
    '        if key == cur:',
    '            deadline_div = f\'<div class="season-deadline-bar">{deadline_text}</div>\'',
    '        region_div = f\'<div class="season-region-tags"><span class="region-tag">\\ud83c\\uddec\\ud83c\\udde7 UK\\u5168\\u5883: {region_n}</span></div>\'',
    '        panels.append(f\'\'\'      <div class="season-panel" id="seasonPanel-{key}" data-season="{key}" style="display:{display_style}">',
    '        <div class="season-panel-head">',
    '          <span class="season-panel-title">{info["icon"]} {info["label"]}\\u9009\\u54c1\\u63a8\\u8350\\uff08{info["months"][0]}-{info["months"][-1]}\\u6708\\uff09{cur_mark}</span>',
    '          <span class="season-panel-meta">\\u8986\\u76d6 {d["events"]} \\u4e2a\\u8282\\u65e5\\u4e8b\\u4ef6 \\u00b7 {len(d["kws"])} \\u4e2a\\u63a8\\u8350\\u65b9\\u5411</span>',
    '        </div>',
    '        <div class="season-panel-note">\\ud83d\\udd0e \\u4ee5\\u4e0b\\u5173\\u952e\\u8bcd\\u5df2\\u81ea\\u52a8\\u6ce8\\u5165\\u6bcf\\u65e5\\u96f7\\u8fbe\\u626b\\u63cf\\uff08\\u4e0e\\u5b63\\u8282\\u540c\\u6b65\\u8f6e\\u6362\\uff09\\uff0c\\u70b9\\u51fb\\u6708\\u4efd\\u6309\\u94ae\\u67e5\\u770b\\u8be5\\u5b63\\u8282\\u8282\\u65e5</div>',
    '        {deadline_div}',
    '        {region_div}',
    '        <div class="season-kw-list">{kws_html}</div>',
    '      </div>\'\'\')',
    '        panel_js.append(',
    '            f\'seasonPanelData["{key}"]={json.dumps(d["kws"], ensure_ascii=False)};\',',
    '        )',
    '',
    '    panel_html = (\'<div id="seasonPanelWrap">\' + "".join(panels) + \'</div>\')',
    '    panel_data_js = ("const seasonPanelData={};\\\\n" + "\\\\n".join(panel_js)',
    '                     + f\'\\\\nconst currentSeasonKey="{cur}";\')',
    '',
    '    return season_nav + panel_html, panel_data_js',
]

new_func = '\n'.join(new_func_lines)
content = content.replace(old_marker, old_marker + new_func)

# 2. Add JS for setSeason and season panel data injection
old_script_close = '''    // 初始加载即收起已过节日（filterHidePast 默认勾选）
    filterFestivals();
    </script>'''

new_script_close = '''    // 2026-08-28 季节按钮交互
    ''' + 'PLACEHOLDER_JS' + '''
    function setSeason(btn, key) {
      document.querySelectorAll('.season-btn').forEach(b => b.classList.remove('season-btn-active'));
      btn.classList.add('season-btn-active');
      document.querySelectorAll('.season-panel').forEach(p => {
        p.style.display = (p.dataset.season === key) ? 'block' : 'none';
      });
      const monthMap = {spring:[3,4,5], summer:[6,7,8], autumn:[9,10,11], winter:[12,1,2]};
      window._seasonMonths = monthMap[key] || [];
      document.getElementById('filterMonth').value = '';
      filterFestivals();
    }

    // 初始加载即收起已过节日（filterHidePast 默认勾选）
    filterFestivals();
    </script>'''

content = content.replace('PLACEHOLDER_JS', season_panel_js)
content = content.replace(new_script_close.replace('PLACEHOLDER_JS', ''), old_script_close)

# Actually let me do this more carefully
content = open('/home/lee/product-radar/festival_engine.py').read()

# Find and replace the script closing section
old_end = '''    // 初始加载即收起已过节日（filterHidePast 默认勾选）
    filterFestivals();
    </script>
    \'\'\''''

new_end = '''    // 2026-08-28 季节按钮交互
    ''' + 'SEASON_JS_PLACEHOLDER' + '''
    function setSeason(btn, key) {
      document.querySelectorAll('.season-btn').forEach(b => b.classList.remove('season-btn-active'));
      btn.classList.add('season-btn-active');
      document.querySelectorAll('.season-panel').forEach(p => {
        p.style.display = (p.dataset.season === key) ? 'block' : 'none';
      });
      const monthMap = {spring:[3,4,5], summer:[6,7,8], autumn:[9,10,11], winter:[12,1,2]};
      window._seasonMonths = monthMap[key] || [];
      document.getElementById('filterMonth').value = '';
      filterFestivals();
    }

    // 初始加载即收起已过节日（filterHidePast 默认勾选）
    filterFestivals();
    </script>
    \'\'\''''

# This is getting complex with string escaping. Let me use a different approach - write to temp file first
print("Writing patch script...")
