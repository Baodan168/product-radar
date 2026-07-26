"""模板加载 + 分语境转义。

audit-report P0/P3 的根因是「不同输出语境混在超大字符串模板里」：
generate_platform.py 的 esc() 只做 HTML 文本转义，却被同时用在
HTML 文本、属性、onclick 内联事件、href/src 和 JS 模板字符串里。
这五种语境的转义规则并不一样，混用就是注入。

所以这里按语境拆开，函数名直接写明用在哪：
    h()        HTML 文本节点
    attr()     HTML 属性值（总是带引号输出）
    js()       嵌入 <script> 的 JSON 字面量
    url()      href / src（走 oa.urls 白名单）

模板用 str.Template 的 ${name} 占位，不用 f-string —— f-string 会把
模板里的 CSS/JS 花括号也当成占位符，原来的生成器为此把每个 { 都写成
{{，可读性极差且极易出错。
"""
import html as _html
import json
from pathlib import Path
from string import Template

from . import urls as _urls
from .config import TEMPLATE_DIR, ASSET_DIR


def h(value) -> str:
    """HTML 文本节点转义。"""
    if value is None:
        return ''
    return _html.escape(str(value), quote=False)


def attr(value) -> str:
    """HTML 属性值转义（含引号）。输出时务必用引号包住。"""
    if value is None:
        return ''
    return _html.escape(str(value), quote=True)


def js(value) -> str:
    """把 Python 对象序列化成可安全嵌入 <script> 的 JSON。

    ensure_ascii=True 让非 ASCII 转成 \\uXXXX，顺带绕开页面编码问题。
    </script> 和 HTML 注释起止符必须转义 —— 否则数据里一个字符串就能
    提前闭合 script 标签，这是最经典的一种注入。
    """
    text = json.dumps(value, ensure_ascii=True)
    return (text.replace('<', '\\u003c')
                .replace('>', '\\u003e')
                .replace('&', '\\u0026')
                .replace(' ', '\\u2028')
                .replace(' ', '\\u2029'))


def url(value, fallback: str = '') -> str:
    """href / src 用：先过白名单，再做属性转义。"""
    return attr(_urls.safe_url(value, fallback))


def load_template(name: str) -> Template:
    path = TEMPLATE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f'模板不存在: {path}')
    return Template(path.read_text(encoding='utf-8'))


def load_asset(name: str) -> str:
    path = ASSET_DIR / name
    if not path.exists():
        raise FileNotFoundError(f'资源不存在: {path}')
    return path.read_text(encoding='utf-8')


def render(template_name: str, **context) -> str:
    """渲染模板。

    用 substitute 而不是 safe_substitute —— 占位符拼错时直接抛
    KeyError，而不是把 ${typo} 原样写进产物让人在页面上发现。
    """
    return load_template(template_name).substitute(**context)
