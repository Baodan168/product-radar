#!/usr/bin/env python3
"""趋势发现数据校验 — CLI 入口。

背景（2026-10-15 审查结论）：discovery JSON 由 LLM（cron）生成，输出格式会随机漂移——
10-03 整天缺 signal_scores/action/competition，10-05 整天分数用 0-10 制（其余为 0-100），
前端进度条/看板排序被直接污染且无任何告警。本脚本是发布边界的硬门禁（与
desensitize_analysis.py --check 同一风格）：坏数据宁可拦下部署，不要静默上线。

用法：
    python3 validate_discovery.py                          # 校验 data/discovery/ 全部
    python3 validate_discovery.py --file data/discovery/2026-10-15.json
                                                           # 单文件（cron 部署前自检用）
    python3 validate_discovery.py --check                  # CI 门禁：有问题退出码 1

宽限期（--recent-days，默认 35）：目录模式下只对近期文件做完整校验——
discovery 数据由 LLM 生成，格式契约 2026 年中多次演进（6-7 月旧文件缺 date/summary
顶层字段属正常历史），全量严校会让 CI 永久红。老文件只验 JSON 可解析。

规则分级：
    ERROR → CI/cron 拦截。字段缺失、分数越界、分数制漂移（0-10 混入 0-100）、
            signal_scores 结构损坏——这些会让前端区块静默空白或排序污染。
    WARN  → 只提示不拦截。amazon_keyword 词数出 5-9 区间、trend_forecast 过短、
            recommendation 不在枚举内（历史 90+ 种写法无法自动归一，只对新数据生效）。
"""
import argparse
import datetime
import json
import os
import re
import sys
from typing import TypeGuard

DISCOVERY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'discovery')

# insight 必须包含的字段（缺失 = ERROR）
REQUIRED_INSIGHT_FIELDS = [
    'keyword', 'keyword_cn', 'amazon_keyword', 'search_1688',
    'demand_signals', 'trend_score', 'trend_direction', 'reason',
    'action', 'competition', 'signal_scores',
]
REQUIRED_TOP_FIELDS = ['date', 'scan_date', 'summary', 'insights']
REQUIRED_SCORE_FIELDS = ['trend', 'gap', 'profit', 'final', 'recommendation']
REC_ENUM = {'strong_buy', 'buy', 'watch', 'pass'}
KW_WORDS_MIN, KW_WORDS_MAX = 5, 9
FORECAST_MIN_CHARS = 300
# 分数制漂移判定：全部子分 ≤ 10 而 trend_score ≥ 40 → 0-10 制混入 0-100 体系
SCALE_DRIFT_TREND_SCORE = 40
SCALE_DRIFT_MAX_SUB = 10


def _is_num(v) -> TypeGuard[float]:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_file(path):
    """校验单个 discovery JSON，返回 (errors, warns)。两条列表元素均为字符串。"""
    errors, warns = [], []
    fname = os.path.basename(path)

    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f'{fname}: JSON 解析失败 — {e}'], []
    except OSError as e:
        return [f'{fname}: 文件读取失败 — {e}'], []

    if not isinstance(data, dict):
        return [f'{fname}: 顶层不是 object'], []

    # 顶层字段
    for field in REQUIRED_TOP_FIELDS:
        if field not in data or data[field] in (None, '', []):
            errors.append(f'{fname}: 顶层缺失 {field}')

    insights = data.get('insights')
    if not isinstance(insights, list) or not insights:
        errors.append(f'{fname}: insights 非数组或为空')
        return errors, warns

    # trend_forecast：dict 已由 generate_platform 归一化兜底 → WARN；缺失/过短 → WARN
    tf = data.get('trend_forecast')
    if tf is None:
        warns.append(f'{fname}: 缺 trend_forecast（OA门户趋势预测板块当日空白）')
    elif isinstance(tf, dict):
        warns.append(f'{fname}: trend_forecast 是 dict（generate_platform 会归一为字符串，但违反 prompt 契约）')
    elif isinstance(tf, str) and len(tf) < FORECAST_MIN_CHARS:
        warns.append(f'{fname}: trend_forecast 过短（{len(tf)} < {FORECAST_MIN_CHARS} 字）')

    seen_keywords = set()
    for i, ins in enumerate(insights):
        tag = f'{fname}[{i}]'
        if not isinstance(ins, dict):
            errors.append(f'{tag}: insight 不是 object')
            continue

        kw = str(ins.get('keyword') or f'#{i}')
        if kw in seen_keywords:
            warns.append(f'{tag}: 关键词当日重复 — {kw}')
        seen_keywords.add(kw)

        # 必填字段
        for field in REQUIRED_INSIGHT_FIELDS:
            v = ins.get(field)
            if v is None or v == '' or v == []:
                errors.append(f'{tag} ({kw}): 缺 {field}')

        # trend_score 越界
        ts = ins.get('trend_score')
        if _is_num(ts) and not (0 <= ts <= 100):
            errors.append(f'{tag} ({kw}): trend_score={ts} 越界（应 0-100）')

        # amazon_keyword 词数（WARN）
        akw = ins.get('amazon_keyword') or ''
        n_words = len(str(akw).split())
        if akw and not (KW_WORDS_MIN <= n_words <= KW_WORDS_MAX):
            warns.append(f'{tag} ({kw}): amazon_keyword {n_words} 词（契约 5-9）— {akw}')

        # demand_signals（WARN：prompt 契约 ≥3）
        ds = ins.get('demand_signals')
        if isinstance(ds, list) and len(ds) < 3:
            warns.append(f'{tag} ({kw}): demand_signals 仅 {len(ds)} 条（契约 ≥3）')

        # signal_scores 结构
        ss = ins.get('signal_scores')
        if ss is None:
            continue  # 缺失已在必填字段报 ERROR
        if not isinstance(ss, dict):
            errors.append(f'{tag} ({kw}): signal_scores 不是 object')
            continue
        for field in REQUIRED_SCORE_FIELDS:
            if field not in ss or ss[field] in (None, ''):
                errors.append(f'{tag} ({kw}): signal_scores 缺 {field}')

        # 分数制漂移：子分全 ≤10 且 trend_score ≥40
        sub = [ss.get(k) for k in ('trend', 'gap', 'profit', 'final') if _is_num(ss.get(k))]
        if sub and all(s <= SCALE_DRIFT_MAX_SUB for s in sub):
            ts2 = ins.get('trend_score')
            if _is_num(ts2) and ts2 >= SCALE_DRIFT_TREND_SCORE:
                errors.append(
                    f'{tag} ({kw}): 疑似 0-10 分制混入 0-100 体系'
                    f'（sub={sub} 而 trend_score={ts2}）— 10-05 事故模式')
            elif len(insights) > 1:
                warns.append(f'{tag} ({kw}): 子分全部 ≤10，请人工确认不是 0-10 分制')

        # 分数越界（0-100）
        for field in ('trend', 'gap', 'profit', 'final'):
            v = ss.get(field)
            if _is_num(v) and not (0 <= v <= 100):
                errors.append(f'{tag} ({kw}): signal_scores.{field}={v} 越界（应 0-100）')

        # recommendation 枚举（WARN：历史 90+ 变体不追溯拦截）
        rec = ss.get('recommendation')
        if isinstance(rec, str) and rec not in REC_ENUM:
            warns.append(f'{tag} ({kw}): recommendation="{rec[:30]}" 不在枚举 {sorted(REC_ENUM)}')

        # demand_signals 元素类型
        if isinstance(ds, list):
            bad = [x for x in ds if not isinstance(x, str)]
            if bad:
                errors.append(f'{tag} ({kw}): demand_signals 含非字符串元素')

    return errors, warns


def iter_files(target):
    """target 为文件路径时返回 [target]，为目录时返回目录下全部日期 JSON。"""
    if os.path.isfile(target):
        return [target]
    files = []
    for fn in sorted(os.listdir(target)):
        if re.match(r'2026-\d{2}-\d{2}\.json$', fn):
            files.append(os.path.join(target, fn))
    return files


def main():
    ap = argparse.ArgumentParser(description='趋势发现数据校验（发布边界门禁）')
    ap.add_argument('target', nargs='?', default=None,
                    help='文件或目录（默认 data/discovery/）')
    ap.add_argument('--file', dest='single_file', default=None,
                    help='只校验单个 JSON 文件')
    ap.add_argument('--recent-days', type=int, default=35,
                    help='目录模式宽限期：仅对文件名日期在近 N 天内的文件做完整校验（默认 35）')
    ap.add_argument('--check', action='store_true',
                    help='CI 模式：存在 ERROR 时退出码 1（WARN 只打印）')
    args = ap.parse_args()

    target = args.single_file or args.target or DISCOVERY_DIR
    if not os.path.exists(target):
        print(f'❌ 目标不存在: {target}', file=sys.stderr)
        return 2

    files = iter_files(target)
    if not files:
        print(f'❌ 未找到 discovery JSON: {target}', file=sys.stderr)
        return 2

    # 宽限期：目录模式下，文件名日期早于 N 天前的文件只验 JSON 可解析
    strict, legacy = [], []
    if os.path.isdir(target) and args.recent_days >= 0:
        cutoff = datetime.date.today() - datetime.timedelta(days=args.recent_days)
        for path in files:
            m = re.match(r'(\d{4}-\d{2}-\d{2})\.json$', os.path.basename(path))
            if m and datetime.date.fromisoformat(m.group(1)) >= cutoff:
                strict.append(path)
            else:
                legacy.append(path)
    else:
        strict = files

    all_errors, all_warns = [], []
    for path in legacy:
        try:
            with open(path, encoding='utf-8') as f:
                json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            all_errors.append(f'{os.path.basename(path)}: JSON 损坏 — {e}')

    for path in strict:
        errs, warns = validate_file(path)
        all_errors.extend(errs)
        all_warns.extend(warns)

    # 汇总输出
    n_files = len(files)
    n_strict = len(strict)
    if not all_errors and not all_warns:
        print(f'✅ {n_files} 个 discovery 文件全部通过校验（{n_strict} 严格 + {len(legacy)} 宽限）')
        return 0

    if all_errors:
        print(f'❌ {len(all_errors)} 个 ERROR / {len(all_warns)} 个 WARN（{n_files} 个文件，其中 {n_strict} 严格校验）：')
        for e in all_errors[:20]:
            print(f'   [ERROR] {e}')
        if len(all_errors) > 20:
            print(f'   …另有 {len(all_errors) - 20} 个 ERROR')
    else:
        print(f'⚠️ 0 ERROR / {len(all_warns)} 个 WARN（{n_files} 个文件，其中 {n_strict} 严格校验）')
    for w in all_warns[:15]:
        print(f'   [WARN] {w}')
    if len(all_warns) > 15:
        print(f'   …另有 {len(all_warns) - 15} 个 WARN')

    if args.check and all_errors:
        print('\n   修复上方 ERROR 后重新推送（历史数据参照 data/discovery/*.bak-* 备份）。', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
