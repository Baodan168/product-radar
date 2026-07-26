"""今日概览 —— 门户首页的数据装配与渲染。

Phase 2 只放骨架，四张卡的真实数据在 Phase 3 接入。
"""
from . import render


def build_dashboard_html() -> str:
    """渲染今日概览主体。"""
    return (
        '<div class="oa-dash-head">'
        '<div class="oa-dash-eyebrow">TODAY</div>'
        '<div class="oa-dash-title">今日概览</div>'
        '<div class="oa-dash-sub">现在该选什么、补什么、关注什么</div>'
        '</div>'
        '<div class="oa-dash-grid" id="dashGrid"></div>'
    )
