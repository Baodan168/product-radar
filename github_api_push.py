"""通过GitHub API推送文件到仓库（绕过git push超时问题）
用法: python3 github_api_push.py "commit message"
"""
import json, os, sys, base64
import urllib.request

REPO = 'liyuhong168/product-radar'
BRANCH = 'main'

def get_token():
    """Read GitHub token from environment (set in .env, sourced by cron)"""
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    # Fallback: read from file (not from git-tracked credentials)
    token_file = os.path.expanduser("~/.hermes/github_token.txt")
    if os.path.exists(token_file):
        with open(token_file) as f:
            return f.read().strip()
    raise RuntimeError("GITHUB_TOKEN not set in environment or ~/.hermes/github_token.txt")

def api(method, path, data=None):
    token = get_token()
    headers = {'Authorization': f'token {token}', 'Content-Type': 'application/json', 'User-Agent': 'hermes'}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f'https://api.github.com{path}', headers=headers, data=body)
    if method != 'POST':
        req.get_method = lambda: method
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

def push_files(files, message):
    """推送指定文件列表到GitHub"""
    ref = api('GET', f'/repos/{REPO}/git/refs/heads/{BRANCH}')
    head_sha = ref['object']['sha']
    commit = api('GET', f'/repos/{REPO}/git/commits/{head_sha}')
    base_tree = commit['tree']['sha']

    # Upload blobs in batches of 5
    tree_items = []
    batch = []
    for rel_path, abs_path in files:
        if not os.path.exists(abs_path):
            continue
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
    print(f'  ✅ 已部署 {len(tree_items)} 个文件')

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
    for subdir in ('data/channels', 'data/history', 'data/discovery', 'output', 'output/data', 'output/assets'):
        full = os.path.join(base, subdir)
        if not os.path.isdir(full):
            continue
        all_files = sorted(os.listdir(full))
        for f in all_files[-12:]:
            if not f.endswith('.json') and not f.endswith('.html') and not f.endswith('.js'):
                continue
            files.append((f'{subdir}/{f}', os.path.join(full, f)))

    # Always-push files
    # 门户壳的 JS 从内联抽到了 output/assets/，漏推的话线上门户会白屏
    for f in ('output/platform.html', 'output/index.html', 'output/assets/portal.js',
              'output/data/radar-all.js', 'output/data/disc-all.js', 'output/data/festivals.js', 'status.json'):
        fp = os.path.join(base, f)
        if os.path.exists(fp):
            files.append((f, fp))

    msg = sys.argv[1] if len(sys.argv) > 1 else 'auto-push'
    push_files(files, msg)
