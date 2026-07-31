#!/usr/bin/env python3
"""设计系统的回归测试 — 跑 `python3 -m pytest tests/ -q`。

盯的是「组件层全部走 var(--oa-*)、令牌层是唯一事实源」这个前提。
它成立时换肤只需改 :root 的令牌值，全站生效；一旦有人往组件里写死
颜色或改用裸变量别名，这个前提就破了 —— 而破了在当前配色下完全看
不出来，要等下次换肤才暴露。

v5 换肤时这个前提被证伪了一次：老测试只拦「裸变量别名」，拦不住
「字面 hex」，于是 :root 之外攒了 76 处写死的颜色（59 处在选品平台
私有层），换令牌值时它们纹丝不动 —— 粉色评分圆环配青色主调那种。
所以补了 test_no_literal_colors_outside_token_layer。
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# 不纳入颜色检查的生成器。
# generate_analysis.py：全仓库没有任何地方引用它（cron_scan.sh / workflow / import 都没有），
# 补货页现在由仓库外的 ~/product-analysis/generate_html.py 产。里面 38 处 hex 是死代码，
# 不值得改，但也别让它把门禁一直卡红。要么确认后删掉，要么删掉这行。
SKIP_GENERATORS = {'generate_analysis.py'}
CSS_PATH = ROOT / 'shared' / 'oa-theme.css'

# 令牌层的结束位置：这一行之后就不许再出现字面颜色
TOKEN_LAYER_END = '/* ══════ Typography ══════ */'


@pytest.fixture(scope='module')
def css():
    return CSS_PATH.read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def css_nocomments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


@pytest.fixture(scope='module')
def below_tokens(css):
    """令牌层之后的全部 CSS，注释已剔除。"""
    i = css.find(TOKEN_LAYER_END)
    assert i != -1, f'找不到令牌层结束标记：{TOKEN_LAYER_END}'
    return re.sub(r'/\*.*?\*/', '', css[i:], flags=re.S)


def test_braces_balanced(css_nocomments):
    opens = css_nocomments.count('{')
    closes = css_nocomments.count('}')
    assert opens == closes, f'花括号不平衡：{opens} 个 {{ vs {closes} 个 }}'


def test_no_undefined_tokens(css_nocomments):
    defined = set(re.findall(r'(--oa-[\w-]+)\s*:', css_nocomments))
    used = set(re.findall(r'var\(\s*(--oa-[\w-]+)', css_nocomments))
    missing = sorted(used - defined)
    assert not missing, f'引用了未定义的令牌：{missing}'


def test_no_dark_mode_remnants(css):
    """暗色模式已移除（D11），不该有任何残留。

    留着会造成两种混乱：改令牌时不知道要不要同步维护暗色块，
    以及系统偏好暗色的用户看到半套主题。
    """
    for banned in ('data-oa-theme', 'prefers-color-scheme',
                   'color-scheme: dark', 'oa-theme-toggle'):
        assert banned not in css, f'oa-theme.css 里仍有暗色残留：{banned}'


def test_legacy_shim_holds_only_variable_aliases(css):
    """遗留 shim 区只放裸变量别名，不放组件样式。

    那些别名（--blue / --muted / --r）只为存量页面兜底。
    往里加组件样式等于开了第二个组件层，换肤时会漏掉。
    """
    idx = css.find('遗留 shim（已废弃，勿在新代码使用）')
    assert idx != -1, '找不到遗留 shim 区块'
    shim = css[idx:]
    selectors = re.findall(r'^([.:\w\[][^{@\n]*?)\s*\{', shim, re.M)
    non_root = [x.strip() for x in selectors if x.strip() != ':root']
    assert not non_root, f'shim 区混进了组件样式：{non_root}'


def test_no_bare_color_aliases_in_component_layer(css):
    """组件层不许再用裸变量别名（--blue / --muted 这类）。

    它们只为存量页面兜底。新组件用了就绕开了 --oa-* 令牌体系，
    下一轮换肤时改令牌不会影响到它们，属于埋雷。
    """
    idx = css.find('v4.0 — 门户壳与今日概览组件')
    assert idx != -1, '找不到 v4.0 组件区块'
    v4 = css[idx:css.find('遗留 shim（已废弃', idx)]
    bare = re.findall(r'var\(\s*(--(?!oa-)[\w-]+)', v4)
    assert not bare, f'v4 组件层用了裸变量别名：{sorted(set(bare))}'


def test_no_dark_mode_anywhere_in_source():
    """全仓库源码与模板里都不该再有暗色痕迹。

    删暗色涉及 CSS / 两个 JS / 两个模板 / 截图工具 / 测试七处，
    漏一处就会留下点不动的按钮或永远不生效的分支。
    """
    root = CSS_PATH.parent.parent
    targets = (list(root.glob('shared/*.css')) + list(root.glob('assets/*.js'))
               + list(root.glob('templates/*.html')) + list(root.glob('tools/*.py'))
               + list(root.glob('oa/*.py')) + list(root.glob('*.py')))
    banned = ('data-oa-theme', 'prefers-color-scheme', 'oa-set-theme',
              'themeToggle', 'oa-theme-toggle')
    hits = []
    for f in targets:
        text = f.read_text(encoding='utf-8')
        for kw in banned:
            if kw in text:
                hits.append(f'{f.relative_to(root)}: {kw}')
    assert not hits, f'暗色残留：{hits}'


def test_no_literal_colors_outside_token_layer(below_tokens):
    """令牌层之外不许写字面颜色（#hex / rgb() / hsl()）。

    这条是 v5 换肤时补的。老测试只看「有没有用裸变量别名」，
    而真正让换肤失效的是写死的 hex —— 改 :root 对它们毫无作用。
    当时 :root 之外有 76 处，改完令牌后页面一半新一半旧。

    需要透明度就在 :root 里定义一个带 alpha 的令牌（如 --oa-scrim），
    不要在组件里现调 rgba。
    """
    bad = re.findall(r'#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)', below_tokens)
    assert not bad, (
        f'令牌层之外出现 {len(bad)} 处字面颜色：{sorted(set(bad))[:12]}\n'
        f'改 :root 不会影响它们，下次换肤就会露馅。请收进 --oa-* 令牌。'
    )


MIN_FONT_PX = 12.0


def test_no_tiny_font_sizes_outside_token_layer(below_tokens):
    """令牌层之外不许出现小于 12px 的字面字号。

    颜色有 test_no_literal_colors_outside_token_layer 守着，字号一直没有 ——
    「改令牌就能换肤」这个前提对字号其实是不成立的。实际后果：组件层散着
    9.5 / 10 / 11 / 11.5px 共 33 处，调 --oa-text-* 完全带不动它们。

    这个团队全天盯屏幕，12px 是下限。要更小的字先问「这条信息是不是根本
    不该出现在首屏」，而不是把它缩到看不见。
    """
    bad = [m for m in re.findall(r'font-size:\s*([0-9.]+)px', below_tokens)
           if float(m) < MIN_FONT_PX]
    assert not bad, (
        f'令牌层之外出现 {len(bad)} 处小于 {MIN_FONT_PX:g}px 的字号：'
        f'{sorted(set(bad), key=float)}\n'
        f'请改用 var(--oa-text-xs) 及以上，改 :root 不会影响写死的 px。'
    )


def test_type_scale_floor_holds(css):
    """字号阶自身的下限也要守住 —— 免得有人直接把 --oa-text-xs 调小。"""
    scale = dict(re.findall(r'(--oa-text-(?:xs|sm|body|h3|h2|h1|display)):\s*([0-9.]+)px', css))
    assert scale, '没解析到字号阶'
    too_small = {k: v for k, v in scale.items() if float(v) < MIN_FONT_PX}
    assert not too_small, f'字号阶跌破 {MIN_FONT_PX:g}px 下限：{too_small}'


def test_no_corrupted_var_values(css_nocomments):
    """拦 `var(--oa-surface)7ed` 这种被批量替换弄坏的值。

    真实事故：上一轮把 `#fff` 全局换成 `var(--oa-surface)`，
    `#fff7ed` 就变成了 `var(--oa-surface)7ed` —— 不是合法颜色，
    浏览器直接丢弃该声明。节日 Tab 的五处底色因此静默消失，
    在页面上只表现为「这个标签怎么没底色」，没人会去查 CSS。
    """
    bad = re.findall(r'var\(\s*--[\w-]+\s*\)[0-9a-fA-F]+', css_nocomments)
    assert not bad, f'被替换弄坏的颜色值：{bad}'


def test_semantic_ink_variants_exist(css):
    """每个语义色都要有 -ink（文字）和 -soft（底色）两档。

    -soft 底上放同名的实色文字对比度不够（比如 --oa-orange 落在
    --oa-orange-soft 上只有 2:1）。组件层一律用 -ink 配 -soft，
    这条保证那对令牌不会被谁顺手删掉。
    """
    for name in ('red', 'orange', 'green', 'blue', 'purple'):
        for suffix in ('ink', 'soft'):
            token = f'--oa-{name}-{suffix}:'
            assert token in css, f'缺少语义令牌 {token}'


def test_no_inline_color_in_templates_and_assets():
    """模板和前端脚本里不许再出现颜色。

    v5 之前：templates/platform.html 用 `style="--tc:var(--purple)"` 给
    四个 Tab 各配一种颜色，assets/platform.js 用 `style.background=` 在
    切 Tab 时覆盖 CSS，generate_platform.py 的 STATUS_CONFIG 直接存 hex。
    三处加起来的效果是：改令牌改不动 Tab 和状态按钮的颜色。
    颜色只能住在 shared/oa-theme.css。

    v6 补充：原先这里是手写的四个文件名，`festival_engine.py` 就从缝里漏了过去
    （34 个节日各一个 themeColor 的内联 style + 品类色 hex 拼 "15" 当透明度）。
    改成「凡是产出 HTML 的 .py 都算」，以后新加生成器自动被覆盖。
    """
    # 拼 HTML 的 Python 文件用 `class="` 认，不再手写名单
    generators = [f for f in sorted(list(ROOT.glob('*.py')) + list(ROOT.glob('oa/*.py')))
                  if f.name not in SKIP_GENERATORS
                  and 'class="' in f.read_text(encoding='utf-8')]
    targets = (list(ROOT.glob('templates/*.html'))
               + list(ROOT.glob('assets/*.js'))
               + generators)
    hits = []
    for f in targets:
        if not f.exists():
            continue
        for line in f.read_text(encoding='utf-8').splitlines():
            if 'data:image/svg' in line:   # favicon 内联 SVG，不是样式
                continue
            if re.search(r'#[0-9a-fA-F]{3,8}\b', line) or re.search(r'\brgba?\([^)]*\)', line):
                hits.append(f'{f.relative_to(ROOT)}: {line.strip()[:70]}')
    assert not hits, '模板/脚本里仍有颜色：\n' + '\n'.join(hits)
