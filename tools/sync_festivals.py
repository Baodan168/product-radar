#!/usr/bin/env python3
"""把节日数据从上游项目同步到仓库内的兜底源。

为什么需要这个脚本
------------------
`festival_engine.FESTIVAL_SOURCES` 有三级回退：

    1. ~/uk-festival-planner/index.html   上游，只在生产机上有
    2. data/festivals_data.js             仓库内兜底
    3. output/data/festivals.js           上次生成的产物

第 2 级本来是「上游不在时的替身」，但**它没有任何脚本维护** —— 是某次手工
拷过来的副本，之后上游更新它就不跟了。2026-07-31 实测时上游 65 个节日、
兜底 64 个（少 back-to-school-peak-2026），而 CI 里上游根本不存在，
只能用兜底，于是 CI 生成的页面和生产机生成的对不上。

兜底源要真的能当源用，就得有东西把它同步。就是这个脚本。

用法
----
    python3 tools/sync_festivals.py            # 同步，有变化则写入
    python3 tools/sync_festivals.py --check    # 只检查是否落后，不写（CI 用）

`--check` 落后时退出码 1，可以挂进 preflight 或 workflow 当门禁。
"""
import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from festival_engine import _extract_js_array, _parse_js_array  # noqa: E402

UPSTREAM = Path('/home/lee/uk-festival-planner/index.html')
FALLBACK = BASE / 'data' / 'festivals_data.js'
MARKER = 'const FESTIVALS = '

HEADER = """// 节日数据 —— 由 tools/sync_festivals.py 从 ~/uk-festival-planner/index.html 同步。
// 不要手工改这个文件：改上游，然后跑同步脚本。
// 这是 festival_engine.FESTIVAL_SOURCES 的第 2 级回退，CI 里没有上游时用的就是它。
"""


def _ids(data):
    return {d.get('id') or d.get('name') for d in data}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='只检查是否落后于上游，不写入；落后则退出码 1')
    args = ap.parse_args()

    if not UPSTREAM.exists():
        # 云端 / CI 上没有上游，这不是错误 —— 那里本来就该用兜底。
        print(f'ℹ️ 上游不在这台机器上（{UPSTREAM}），跳过')
        return 0

    up_text = UPSTREAM.read_text(encoding='utf-8')
    up_array = _extract_js_array(up_text, MARKER)
    if not up_array:
        print(f'❌ 上游里找不到 `{MARKER}` 数组 —— 上游格式可能变了，先看一眼再说')
        return 2

    up_data = _parse_js_array(up_array)
    if not up_data:
        print('❌ 上游数组解析失败（需要 node）')
        return 2

    old_data = []
    if FALLBACK.exists():
        old_array = _extract_js_array(FALLBACK.read_text(encoding='utf-8'), MARKER)
        if old_array:
            old_data = _parse_js_array(old_array) or []

    missing = _ids(up_data) - _ids(old_data)
    extra = _ids(old_data) - _ids(up_data)

    if not missing and not extra and len(up_data) == len(old_data):
        print(f'✅ 兜底源已是最新（{len(up_data)} 个节日）')
        return 0

    print(f'兜底源落后：上游 {len(up_data)} 个，兜底 {len(old_data)} 个')
    if missing:
        print(f'  兜底缺少：{sorted(missing)}')
    if extra:
        print(f'  兜底多出：{sorted(extra)}')

    if args.check:
        print('\n跑 `python3 tools/sync_festivals.py` 同步后提交。')
        return 1

    # 原样搬数组文本，不重新序列化 —— 保留上游的注释与分组，diff 也好读
    FALLBACK.write_text(HEADER + MARKER + up_array + ';\n', encoding='utf-8')
    print(f'✅ 已写入 {FALLBACK.relative_to(BASE)}（{len(up_data)} 个节日）')
    print('   记得提交，否则 CI 用的还是旧的。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
