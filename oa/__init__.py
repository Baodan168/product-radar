"""OA 门户生成器内核。

拆分动机见 DESIGN-DECISIONS.md：原本 generate_portal.py 和
generate_platform.py 各自把数据加载、HTML/CSS/JS 拼接混在一个大 f-string 里，
不同输出语境（HTML 文本 / 属性 / JS 字符串 / URL）的转义规则混用，
是 audit-report P0/P3 的根因。

这里按语境分工：
    config      门户导航与站点常量（单一事实源）
    urls        URL 协议+主机白名单
    render      模板加载 + 分语境转义
    health      板块新鲜度与探针清单
    restock     补货告警摘要（容错解析仓库外产物）
    dashboard   今日概览数据装配
    platform/   选品平台的数据加载与视图模型
"""
