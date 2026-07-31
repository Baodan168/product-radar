"""不让空数据覆盖好数据。

真实事故：festival_engine.load_festivals() 的数据源是一台机器上的绝对
路径，那台机器上目录一改名它就静默返回 []，generate_platform.py 照样
把 `window.FESTIVALS = [];` 写进 output/data/festivals.js，一份 133KB
的好数据就没了 —— 而且页面还「正常」生成，只是节日 Tab 空了，
不看那个 Tab 根本发现不了。

所以凡是「重新生成整份数据文件」的写入，都过这里：
新内容明显比旧的空，就拒绝写，保留旧的并报警。
宁可让页面显示上一次的数据，也不要显示空的。
"""
import json
from pathlib import Path


def _payload_len(text: str):
    """估算 JS 数据文件里承载了多少条记录。

    格式是 `window.X = <JSON>;`，切出 JSON 再数长度。
    解析不了就返回 None（当作「不知道」，不参与比较）。
    """
    try:
        body = text.split('=', 1)[1].strip().rstrip(';')
        data = json.loads(body)
    except (IndexError, json.JSONDecodeError):
        return None
    if isinstance(data, (list, dict)):
        return len(data)
    return None


def write_data_js(path: Path, var_name: str, payload, min_ratio: float = 0.5):
    """写 `window.<var_name> = <json>;`，但拒绝明显的数据塌缩。

    min_ratio: 新数据条数低于旧数据的这个比例就拒绝写。
    默认 0.5 —— 正常增删不会一次砍掉一半，砍掉一半基本就是数据源挂了。

    返回 (是否写入, 说明)。
    """
    path = Path(path)
    text = f'window.{var_name} = {json.dumps(payload, ensure_ascii=False)};'
    new_len = len(payload) if isinstance(payload, (list, dict)) else None

    if path.exists() and new_len is not None:
        try:
            old_len = _payload_len(path.read_text(encoding='utf-8'))
        except OSError:
            old_len = None

        if old_len:
            if new_len == 0:
                msg = (f'拒绝写入 {path.name}：新数据为空，旧数据有 {old_len} 条。'
                       f'数据源可能挂了，保留旧文件。')
                print(f'  ⚠️ {msg}')
                return False, msg
            if new_len < old_len * min_ratio:
                msg = (f'拒绝写入 {path.name}：新数据 {new_len} 条，'
                       f'不足旧数据 {old_len} 条的 {min_ratio:.0%}。保留旧文件。')
                print(f'  ⚠️ {msg}')
                return False, msg

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return True, f'{path.name} 已写入（{new_len} 条）' if new_len is not None else f'{path.name} 已写入'
