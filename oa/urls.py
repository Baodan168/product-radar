"""URL 协议与主机白名单。

audit-report P2：image_url / amazon_url / amazon_search_url / search_1688_url
这些字段直接进 href 和 src，代码只判断字段存不存在，没限制协议和主机。
被污染的上游数据可以塞进 javascript: 和 data: URL，或者任意第三方链接。

这里在**生成期**就把非法值滤掉，页面上永远不会出现没过审的 URL。
生成期过滤比运行期过滤可靠：产物是静态 HTML，过不了这关的值根本
写不进文件。

同时修 audit P1 的 Worker 域名边界问题：endsWith('amazon.co.uk')
会放行 evilamazon.co.uk，必须按点号边界匹配。
"""
from urllib.parse import urlsplit

# 只放行 HTTPS。http/javascript/data/file 一律拒绝。
ALLOWED_SCHEME = 'https'

# 主机白名单。值为 True 表示同时放行其子域（按点号边界，不是字符串后缀）。
ALLOWED_HOSTS = {
    # Amazon UK — 产品链接与搜索
    'amazon.co.uk': True,
    'www.amazon.co.uk': False,
    # Amazon 图片 CDN
    'm.media-amazon.com': False,
    'images-na.ssl-images-amazon.com': False,
    'images-eu.ssl-images-amazon.com': False,
    'ssl-images-amazon.com': True,
    'media-amazon.com': True,
    # 1688 采购
    '1688.com': True,
    's.1688.com': False,
    # Google Trends
    'trends.google.com': False,
    'trends.google.co.uk': False,
    # 本站
    'liyuhong168.github.io': False,
}


def host_allowed(hostname: str) -> bool:
    """主机是否在白名单内。

    用点号边界而不是 endsWith —— 后者会把 evilamazon.co.uk 判成
    amazon.co.uk 的子域（audit P1）。
    """
    if not hostname:
        return False
    host = hostname.lower().rstrip('.')
    if host in ALLOWED_HOSTS:
        return True
    for allowed, with_subdomains in ALLOWED_HOSTS.items():
        if with_subdomains and host.endswith('.' + allowed):
            return True
    return False


def is_safe(url) -> bool:
    """URL 是否可以安全地放进 href / src。"""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url:
        return False
    # 控制字符能骗过一些解析器（例如 "java\tscript:"）
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in url):
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme.lower() != ALLOWED_SCHEME:
        return False
    # URL 里内嵌凭据的一律拒绝
    if parts.username or parts.password:
        return False
    # 只允许默认端口
    try:
        if parts.port not in (None, 443):
            return False
    except ValueError:
        return False
    return host_allowed(parts.hostname or '')


def safe_url(url, fallback: str = '') -> str:
    """过审就原样返回，否则返回 fallback（默认空串）。"""
    return url.strip() if is_safe(url) else fallback


def sanitize_product_urls(product: dict) -> dict:
    """就地清洗产品字典里的 URL 字段，返回同一个字典。

    没过审的字段置为空串，渲染层据此隐藏对应的链接/图片，
    而不是渲染一个指向不可信地址的元素。
    """
    for field in ('image_url', 'amazon_url', 'amazon_search_url',
                  'search_1688_url', 'url', 'link'):
        if field in product:
            product[field] = safe_url(product.get(field))
    return product
