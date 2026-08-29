"""通过GitHub API推送文件到仓库（绕过git push超时问题）
用法: python3 github_api_push.py "commit message"

2026-08-29 产物出库（PROPOSAL-artifacts-out-of-git.md 第 2 步落地）：
只推 数据（data/）+ 补货页（output/analysis/）+ status.json/根 assets。
index.html / platform.html / output/data|assets 由 CI 从 data/ 现场生成
（.github/workflows/update.yml），不再从本机推 —— 推送量从 ~40 文件
降到数据变更集，cron 900s 预算里的 deploy 步骤基本不再占时。
"""
import json, os, sys, base64, time, hashlib
import urllib.request
import urllib.error
import http.client

REPO = 'Baodan168/product-radar'
BRANCH = 'main'

# 部署只推「内容变化」的文件：用 sha1 状态文件记录上次推送的文件指纹，
# 未变化的文件跳过（output/analysis 85 个 html 每次全量重传是 900s 预算下
# 最大的浪费——138 文件全推 ~150s，变更集通常只有 ~40 个文件 ~50s）。
# 状态文件放 logs/（gitignored），首次运行无状态文件时全量推送。
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'push_state.json')

def _file_sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def _load_state():
    try:
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        tmp = STATE_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        print(f'  ⚠️ 状态文件写入失败（不影响推送）: {e}')

def get_token():
    """优先读文件 token（classic PAT，写权限齐全），env 里的 fine-grained PAT 作 fallback。

    2026-08-28 统一修复（与 product-radar-au 一致）：.env 的 GITHUB_TOKEN 是
    fine-grained PAT，授权范围有限（曾只授权本仓库、未授权 AU 仓库导致 AU 部署
    403）。本仓库当前可用是因 fine-grained 恰好有本仓库写权限——为防其权限变更
    时静默断更，统一优先使用 ~/.hermes/github_token.txt 的 classic PAT。
    """
    token_file = os.path.expanduser("~/.hermes/github_token.txt")
    if os.path.exists(token_file):
        with open(token_file) as f:
            tok = f.read().strip()
        if tok:
            return tok
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    raise RuntimeError("GITHUB_TOKEN not set in environment or ~/.hermes/github_token.txt")

def api(method, path, data=None, _retries=2):
    """GitHub API 调用，带重试（GFW 间歇阻断 api.github.com 443 → RemoteDisconnected，重试可过）
    timeout=30（2026-08-13 从 60 调低）：正常响应 <4s；单调用最坏耗时 30+2+30 = 62s，
    配合外层 cron 部署 timeout 180s，一次 GFW 断连不再拖垮整个部署步骤。"""
    token = get_token()
    headers = {'Authorization': f'token {token}', 'Content-Type': 'application/json', 'User-Agent': 'hermes'}
    body = json.dumps(data).encode() if data else None
    last_err = None
    for attempt in range(_retries):
        try:
            req = urllib.request.Request(f'https://api.github.com{path}', headers=headers, data=body)
            if method != 'POST':
                req.get_method = lambda: method
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.RemoteDisconnected) as e:
            last_err = e
            if attempt < _retries - 1:
                time.sleep(2 * (attempt + 1))  # 2s, 4s backoff
    raise last_err

def push_files(files, message):
    """推送指定文件列表到GitHub（只推内容变化的文件）"""
    state = _load_state()
    changed = []
    for rel_path, abs_path in files:
        if not os.path.exists(abs_path):
            continue
        sha = _file_sha1(abs_path)
        if state.get(rel_path) == sha:
            continue  # 内容未变，跳过
        changed.append((rel_path, abs_path, sha))

    if not changed:
        print('  无变更（所有文件 hash 一致，跳过推送）')
        return

    ref = api('GET', f'/repos/{REPO}/git/refs/heads/{BRANCH}')
    head_sha = ref['object']['sha']
    commit = api('GET', f'/repos/{REPO}/git/commits/{head_sha}')
    base_tree = commit['tree']['sha']

    # Upload blobs in batches of 5
    tree_items = []
    batch = []
    for rel_path, abs_path, _ in changed:
        batch.append((rel_path, abs_path))
        if len(batch) >= 5:
            tree_items.extend(_upload_batch(batch))
            batch = []
    if batch:
        tree_items.extend(_upload_batch(batch))

    if not tree_items:
        print('  无变更')
        return

    # Create tree
    tree = api('POST', f'/repos/{REPO}/git/trees', {'base_tree': base_tree, 'tree': tree_items})
    # Create commit
    new_commit = api('POST', f'/repos/{REPO}/git/commits', {
        'message': message, 'tree': tree['sha'], 'parents': [head_sha]
    })
    # Update ref
    api('PATCH', f'/repos/{REPO}/git/refs/heads/{BRANCH}', {'sha': new_commit['sha']})
    print(f'  ✅ 已部署 {len(tree_items)} 个文件（跳过 {len(files)-len(changed)} 个未变更）')
    # 推送成功后更新状态文件
    for rel_path, _, sha in changed:
        state[rel_path] = sha
    _save_state(state)

def _upload_batch(batch):
    items = []
    for rel_path, abs_path in batch:
        with open(abs_path, 'rb') as f:
            content = f.read()
        blob = api('POST', f'/repos/{REPO}/git/blobs',
                   {'content': base64.b64encode(content).decode(), 'encoding': 'base64'})
        items.append({'path': rel_path, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    return items

if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    files = []

    import glob
    # 2026-08-29 产物出库：'output', 'output/data', 'output/assets' 已从本机推送
    # 白名单移除 —— 那三类是 CI 的生成物（update.yml），本机推了也会被 CI 覆盖。
    for subdir in ('data/channels', 'data/history', 'data/discovery'):
        full = os.path.join(base, subdir)
        if not os.path.isdir(full):
            continue
        all_files = sorted(os.listdir(full))
        for f in all_files[-12:]:
            if not f.endswith('.json') and not f.endswith('.html') and not f.endswith('.js'):
                continue
            files.append((f'{subdir}/{f}', os.path.join(full, f)))

    # ⚠️ output/analysis 全量推送（补货详情页+列表页，不能截断）
    # 2026-07-31 修复：此前 subdir 元组缺 output/analysis，补货数据从未推送到线上
    ana_dir = os.path.join(base, 'output/analysis')
    if os.path.isdir(ana_dir):
        for f in sorted(os.listdir(ana_dir)):
            if f.endswith('.html'):
                files.append((f'output/analysis/{f}', os.path.join(ana_dir, f)))

    # Always-push files（2026-08-29 起不再含 output/*：门户 HTML/数据 JS 由 CI 生成）
    for f in ('status.json',
              # 顶层 assets/ 是生成器的源文件（模板从仓库根路径引用），
              # 本机改动未 git 提交时由这里兜底同步到远程，漏了会白屏。
              'assets/platform.js', 'assets/portal.js'):
        fp = os.path.join(base, f)
        if os.path.exists(fp):
            files.append((f, fp))

    msg = sys.argv[1] if len(sys.argv) > 1 else 'auto-push'
    push_files(files, msg)
