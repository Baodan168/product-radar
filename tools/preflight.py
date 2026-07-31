#!/usr/bin/env python3
"""部署前体检 —— 只读，不改任何东西。

把 DEPLOY-CHECKLIST.md 阶段 0 那张「看到什么 → 意味着 → 怎么办」的判断表
变成一条命令。给两类人用：

  - 负责人：跑一次，看最后那行结论决定能不能合并
  - 本机的 Claude Code 会话：开工第一件事跑它，输出就是当前状态

退出码：0 = 可以往下走，1 = 有阻塞项。

用法:
    python3 tools/preflight.py              # 用现有的远端引用
    python3 tools/preflight.py --fetch      # 先 git fetch（会写 .git，但不动工作区）
"""
import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
UI_BRANCH = 'claude/oa-portal-ui-upgrade-ts4zrf'

BLOCK, WARN, OK, INFO = 'BLOCK', 'WARN', 'OK', 'INFO'
MARK = {BLOCK: '❌', WARN: '⚠️ ', OK: '✅', INFO: '·　'}

findings = []


def note(level, title, detail=''):
    findings.append((level, title, detail))
    print(f'{MARK[level]} {title}')
    for line in (detail or '').splitlines():
        if line.strip():
            print(f'      {line}')


def sh(*args, cwd=BASE):
    """跑一条命令，返回 (returncode, stdout+stderr)。不抛异常。"""
    try:
        r = subprocess.run(args, cwd=str(cwd), capture_output=True,
                           text=True, timeout=180)
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return 127, f'命令不存在: {args[0]}'
    except subprocess.TimeoutExpired:
        return 124, '超时'


def section(name):
    print(f'\n── {name} ' + '─' * max(0, 58 - len(name)))


# ══════════════════════════════════════════════════════════
def check_environment():
    section('运行环境')
    # 本机独有的依赖，用来判断这是不是 hermes 那台机器
    markers = {
        '~/.hermes/.env（cron 的凭据来源）': Path.home() / '.hermes' / '.env',
        '~/product-analysis/（补货引擎源码）': Path.home() / 'product-analysis',
        '~/hermes-agent/': Path.home() / 'hermes-agent',
    }
    present = {k: p for k, p in markers.items() if p.exists()}
    if present:
        note(OK, f'看起来在生产机上（命中 {len(present)}/{len(markers)} 个本机标志）',
             '\n'.join(f'有 {k}' for k in present))
    else:
        note(INFO, '不在生产机上（没有本机标志）',
             '补货管道、cron 日志、上游源码这几项检查会跳过。\n'
             '这是正常的 —— Claude Code 的云端会话就是这种情况。')
    return bool(present)


def check_git(on_prod):
    section('Git 状态')
    blocked = False

    rc, branch = sh('git', 'branch', '--show-current')
    rc, head = sh('git', 'rev-parse', '--short', 'HEAD')
    note(INFO, f'当前分支 {branch or "(detached)"} @ {head}')

    rc, main_sha = sh('git', 'rev-parse', '--short', 'origin/main')
    if rc != 0:
        note(WARN, '读不到 origin/main', '先跑 git fetch origin')
    else:
        note(INFO, f'origin/main @ {main_sha}')

    # UI 分支是否已经合进 main
    rc, merged = sh('git', 'branch', '-r', '--merged', 'origin/main')
    if rc == 0:
        if f'origin/{UI_BRANCH}' in merged:
            note(OK, 'UI 升级分支已经合进 origin/main', '这次不需要再合并')
        else:
            rc2, ahead = sh('git', 'rev-list', '--count',
                            f'origin/main..origin/{UI_BRANCH}')
            if rc2 == 0 and ahead.isdigit():
                note(INFO, f'UI 升级分支领先 origin/main {ahead} 个 commit',
                     '这些就是待部署的内容')

    # 本地脏文件
    rc, dirty = sh('git', 'status', '--porcelain')
    lines = [l for l in dirty.splitlines() if l.strip()] if dirty else []
    artifacts = [l for l in lines if re.search(r'\boutput/', l)]
    others = [l for l in lines if l not in artifacts]
    if not lines:
        note(OK, '工作区干净')
    else:
        if artifacts:
            note(OK, f'{len(artifacts)} 个 output/ 下的产物有改动',
                 'cron 重新生成的，正常，合并时会被覆盖')
        if others:
            note(WARN, f'{len(others)} 个非产物文件有本地改动',
                 '合并前先看清楚这些是什么：\n' +
                 '\n'.join(others[:12]) +
                 ('\n…' if len(others) > 12 else ''))

    # stash 积压（cron_scan.sh:11 每次 push 但从不 pop）
    rc, stash = sh('git', 'stash', 'list')
    n = len([l for l in stash.splitlines() if l.strip()]) if stash else 0
    if n == 0:
        note(OK, 'stash 是空的')
    elif n <= 3:
        note(INFO, f'stash 有 {n} 层', 'cron_scan.sh:11 每次跑都 push 但从不 pop')
    else:
        note(WARN, f'stash 积了 {n} 层',
             'cron_scan.sh:11 只 push 不 pop。确认都是自动产物快照后可以 git stash clear')
    return blocked


def check_artifacts_fresh():
    """产物是不是比源文件旧 —— 旧了说明没重新生成，会出「混合体」。"""
    section('产物新鲜度')
    sources = [BASE / 'shared/oa-theme.css', BASE / 'templates/portal.html',
               BASE / 'templates/platform.html', BASE / 'assets/portal.js',
               BASE / 'assets/platform.js']
    sources = [p for p in sources if p.exists()]
    if not sources:
        note(WARN, '找不到源文件，跳过')
        return False
    newest_src = max(p.stat().st_mtime for p in sources)

    blocked = False
    for rel in ('output/index.html', 'output/platform.html'):
        p = BASE / rel
        if not p.exists():
            note(BLOCK, f'{rel} 不存在', '跑 generate_portal.py / generate_platform.py')
            blocked = True
            continue
        if p.stat().st_mtime < newest_src:
            age = (newest_src - p.stat().st_mtime) / 3600
            note(BLOCK, f'{rel} 比源文件旧 {age:.1f} 小时',
                 '这就是「旧 markup + 新 CSS」混合体的成因。\n'
                 '跑 python3 generate_platform.py && python3 generate_portal.py')
            blocked = True
        else:
            note(OK, f'{rel} 不比源文件旧')

    # output/assets/portal.js 由 generate_portal.py 同步，cron_scan.sh 不跑它
    mirror = BASE / 'output/assets/portal.js'
    src = BASE / 'assets/portal.js'
    if src.exists():
        if not mirror.exists():
            note(WARN, 'output/assets/portal.js 不存在',
                 'cron_scan.sh 不跑 generate_portal.py，需要手动补一次。\n'
                 '（线上有 update.yml 的拷贝顺序兜着，但这是巧合不是设计）')
        elif mirror.stat().st_mtime < src.stat().st_mtime:
            note(WARN, 'output/assets/portal.js 比 assets/portal.js 旧',
                 '跑一次 python3 generate_portal.py')
        else:
            note(OK, 'output/assets/portal.js 是新的')
    return blocked


def check_desensitize():
    section('补货页脱敏门禁')
    cli = BASE / 'desensitize_analysis.py'
    if not cli.exists():
        note(WARN, '找不到 desensitize_analysis.py，跳过')
        return False
    rc, out = sh(sys.executable, str(cli), '--check')
    if rc == 0:
        note(OK, '未发现敏感数据', 'update.yml 的 --check 门禁会放行')
    else:
        note(BLOCK, 'output/analysis/ 里有未脱敏的内容',
             '这会让 update.yml 拦下**整个部署** —— 站点当天完全不更新。\n'
             '修法：python3 desensitize_analysis.py（幂等，可重复跑）\n'
             '输出：' + (out.splitlines()[-1] if out else ''))
    return rc != 0


def check_tests():
    section('回归测试')
    rc, out = sh(sys.executable, '-m', 'pytest', 'tests/', '-q')
    tail = out.splitlines()[-1] if out else ''
    if rc == 0:
        note(OK, f'测试全绿  {tail}')
    elif rc == 127 or 'No module named pytest' in out:
        note(WARN, '没装 pytest，跳过', 'pip install pytest')
        return False
    else:
        note(BLOCK, '测试有失败', tail)
    return rc not in (0, 127) and 'No module named pytest' not in out


def check_restock_pipeline(on_prod):
    """最阴的那个隐患：补货管道少了脱敏那一步。"""
    section('补货管道（仓库外）')
    if not on_prod:
        note(INFO, '不在生产机上，跳过')
        return False
    candidates = [Path.home() / 'product-analysis' / 'restock_pipeline.sh',
                  BASE / 'restock_pipeline.sh']
    script = next((p for p in candidates if p.exists()), None)
    if script is None:
        note(WARN, '找不到 restock_pipeline.sh',
             '找到它之后确认里面有 desensitize_analysis.py')
        return False
    text = script.read_text(encoding='utf-8', errors='replace')
    if 'desensitize' in text:
        note(OK, f'{script.name} 里有脱敏调用')
        return False
    note(BLOCK, f'{script.name} 里没有 desensitize_analysis.py',
         f'路径：{script}\n'
         '后果：下个周一/四补货管道会把未脱敏 HTML 推到 main，\n'
         'update.yml 的 --check 会拦下整个部署 —— 站点那天完全不更新，\n'
         '而失败只在 GitHub Actions 里可见，不在 cron 摘要里。\n'
         '修法：在 cp 产物之后、git push 之前加一行\n'
         '      python3 desensitize_analysis.py')
    return True


def check_last_cron(on_prod):
    section('上次 cron')
    logs = sorted((BASE / 'logs').glob('cron_*.log'),
                  key=lambda p: p.stat().st_mtime, reverse=True) \
        if (BASE / 'logs').is_dir() else []
    if not logs:
        note(INFO, '没有 cron 日志', '这台机器可能不跑定时任务')
        return False
    latest = logs[0]
    age_h = (time.time() - latest.stat().st_mtime) / 3600
    text = latest.read_text(encoding='utf-8', errors='replace')
    # 只有管线级失败才算失败。扫描器给每个被淘汰的产品也打 ❌
    # （"❌ <标题> → 包装尺寸 60x50x0cm (限30x21x6cm)"），一次扫描能有几十条，
    # 那是过滤器在干正事。区分靠缩进：cron_scan.sh 的失败 echo 顶格，
    # 产品淘汰记录由 run_scan_v2.py 缩进打印。
    hard = [l for l in text.splitlines() if l.startswith('❌')]
    if hard:
        note(BLOCK, f'上次 cron 有失败（{latest.name}，{age_h:.1f} 小时前）',
             '\n'.join(hard[:8]) + '\n合并前先解决这个 —— 同步失败会导致用旧代码生成。')
        return True
    note(OK, f'上次 cron 正常（{latest.name}，{age_h:.1f} 小时前）')
    # 降级告警（BSR 抓取、平台/门户生成）不阻塞，但值得看一眼
    soft = [l.strip() for l in text.splitlines() if '⚠️' in l]
    if soft:
        note(INFO, f'有 {len(soft)} 条降级告警（不阻塞）', '\n'.join(soft[:5]))
    if age_h > 30:
        note(WARN, f'但已经 {age_h:.0f} 小时没跑了', '确认 crontab 还在生效')
    return False


# ══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true',
                    help='先 git fetch origin（写 .git，不动工作区）')
    args = ap.parse_args()

    print('部署前体检 —— 只读，不改任何东西')
    print(f'仓库：{BASE}')

    if args.fetch:
        rc, out = sh('git', 'fetch', 'origin', '--quiet')
        print(f'git fetch: {"ok" if rc == 0 else out}')

    on_prod = check_environment()
    blockers = [
        check_git(on_prod),
        check_artifacts_fresh(),
        check_desensitize(),
        check_tests(),
        check_restock_pipeline(on_prod),
        check_last_cron(on_prod),
    ]

    n_block = sum(1 for lv, _, _ in findings if lv == BLOCK)
    n_warn = sum(1 for lv, _, _ in findings if lv == WARN)

    print('\n' + '═' * 62)
    if n_block:
        print(f'❌ 结论：有 {n_block} 项阻塞、{n_warn} 项提醒 —— 先解决阻塞项再合并')
        print('   阻塞项：')
        for lv, title, _ in findings:
            if lv == BLOCK:
                print(f'     · {title}')
    elif n_warn:
        print(f'✅ 结论：没有阻塞项，{n_warn} 项提醒 —— 看一眼提醒后可以合并')
    else:
        print('✅ 结论：全部通过，可以合并')
    print('═' * 62)
    print('下一步看 DEPLOY-CHECKLIST.md')
    return 1 if n_block else 0


if __name__ == '__main__':
    sys.exit(main())
