#!/usr/bin/env python3
"""安全修复的回归测试 —— 对应 audit-report 的 P0/P1/P2。

这些问题的共同点是：修好之后从页面上完全看不出来，
一旦被改回去也看不出来，只有测试盯得住。
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))


@pytest.fixture(scope='module')
def platform_js():
    return (BASE / 'assets' / 'platform.js').read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def worker_js():
    return (BASE / 'cloudflare-worker.js').read_text(encoding='utf-8')


# ── P0：浏览器端不得持有 GitHub 凭据 ──────────────────

def test_no_github_token_in_browser_code(platform_js):
    """Token 曾经存在 localStorage 里，页面上任何 JS 都能读走。"""
    lowered = platform_js.lower()
    for banned in ('sync_token_key', 'setsynctoken', 'ghp_', 'github_pat_'):
        assert banned not in lowered, f'浏览器代码里出现了 {banned}'


def test_browser_never_calls_github_api_directly(platform_js):
    """直连 GitHub API 就意味着浏览器得带凭据。"""
    assert 'api.github.com' not in platform_js, '前端仍在直连 GitHub API'


def test_no_prompt_for_credentials(platform_js):
    assert not re.search(r'prompt\s*\([^)]*[Tt]oken', platform_js), '还在用 prompt 要 Token'


def test_sync_endpoint_comes_from_config(platform_js):
    """同步地址由生成期注入，不在前端写死。"""
    assert 'PD.SYNC_ENDPOINT' in platform_js


def test_sync_endpoint_must_be_https():
    """非 https 的端点会让同步请求明文出网，生成期就该拦掉。"""
    src = (BASE / 'generate_platform.py').read_text(encoding='utf-8')
    assert "startswith('https://')" in src, '没有校验端点协议'


# ── P1：同步状态分级，不把「已接收」当「已写入」────────

def test_sync_stages_are_distinct(platform_js):
    """repository_dispatch 的 204 只代表 GitHub 收下了事件，
    不代表 workflow 跑了、写成功了。这两件事必须显示成不同状态。"""
    assert 'SYNC_STAGES' in platform_js
    for stage in ('dispatched', 'written', 'failed', 'unconfigured'):
        assert f'{stage}:' in platform_js or f"'{stage}'" in platform_js, f'缺少 {stage} 阶段'


def test_dispatched_and_written_have_different_labels(platform_js):
    m = re.search(r'const SYNC_STAGES = \{(.*?)\n\};', platform_js, re.S)
    assert m, '找不到 SYNC_STAGES'
    body = m.group(1)
    labels = dict(re.findall(r"(\w+):\s*\['([^']*)'", body))
    assert labels['dispatched'] != labels['written'], '「已提交」和「已写入」显示成一样了'
    assert '已写入' in labels['written']


def test_unconfigured_sync_fails_loudly_not_silently(platform_js):
    """没配端点时要明说，不能假装同步成功。"""
    assert "if (!SYNC_ENDPOINT)" in platform_js
    assert "setSyncStage('local'" in platform_js


# ── P1：Worker 主机边界 ────────────────────────────────

def test_worker_uses_dot_boundary_not_suffix(worker_js):
    """endsWith('amazon.co.uk') 会放行 evilamazon.co.uk。"""
    assert 'function hostAllowed' in worker_js
    m = re.search(r'function hostAllowed\(hostname\) \{(.*?)\n\}', worker_js, re.S)
    body = m.group(1)
    assert '`.${d}`' in body or "'.' + d" in body, 'Worker 没有按点号边界判子域'


@pytest.mark.skipif(not Path('/opt/node22/bin/node').exists() and not Path('/usr/bin/node').exists(),
                    reason='没有 node')
def test_worker_host_allowlist_behaviour(tmp_path):
    """直接在 node 里跑 Worker 的判断函数。"""
    script = tmp_path / 't.mjs'
    script.write_text(f'''
import {{ hostAllowed, validateStatus }} from '{BASE / "cloudflare-worker.js"}';
const cases = {{
  'amazon.co.uk': true,
  'www.amazon.co.uk': true,
  'm.amazon.co.uk': true,
  'evilamazon.co.uk': false,
  'amazon.co.uk.evil.com': false,
  'evil.com': false,
  '': false,
}};
const out = {{}};
for (const [h, want] of Object.entries(cases)) out[h] = [hostAllowed(h), want];
out['_status_ok'] = [validateStatus({{a: 'pending'}}), null];
out['_status_array'] = [validateStatus([]) !== null, true];
out['_status_nonstring'] = [validateStatus({{a: 1}}) !== null, true];
console.log(JSON.stringify(out));
''', encoding='utf-8')
    node = '/opt/node22/bin/node' if Path('/opt/node22/bin/node').exists() else 'node'
    r = subprocess.run([node, str(script)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    got = json.loads(r.stdout)
    for host, (actual, want) in got.items():
        if host.startswith('_'):
            continue
        assert actual == want, f'{host}: 实际 {actual}，期望 {want}'
    assert got['_status_ok'][0] is None, '合法状态被拒'
    assert got['_status_array'][0] is True, '数组没被拒'
    assert got['_status_nonstring'][0] is True, '非字符串值没被拒'


def test_worker_restricts_protocol_port_and_credentials(worker_js):
    assert "target.protocol !== 'https:'" in worker_js, '没限制 https'
    assert 'target.username' in worker_js, '没拒绝 URL 内嵌凭据'
    assert "target.port" in worker_js, '没限制端口'


def test_worker_cors_is_not_wildcard(worker_js):
    """原来是 Access-Control-Allow-Origin: *。"""
    assert "'Access-Control-Allow-Origin': origin" in worker_js
    assert "h.set('Access-Control-Allow-Origin', '*')" not in worker_js


def test_worker_reports_missing_secret_as_501(worker_js):
    assert '501' in worker_js and '同步未配置' in worker_js


# ── P1：跨平台超时 ─────────────────────────────────────

def test_scanner_has_no_sigalrm():
    """SIGALRM 是 Unix 专属，Windows 上直接 AttributeError；
    而且只能在主线程注册，以后并行扫描会踩坑。"""
    src = (BASE / 'run_scan_v2.py').read_text(encoding='utf-8')
    code = re.sub(r'#.*', '', src)
    assert 'SIGALRM' not in code, 'run_scan_v2.py 仍在用 SIGALRM'
    assert 'signal.alarm' not in code, 'run_scan_v2.py 仍在用 signal.alarm'


def test_scanner_uses_portable_timeout():
    src = (BASE / 'run_scan_v2.py').read_text(encoding='utf-8')
    assert 'concurrent.futures' in src
    assert 'TimeoutError' in src


def test_all_python_files_parse():
    """整个仓库在当前 Python 上必须能解析。

    festival_engine.py 曾经因为嵌套同类三引号 f-string 需要 3.12+，
    在 3.11 上直接 SyntaxError，连带 generate_platform.py 起不来。
    """
    bad = []
    for f in list(BASE.glob('*.py')) + list(BASE.glob('oa/*.py')) + \
             list(BASE.glob('sources/*.py')) + list(BASE.glob('tools/*.py')):
        try:
            ast.parse(f.read_text(encoding='utf-8'))
        except SyntaxError as e:
            bad.append(f'{f.name}:{e.lineno} {e.msg}')
    assert not bad, f'这些文件解析失败：{bad}'


# ── P1/P3：workflow 并发与增量写入 ─────────────────────

def test_status_sync_workflow_has_concurrency():
    y = (BASE / '.github' / 'workflows' / 'status-sync.yml').read_text(encoding='utf-8')
    assert 'concurrency:' in y, '缺少并发控制，两次同步会互相覆盖'
    assert 'cancel-in-progress: false' in y, '同步是用户操作，不该被取消'


def test_status_sync_merges_instead_of_overwriting():
    """audit P1：整份覆盖会让并发的两次修改丢一次。"""
    y = (BASE / '.github' / 'workflows' / 'status-sync.yml').read_text(encoding='utf-8')
    assert 'merged' in y and 'current' in y, 'workflow 仍是整份覆盖'
    assert '_schema' in y, '状态文件没有 schema 版本'


def test_status_sync_retries_and_fails_loudly():
    y = (BASE / '.github' / 'workflows' / 'status-sync.yml').read_text(encoding='utf-8')
    assert '::error::' in y, 'push 失败时没有显式报错'
    assert 'rebase' in y, 'push 被拒后没有 rebase 重试'
