#!/usr/bin/env python3
"""设计系统的回归测试 — 跑 `python3 -m pytest tests/ -q`。

盯的是「组件层全部走 var(--oa-*)、令牌层是唯一事实源」这个前提。
它成立时换肤只需改 :root 的令牌值，全站生效；一旦有人往组件里写死
颜色或改用裸变量别名，这个前提就破了 —— 而破了在当前配色下完全看
不出来，要等下次换肤才暴露。下一轮 UI 升级正是靠这个前提吃饭的。
"""
import re
from pathlib import Path

import pytest

CSS_PATH = Path(__file__).resolve().parent.parent / 'shared' / 'oa-theme.css'


@pytest.fixture(scope='module')
def css():
    return CSS_PATH.read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def css_nocomments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


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
