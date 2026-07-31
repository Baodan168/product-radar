#!/usr/bin/env python3
"""补货跟进页脱敏 — CLI 入口。

逻辑在 oa/desensitize.py，本文件只是薄壳（和 generate_*.py 同一风格）。

用法：
    python3 desensitize_analysis.py            # 就地脱敏 output/analysis/
    python3 desensitize_analysis.py --check    # 只检查不改，有泄露则退出码 1
    python3 desensitize_analysis.py --dry-run  # 走一遍流程但不落盘

--check 用在 CI（.github/workflows/update.yml 部署前），
这样即使有人直接提交了未脱敏的文件，部署也会红，而不是静默上线。
"""
import argparse
import sys

from oa.desensitize import ANALYSIS_DIR, DesensitizeError, scan_dir, scrub_dir


def main():
    ap = argparse.ArgumentParser(description='补货跟进页发布边界脱敏')
    ap.add_argument('--check', action='store_true',
                    help='只检查不修改；发现敏感数据时退出码 1')
    ap.add_argument('--dry-run', action='store_true',
                    help='执行脱敏流程但不写文件')
    ap.add_argument('--dir', default=None, help=f'目标目录（默认 {ANALYSIS_DIR}）')
    args = ap.parse_args()

    target = args.dir or ANALYSIS_DIR

    if args.check:
        leaks = scan_dir(target)
        if not leaks:
            print(f'✅ {target} 未发现敏感数据')
            return 0
        print(f'❌ {len(leaks)} 个文件仍含敏感数据：', file=sys.stderr)
        for name, items in list(leaks.items())[:10]:
            first = items[0]
            print(f'   {name}: {first[0]} — {first[1]}', file=sys.stderr)
        if len(leaks) > 10:
            print(f'   …另有 {len(leaks) - 10} 个文件', file=sys.stderr)
        print('\n   跑 `python3 desensitize_analysis.py` 脱敏后再提交。', file=sys.stderr)
        return 1

    try:
        changed, untouched = scrub_dir(target, dry_run=args.dry_run)
    except DesensitizeError as e:
        # 脱敏做不干净时宁可整个失败，也不要写出半成品
        print(f'❌ {e}', file=sys.stderr)
        return 2

    verb = '将脱敏' if args.dry_run else '已脱敏'
    print(f'✅ {verb} {len(changed)} 个文件，{len(untouched)} 个无需改动')
    for name in changed[:5]:
        print(f'   {name}')
    if len(changed) > 5:
        print(f'   …另有 {len(changed) - 5} 个')
    return 0


if __name__ == '__main__':
    sys.exit(main())
