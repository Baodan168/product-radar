#!/usr/bin/env python3
"""设计系统的回归测试 — 跑 `python3 -m pytest tests/ -q`。

暗色模式靠「组件全部走 var(--oa-*)，暗色只换令牌值」这个前提成立。
一旦有人往组件里写死颜色，或者两个暗色块写歪了，暗色就会局部失效，
而这种失效在浅色下完全看不出来。这几个测试就是盯这个。
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


def _dark_blocks(css):
    """取出两个暗色令牌块的正文。"""
    media = re.search(
        r'@media \(prefers-color-scheme: dark\).*?'
        r':root:not\(\[data-oa-theme="light"\]\) \{(.*?)\n  \}',
        css, re.S)
    attr = re.search(r'\n:root\[data-oa-theme="dark"\] \{(.*?)\n\}', css, re.S)
    assert media, '找不到 prefers-color-scheme 暗色块'
    assert attr, '找不到 [data-oa-theme="dark"] 暗色块'
    return media.group(1), attr.group(1)


def test_dark_blocks_define_same_tokens(css):
    """两条路径必须给出同一组令牌。

    系统偏好暗色走 @media，手动点切换按钮走属性选择器。
    只在一边加令牌的话，两条路径下页面长得不一样，
    而且只有切过主题的人才会撞见。
    """
    media_body, attr_body = _dark_blocks(css)
    media_tokens = set(re.findall(r'(--oa-[\w-]+)\s*:', media_body))
    attr_tokens = set(re.findall(r'(--oa-[\w-]+)\s*:', attr_body))
    diff = media_tokens ^ attr_tokens
    assert not diff, f'两个暗色块的令牌不一致，差异：{sorted(diff)}'


def test_dark_blocks_have_same_values(css):
    """同名令牌在两个块里的值也必须一致。"""
    media_body, attr_body = _dark_blocks(css)
    pat = r'(--oa-[\w-]+)\s*:\s*([^;]+);'
    media = {k: v.strip() for k, v in re.findall(pat, media_body)}
    attr = {k: v.strip() for k, v in re.findall(pat, attr_body)}
    mismatched = {k: (media[k], attr[k]) for k in media if k in attr and media[k] != attr[k]}
    assert not mismatched, f'同名令牌取值不一致：{mismatched}'


def test_dark_overrides_core_surface_tokens(css):
    """暗色至少要覆盖决定明暗观感的那几个令牌。"""
    _, attr_body = _dark_blocks(css)
    tokens = set(re.findall(r'(--oa-[\w-]+)\s*:', attr_body))
    required = {'--oa-bg', '--oa-surface', '--oa-text', '--oa-sub', '--oa-border'}
    assert required <= tokens, f'暗色块缺少核心令牌：{sorted(required - tokens)}'


def test_legacy_shim_uses_high_specificity(css):
    """遗留 shim 必须带 :root[data-oa-theme] 前缀。

    output/analysis/*.html 由仓库外的 product-analysis 项目生成，
    它的内联 <style> 排在 <link> 之后，同特异度下会赢。
    裸类选择器压不住它，暗色会在那几个页面上失效。
    """
    idx = css.find('遗留 shim（已废弃，勿在新代码使用）')
    assert idx != -1, '找不到遗留 shim 区块'
    shim = css[idx:]
    selectors = re.findall(r'^([.\w][^{@\n]*?)\s*\{', shim, re.M)
    bare = [s.strip() for s in selectors if 'data-oa-theme' not in s]
    assert not bare, f'shim 区里这些选择器特异度不够，压不住页面内联样式：{bare}'


def test_no_bare_color_aliases_in_component_layer(css):
    """组件层不许再用裸变量别名（--blue / --muted 这类）。

    它们只为存量页面兜底，新组件用了就会绕开 --oa-* 令牌体系，
    暗色切换时不跟随。
    """
    idx = css.find('v4.0 — 门户壳与今日概览组件')
    assert idx != -1, '找不到 v4.0 组件区块'
    v4 = css[idx:css.find('遗留 shim（已废弃', idx)]
    bare = re.findall(r'var\(\s*(--(?!oa-)[\w-]+)', v4)
    assert not bare, f'v4 组件层用了裸变量别名：{sorted(set(bare))}'
