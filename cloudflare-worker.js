/**
 * Cloudflare Worker — Amazon UK 抓取代理 + 看板状态同步代理
 *
 * 两条路由：
 *   GET  /?url=<amazon-uk-url>   抓取代理（原有功能）
 *   POST /kanban-sync            看板状态同步（audit P0 的修法）
 *
 * ── 为什么要加 /kanban-sync ──
 * 原来选品平台把 GitHub Token 存在浏览器 localStorage 里，直接调
 * repository_dispatch。任何能在页面执行 JS 的代码都能读走那个 Token，
 * 配合同页面的 innerHTML 注入面就是一条完整的凭据窃取链（audit P0）。
 * GitHub Pages 是纯静态的、没有服务端，但这个 Worker 已经在跑了，
 * 加一条路由的边际成本最低，且保住了多设备同步。
 *
 * ── 部署（必须做完这几步同步才会生效）──
 *   1. wrangler deploy   （或在 Cloudflare 控制台粘贴本文件）
 *   2. wrangler secret put GITHUB_TOKEN
 *      Token 只需要 Actions:write（触发 workflow），不需要 contents:write；
 *      实际写文件由 Actions 内置的 GITHUB_TOKEN 完成，带格式校验。
 *   3. 环境变量 ALLOWED_ORIGIN = https://liyuhong168.github.io
 *   4. 把 Worker 地址填进 config.json 的 kanban_sync.endpoint
 *
 * 没配 Secret 时 /kanban-sync 返回 501，前端显示「同步未配置」，
 * 不会静默失败。
 *
 * 注意：从 Service Worker 格式（addEventListener）改成了 Module 格式
 * （export default），因为 Secret 只能通过 env 参数拿到。
 */

const ALLOWED_HOSTS = ['amazon.co.uk'];
const ALLOWED_PATHS = [
  '/gp/new-releases/', '/gp/bestsellers/', '/gp/most-wished-for/',
  '/gp/gifts/', '/gp/movers-and-shakers/', '/s?k=', '/dp/',
];

const REPO = 'liyuhong168/product-radar';
const DISPATCH_EVENT = 'status-sync';

// 看板状态的体量上限，挡住把 Worker 当免费存储用
const MAX_STATUS_ENTRIES = 5000;
const MAX_BODY_BYTES = 512 * 1024;
const MAX_KEY_LEN = 64;
const MAX_VALUE_LEN = 64;

/**
 * 主机是否在白名单内。
 *
 * audit P1：原来是 target.hostname.endsWith(d)，纯字符串后缀匹配没有
 * 主机边界 —— evilamazon.co.uk 满足 endsWith('amazon.co.uk')，
 * 但它不是 Amazon。必须按点号边界判子域。
 */
function hostAllowed(hostname) {
  const host = String(hostname || '').toLowerCase().replace(/\.$/, '');
  return ALLOWED_HOSTS.some(
    (d) => host === d || host === `www.${d}` || host.endsWith(`.${d}`)
  );
}

function corsHeaders(env) {
  const origin = (env && env.ALLOWED_ORIGIN) || 'https://liyuhong168.github.io';
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin',
  };
}

function json(body, status, env) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(env) },
  });
}

/** 看板状态的形状校验：{ [asin]: statusKey }，外加可选 _meta。 */
function validateStatus(data) {
  if (data === null || typeof data !== 'object' || Array.isArray(data)) {
    return '状态必须是一个 JSON 对象';
  }
  const keys = Object.keys(data);
  if (keys.length > MAX_STATUS_ENTRIES) {
    return `条目过多（${keys.length} > ${MAX_STATUS_ENTRIES}）`;
  }
  for (const k of keys) {
    if (k === '_meta') continue;
    if (k.length > MAX_KEY_LEN) return `键过长: ${k.slice(0, 20)}…`;
    const v = data[k];
    if (typeof v !== 'string') return `键 ${k} 的值不是字符串`;
    if (v.length > MAX_VALUE_LEN) return `键 ${k} 的值过长`;
  }
  return null;
}

async function handleKanbanSync(request, env) {
  if (request.method !== 'POST') {
    return json({ error: '只接受 POST' }, 405, env);
  }
  if (!env || !env.GITHUB_TOKEN) {
    // 显式告知未配置，而不是假装成功 —— 和 audit P1
    // 「不要把事件已接收当成写入成功」是同一条原则
    return json({
      error: '同步未配置',
      detail: 'Worker 尚未设置 GITHUB_TOKEN Secret，看板同步不可用。',
    }, 501, env);
  }

  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) {
    return json({ error: '请求体过大' }, 413, env);
  }

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (e) {
    return json({ error: 'JSON 解析失败' }, 400, env);
  }

  const status = payload && payload.status;
  const problem = validateStatus(status);
  if (problem) {
    return json({ error: '状态格式不合法', detail: problem }, 400, env);
  }

  const res = await fetch(`https://api.github.com/repos/${REPO}/dispatches`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'product-radar-kanban-sync',
    },
    body: JSON.stringify({
      event_type: DISPATCH_EVENT,
      client_payload: { status },
    }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    return json({
      error: 'GitHub 拒绝了请求',
      status: res.status,
      detail: detail.slice(0, 300),
    }, 502, env);
  }

  /* 关键：repository_dispatch 返回 204 只代表 GitHub 收下了事件，
     不代表 workflow 跑了，更不代表文件写成功了（audit P1）。
     所以这里回 accepted 而不是 success，前端据此显示「已提交」
     而不是「已同步」，真正的写入结果由前端查 workflow 得到。 */
  return json({
    accepted: true,
    stage: 'dispatched',
    note: '事件已提交，仓库写入结果需要查询 workflow 运行状态',
  }, 202, env);
}

async function handleProxy(request, env) {
  const url = new URL(request.url);
  const targetUrl = url.searchParams.get('url');
  if (!targetUrl) {
    return new Response('Missing url parameter', { status: 400, headers: corsHeaders(env) });
  }

  let target;
  try {
    target = new URL(targetUrl);
  } catch {
    return new Response('Invalid URL', { status: 400, headers: corsHeaders(env) });
  }

  if (target.protocol !== 'https:') {
    return new Response('Only https is allowed', { status: 403, headers: corsHeaders(env) });
  }
  if (target.username || target.password) {
    return new Response('Credentials in URL are not allowed', { status: 403, headers: corsHeaders(env) });
  }
  if (target.port && target.port !== '443') {
    return new Response('Non-default port is not allowed', { status: 403, headers: corsHeaders(env) });
  }
  if (!hostAllowed(target.hostname)) {
    return new Response('Domain not allowed', { status: 403, headers: corsHeaders(env) });
  }
  const pathAndQuery = target.pathname + target.search;
  if (!ALLOWED_PATHS.some((p) => target.pathname.startsWith(p) || pathAndQuery.startsWith(p))) {
    return new Response('Path not allowed', { status: 403, headers: corsHeaders(env) });
  }

  const response = await fetch(target.href, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Accept-Language': 'en-GB,en;q=0.9',
      'Cookie': 'lc-main=en_GB; i18n-prefs=GBP',
    },
  });

  const h = new Headers(response.headers);
  for (const [k, v] of Object.entries(corsHeaders(env))) h.set(k, v);
  return new Response(response.body, { status: response.status, headers: h });
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(env) });
    }
    const url = new URL(request.url);
    if (url.pathname === '/kanban-sync') {
      return handleKanbanSync(request, env);
    }
    return handleProxy(request, env);
  },
};

// 供测试使用
export { hostAllowed, validateStatus };
