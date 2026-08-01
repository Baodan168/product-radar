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
import json
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


def check_festival_fallback(on_prod):
    """仓库内的节日兜底源有没有落后于上游。

    FESTIVAL_SOURCES 第 1 级是 ~/uk-festival-planner/（只在生产机上），
    第 2 级是仓库内的 data/festivals_data.js。云端和 CI 上只有第 2 级 ——
    所以它一旦变旧，那些环境生成的页面就和生产机的对不上。
    2026-07-31 实测：上游 65 个节日、兜底 64 个，CI 页面因此少一个节日。
    这个兜底源以前没有任何脚本维护，现在归 tools/sync_festivals.py 管。
    """
    section('节日兜底源')
    if not on_prod:
        note(INFO, '不在生产机上，跳过', '上游只在生产机上，比不了')
        return False
    script = BASE / 'tools' / 'sync_festivals.py'
    if not script.exists():
        note(WARN, '找不到 tools/sync_festivals.py')
        return False
    rc, out = sh('python3', str(script), '--check')
    if rc == 0:
        note(OK, (out.strip().splitlines() or ['兜底源是最新的'])[-1].lstrip('✅ ').strip())
        return False
    if rc == 1:
        note(BLOCK, '节日兜底源落后于上游',
             out.strip() + '\n修法：python3 tools/sync_festivals.py 然后提交。')
        return True
    note(WARN, '兜底源检查跑不了', out.strip()[:200])
    return False


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
    """读 logs/last_run.json 判定上次跑的结果。

    别回去 grep 日志里的 ❌：详情页验证给每个被淘汰的产品也打 ❌，一次几十条，
    那是过滤器在干正事。这个函数最早就是那么写的（`'❌' in text`），把一次
    完全成功的扫描报成了阻塞项。emoji 同时当装饰和状态信号，靠缩进之类的
    形状特征去区分只是权宜之计 —— 排版一改就又破了。
    现在 cron_scan.sh 直接写机器可读的状态，这里只读它。
    """
    section('上次 cron')
    status_file = BASE / 'logs' / 'last_run.json'
    logs = sorted((BASE / 'logs').glob('cron_*.log'),
                  key=lambda p: p.stat().st_mtime, reverse=True) \
        if (BASE / 'logs').is_dir() else []

    if not status_file.exists():
        if not logs:
            note(INFO, '没有 cron 日志', '这台机器可能不跑定时任务')
        else:
            # 状态文件是随本轮改动引入的；老日志还在但没有状态文件时不臆测成败
            age_h = (time.time() - logs[0].stat().st_mtime) / 3600
            note(INFO, f'还没有运行状态文件（上次日志 {age_h:.1f} 小时前）',
                 'logs/last_run.json 由 cron_scan.sh 写，下次跑完就有了。\n'
                 '在那之前这一项不做判断 —— 猜一个成败还不如不猜。')
        return False

    try:
        st = json.loads(status_file.read_text(encoding='utf-8'))
    except Exception as e:
        note(BLOCK, '运行状态文件读不了', f'{status_file}: {e}')
        return True

    age_h = (time.time() - status_file.stat().st_mtime) / 3600
    log_name = Path(st.get('log') or '?').name

    if not st.get('ok'):
        note(BLOCK, f'上次 cron 失败于 {st.get("failed_step") or "未知步骤"}'
                    f'（{age_h:.1f} 小时前）',
             f'日志：{log_name}\n合并前先解决这个 —— 同步失败会导致用旧代码生成。')
        return True

    note(OK, f'上次 cron 正常（{log_name}，{age_h:.1f} 小时前）')
    warns = st.get('warnings') or []
    if warns:
        note(INFO, f'有 {len(warns)} 条降级告警（不阻塞）', '\n'.join(warns[:5]))
    if age_h > 30:
        note(WARN, f'但已经 {age_h:.0f} 小时没跑了', '确认调度还在生效')
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
        check_festival_fallback(on_prod),
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
