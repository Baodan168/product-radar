/* ════════════════════════════════════════════
   选品平台 v6
   配套 templates/platform.html，由 generate_platform.py 装配

   从 generate_platform.py 的 f-string 里抽出来的。原来 700 行 JS 混在
   Python 大字符串里，每个 { 都要写成 {{，且 HTML 文本 / 属性 / JS 字符串 /
   URL 四种语境共用一个 esc()，这是 audit P0 的直接成因。

   现在：
   - 数据从 window.PLATFORM_DATA 读，不再靠字符串插值拼进代码
   - esc() 只管 HTML 文本，escAttr() 管属性，safeUrl() 管 href/src
   - 没有任何内联 onclick，全部走 data-act + 事件委托
   ════════════════════════════════════════════ */
(function () {
'use strict';

var PD = window.PLATFORM_DATA || {};

const DATES = PD.DATES;
const RADAR_DATES = PD.RADAR_DATES;
const DISC_DATES = PD.DISC_DATES;
const STATUS = PD.STATUS;
const PROD_STATUS = PD.PROD_STATUS;
const SEASON_EVENTS = PD.SEASON_EVENTS;
const METRICS = PD.METRICS;
const SEARCH_INDEX = PD.SEARCH_INDEX;
const KANBAN_COLS = PD.KANBAN_COLS;
const INJECT_CFG = PD.INJECT_CFG;
const SK = 'pp_v3_status';
const OLD_SK = 'productRadar_v2_status';
const STATUS_FILE = 'data/kanban_status.json';
// 同步端点从生成期注入（config.json 的 kanban_sync.endpoint）。
// 没配就只在本地存，不做远端同步 —— 并且明确显示「未配置」。
const SYNC_ENDPOINT = PD.SYNC_ENDPOINT || '';
let SERVER_STATUS = {};
let syncing = false;

// Migrate old key
(function(){try{const o=JSON.parse(localStorage.getItem(OLD_SK)||'{}');const c=JSON.parse(localStorage.getItem(SK)||'{}');if(Object.keys(o).length>0&&Object.keys(c).length===0)localStorage.setItem(SK,JSON.stringify(o))}catch(e){}})();

/* ── 同步状态显示 ────────────────────────────
   audit P1：原来 repository_dispatch 一返回成功就显示「已同步」，
   但那个 204 只代表 GitHub 收下了事件 —— workflow 可能没跑、可能校验
   失败、可能被并发覆盖。用户看到「已同步」，刷新后状态却没了。
   所以把阶段拆开，每个阶段说的是它真正确认了的事。 */
const SYNC_STAGES = {
  idle:        ['⚪ 未同步',   'var(--oa-sub)'],
  unconfigured:['⚪ 同步未配置','var(--oa-sub)'],
  local:       ['💾 已存本地', 'var(--oa-sub)'],
  sending:     ['⏳ 提交中…',  'var(--oa-orange)'],
  dispatched:  ['📨 已提交，等待写入', 'var(--oa-orange)'],
  written:     ['✅ 已写入仓库','var(--oa-green)'],
  failed:      ['❌ 同步失败', 'var(--oa-red)'],
};

function setSyncStage(stage, detail) {
  const el = document.getElementById('syncStatus');
  if (!el) return;
  const [label, color] = SYNC_STAGES[stage] || SYNC_STAGES.idle;
  el.textContent = label;
  el.style.color = color;
  el.title = detail || label;
  el.dataset.stage = stage;
}

// Fetch server status on load
async function fetchServerStatus() {
  try {
    const r = await fetch(STATUS_FILE + '?t=' + Date.now(), {cache: 'no-store'});
    if (!r.ok) return;
    const data = await r.json();
    if (!data || typeof data !== 'object') return;
    SERVER_STATUS = data;
    const local = JSON.parse(localStorage.getItem(SK) || '{}');
    // 比较 _meta.ts，服务端更新时才覆盖本地
    var localTs = (local._meta && local._meta.ts) || 0;
    var serverTs = (data._meta && data._meta.ts) || 0;
    if (serverTs > localTs) {
      localStorage.setItem(SK, JSON.stringify(Object.assign({}, PROD_STATUS, local, data)));
    }
    setSyncStage('written', '仓库最后写入 ' +
      (serverTs ? new Date(serverTs).toLocaleString('zh-CN') : '时间未知'));
  } catch(e) { console.warn('读取远端状态失败:', e); }
}
fetchServerStatus();

function getSt(){try{const local=JSON.parse(localStorage.getItem(SK)||'{}');return Object.assign({},PROD_STATUS,SERVER_STATUS,local)}catch(e){return Object.assign({},PROD_STATUS,SERVER_STATUS)}}

function saveSt(a,s,all){
  var t = all || getSt();
  if(!all){if(s==='pending')delete t[a];else t[a]=s;}
  t._meta = {ts: Date.now(), src: 'web'};
  localStorage.setItem(SK, JSON.stringify(t));
  syncToServer();
}

/* 同步走 Worker 代理，浏览器不再持有任何 GitHub 凭据。
   原来这里从 localStorage 读一个 Token 直接调 GitHub API —— 任何能在
   本页执行 JS 的代码都能读走它（audit P0）。Token 现在只存在于
   Cloudflare Worker 的 Secret 里。 */
async function syncToServer() {
  if (syncing) return;
  if (!SYNC_ENDPOINT) {
    setSyncStage('local', '未配置同步端点，状态只保存在本机浏览器。' +
      '配置方法见 cloudflare-worker.js 顶部说明。');
    return;
  }
  syncing = true;
  setSyncStage('sending');
  try {
    const status = JSON.parse(localStorage.getItem(SK) || '{}');
    const res = await fetch(SYNC_ENDPOINT, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({status: status}),
    });
    const body = await res.json().catch(() => ({}));

    if (res.status === 501) {
      setSyncStage('unconfigured', body.detail || 'Worker 未配置 GITHUB_TOKEN');
    } else if (res.status === 202 || res.ok) {
      // 只确认到「已提交」。真正写入与否由下次 fetchServerStatus 确认
      setSyncStage('dispatched', body.note || '事件已提交，等待 workflow 写入');
    } else {
      setSyncStage('failed', 'HTTP ' + res.status + ' ' + (body.error || ''));
    }
  } catch(e) {
    setSyncStage('failed', '网络错误: ' + e);
  }
  syncing = false;
}

function esc(s){const d=document.createElement('div');d.textContent=s||'';return d.innerHTML}
// 属性值专用：esc() 不转义引号，直接塞进 attr="..." 会被一个引号撑破。
// 这是 audit P0 说的「esc() 只适合 HTML 文本转义」的具体补丁。
function escAttr(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];})}
// 外链统一过白名单，挡住 javascript: / data: 和任意第三方域
var URL_HOSTS=[/^([a-z0-9-]+\.)*amazon\.co\.uk$/,/^([a-z0-9-]+\.)*media-amazon\.com$/,
  /^([a-z0-9-]+\.)*ssl-images-amazon\.com$/,/^([a-z0-9-]+\.)*1688\.com$/,
  /^trends\.google\.(com|co\.uk)$/,/^Baodan168\.github\.io$/];
function safeUrl(u){
  if(!u) return '';
  try{ var x=new URL(u,location.href);
    if(x.protocol!=='https:') return '';
    if(x.username||x.password) return '';
    var h=x.hostname.toLowerCase();
    return URL_HOSTS.some(function(re){return re.test(h)}) ? x.href : '';
  }catch(e){ return ''; }
}

let curDate = DATES[0] || '';
let curTab = 'discovery';

// ===== Date Picker (unified) =====
const picker = document.getElementById('datePicker');
const ALL_DATES = [...new Set([...DISC_DATES, ...RADAR_DATES])].sort().reverse();

function initDatePicker(dates, selectElem) {
  selectElem.innerHTML = '';
  dates.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d; opt.textContent = d;
    selectElem.appendChild(opt);
  });
}

initDatePicker(ALL_DATES, picker);
picker.addEventListener('change', () => { curDate = picker.value; renderAll(); });

// ===== Main Tabs =====
document.querySelector('.main-tabs').addEventListener('click', e => {
  const t = e.target.closest('.main-tab'); if (!t) return;
  document.querySelectorAll('.main-tab').forEach(b => { b.classList.remove('active'); b.style.background='var(--card)'; b.style.color='var(--muted)' });
  t.classList.add('active'); t.style.background='var(--tc)'; t.style.color='#fff';
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById('sec-'+t.dataset.tab).classList.add('active');
  
  // 切换Tab
  curTab = t.dataset.tab;
  
  if (t.dataset.tab === 'kanban') renderKanban();
  renderAll();
});
document.querySelector('.main-tab.active').style.background='var(--tc)';
document.querySelector('.main-tab.active').style.color='#fff';

// ===== Season Events =====
function renderSeasonEvents() {
  const bar = document.getElementById('seasonBar');
  if (!SEASON_EVENTS || !SEASON_EVENTS.length) { bar.innerHTML = ''; return; }
  bar.innerHTML = SEASON_EVENTS.map(ev => {
    const urgent = ev.days_until <= 30;
    const cats = (ev.recommended_categories || []).slice(0, 3).join(', ');
    return `<div class="event-chip ${urgent ? 'urgent' : ''}">
      <span class="ev-name">${esc(ev.event_name)}</span>
      <span class="ev-days">${ev.days_until}天</span>
      ${cats ? `<span class="ev-cats">${esc(cats)}</span>` : ''}
    </div>`;
  }).join('');
}

// ===== Render Discovery =====
function renderDiscovery() {
  const list = document.getElementById('insightList');
  const empty = document.getElementById('emptyDisc');
  const forecastArea = document.getElementById('forecastArea');
  const discData = DISC_ALL[curDate];
  const insights = discData ? discData.insights || [] : [];
  const forecast = discData ? discData.trend_forecast || '' : '';

  document.getElementById('discCnt').textContent = insights.length;

  renderSeasonEvents();

  if (!insights.length) { list.innerHTML=''; empty.style.display='block'; forecastArea.innerHTML=''; return; }
  empty.style.display='none';

  // Forecast
  forecastArea.innerHTML = forecast ? `<div class="forecast-card"><div class="forecast-title">🔮 未来趋势预测</div><div class="forecast-text">${esc(forecast)}</div></div>` : '';

  list.innerHTML = insights.map((ins, idx) => {
    const score = ins.trend_score || 0;
    const scoreCls = score >= 80 ? 'hot' : score >= 50 ? 'warm' : 'cool';
    const dir = ins.trend_direction === 'rising' ? '📈' : ins.trend_direction === 'falling' ? '📉' : '➡️';
    const signals = (ins.demand_signals || []).map(s => `<span class="signal-chip">${esc(s)}</span>`).join('');

    // Signal bars (trend/gap/profit)
    let signalBarsHtml = '';
    if (ins.signal_scores) {
      const ss = ins.signal_scores;
      const trendVal = ss.trend || ss.trend_score || 0;
      const gapVal = ss.gap || ss.gap_score || 0;
      const profitVal = ss.profit || ss.profit_score || 0;
      signalBarsHtml = `<div class="signal-bars">
        <div class="signal-bar-row"><span class="signal-bar-label">趋势</span><div class="signal-bar-track"><div class="signal-bar-fill trend" style="width:${Math.min(trendVal, 100)}%"></div></div><span class="signal-bar-val" style="color:#AF52DE">${trendVal}</span></div>
        <div class="signal-bar-row"><span class="signal-bar-label">缺口</span><div class="signal-bar-track"><div class="signal-bar-fill gap" style="width:${Math.min(gapVal, 100)}%"></div></div><span class="signal-bar-val" style="color:var(--blue)">${gapVal}</span></div>
        <div class="signal-bar-row"><span class="signal-bar-label">利润</span><div class="signal-bar-track"><div class="signal-bar-fill profit" style="width:${Math.min(profitVal, 100)}%"></div></div><span class="signal-bar-val" style="color:var(--green)">${profitVal}</span></div>
      </div>`;
    }

    // Amazon search URL
    const amzKw = ins.amazon_keyword || ins.keyword || '';
    const amzUrl = ins.amazon_search_url || `https://www.amazon.co.uk/s?k=${encodeURIComponent(amzKw)}&i=kitchen`;
    // 1688 search
    const aliKw = ins.search_1688 || ins.keyword_cn || ins.keyword || '';
    const aliUrl = ins.search_1688_url || `https://s.1688.com/selloffer/offer_search.htm?keywords=${encodeURIComponent(aliKw)}`;
    // Google Trends
    const gtUrl = `https://trends.google.com/trends/explore?geo=GB&q=${encodeURIComponent(amzKw)}`;

    // Competition summary
    const compHtml = ins.competition ? `<div class="comp-box"><div class="label">📊 竞争格局</div><div class="text">${esc(ins.competition)}</div></div>` : '';

    // Radar cross-validation: find matching radar products
        let radarHtml = '';
        const kwLower = (ins.keyword || '').toLowerCase();
        // Split on space, filter words >= 4 chars
        const kwParts = kwLower.split(' ').filter(w => w.length >= 4);
        if (kwParts.length >= 2 && typeof RADAR_ALL !== 'undefined' && curDate) {
          const radarData = RADAR_ALL[curDate];
          if (radarData && radarData.products) {
            const genericWords = ['reusable','portable','new','foldable','adjustable','lightweight','durable','easy','large','small','medium','extra','premium','universal','compact','strong','soft','perfect','great','super','best','high','quality','multi','value','piece','garden','plant','tray','brush','cleaning','cooling','cover','strap','seat','balls','label','pail','basket','organiser','drawer','bottle','hand'];
            const minMatches = Math.max(2, Math.ceil(kwParts.length * 0.75));
            const matched = radarData.products.filter(p => {
              const name = (p.name || '').toLowerCase();
              const hits = kwParts.filter(part => name.includes(part));
              if (hits.length < minMatches) return false;
              const distinct = hits.filter(h => !genericWords.includes(h));
              return distinct.length >= 1;
            });
            if (matched.length > 0) {
              radarHtml = `<div class="radar-match"><div class="label">📡 雷达验证（已找到${matched.length}个产品）</div>` +
                matched.map(p => {
                  const reviews = p.reviews || 0;
                  const ocean = reviews < 20 ? '🌊蓝海' : reviews <= 50 ? '🟢低竞争' : '🟡中等';
                  return `<div class="radar-product">✅ ${esc((p.name||'').substring(0,45))} — £${(p.price||0).toFixed(2)} | ${reviews}评论 ${ocean} | 利润率${((p.profit_margin||0)*100).toFixed(0)}%</div>`;
                }).join('') + `</div>`;
            }
          }
        }

    return `<div class="insight-card" data-idx="${idx}">
      <div class="insight-hd" data-act="toggle-insight">
        <div class="insight-score ${scoreCls}">${score}</div>
        <div class="insight-main">
          <div class="insight-kw">${dir} ${esc(ins.keyword)}</div>
          ${ins.keyword_cn ? `<div class="insight-kw-cn">${esc(ins.keyword_cn)}</div>` : ''}
          <div class="insight-signals">${signals}</div>
          ${signalBarsHtml}
        </div>
        <div class="insight-arrow">›</div>
      </div>
      <div class="insight-detail">
        <div class="detail-sec">
          <div class="detail-title">💡 选品理由</div>
          <div class="detail-text">${esc(ins.reason)}</div>
        </div>
        ${ins.action ? `<div class="action-box"><div class="label">📋 行动建议</div><div class="text">${esc(ins.action)}</div></div>` : ''}
        ${compHtml}
        ${radarHtml}
        <div class="search-btns">
          <a class="btn-search amazon" href="${safeUrl(amzUrl)}" target="_blank" rel="noopener noreferrer">🛒 Amazon UK 搜索「${esc(amzKw)}」</a>
          <a class="btn-search alibaba" href="${safeUrl(aliUrl)}" target="_blank" rel="noopener noreferrer">🏭 1688 搜索「${esc(aliKw)}」</a>
          <a class="btn-search google" href="${safeUrl(gtUrl)}" target="_blank" rel="noopener noreferrer">📊 Google Trends</a>
        </div>
      </div>
    </div>`;
  }).join('');
}

// ===== Render Radar =====
let radarStatus = 'all';
function renderRadar() {
  const grid = document.getElementById('radarGrid');
  const empty = document.getElementById('emptyRadar');
  const radarData = RADAR_ALL[curDate];
  const products = radarData ? radarData.products || [] : [];

  if (!products.length) { grid.innerHTML=''; empty.style.display='block'; return; }
  empty.style.display='none';

  const search = document.getElementById('radarSearch').value.toLowerCase();
  const mf = document.getElementById('fMargin').value;
  const sf = document.getElementById('fSort').value;
  const sts = getSt();

  let filtered = products.filter(p => {
    const st = sts[p.asin]||'pending';
    if (radarStatus==='all' && st==='rejected') return false;
    if (radarStatus==='all' && p.is_new===false) return false;
    if (radarStatus!=='all' && st!==radarStatus) return false;
    if (search && !p.name.toLowerCase().includes(search)) return false;
    if (mf!=='all') {if((p.profit_margin||0)<Number(mf)/100)return false}
    return true;
  });
  document.getElementById('radarCnt').textContent = filtered.length;

  filtered.sort((a,b)=>{
    if(sf==='score')return(b.score||0)-(a.score||0);
    if(sf==='margin')return(b.profit_margin||0)-(a.profit_margin||0);
    if(sf==='new'){const an=a.is_new?1:0,bn=b.is_new?1:0;if(an!==bn)return bn-an;return(b.score||0)-(a.score||0)}
    return 0;
  });

  grid.innerHTML = filtered.map(p => {
    const st=sts[p.asin]||'pending';
    const margin=((p.profit_margin||0)*100).toFixed(1);
    const mCls=margin>=30?'high':margin>=20?'mid':'low';
    const barC=margin>=30?'var(--green)':margin>=20?'var(--orange)':'var(--red)';
    const sc=p.score||0;
    const scCls=sc>=120?'hot':sc>=80?'high':sc>=40?'mid':'low';
    const badge=p.is_new?'<span class="badge-new">NEW</span>':(p.is_new===false?'<span class="badge-repeat">重复</span>':'')+(p.verify_status==='unverified'?'<span class="badge-warn">⚠️未验证</span>':'');
    const img=p.image_url?`<div class="pc-img"><img src="${safeUrl(p.image_url)}" alt="${esc(p.name)}" loading="lazy"/></div>`:'<div class="pc-img"><div class="ph">📦</div></div>';
    const url=p.amazon_url||(p.asin?`https://www.amazon.co.uk/dp/${p.asin}`:'#');
    const cb=p.cost_breakdown||{};
    const costH=cb.vat?`<button class="cost-tog" data-act="toggle-cost">💰 成本明细</button><div class="cost-det">VAT: £${cb.vat?.toFixed(2)||'-'} · 佣金: £${cb.commission?.toFixed(2)||'-'} · FBA: £${cb.fba?.toFixed(2)||'-'}<br>广告: £${cb.ads?.toFixed(2)||'-'} · 退货: £${cb.returns?.toFixed(2)||'-'} · 采购: £${cb.sourcing?.toFixed(2)||'-'}<br><b>总成本: £${cb.total_cost?.toFixed(2)||'-'} · 净利润: £${(p.net_profit||0).toFixed(2)}</b></div>`:'';
    const sigs=(p.sources||[]).filter(s=>typeof s==='string').map(s=>{let c='';if(s.includes('TikTok'))c='tiktok';if(s.includes('多源'))c='multi';return`<span class="sig ${escAttr(c)}">${s}</span>`}).join('');
    const sd=p.sd_label?`<span class="sig sd">${p.sd_label}</span>`:'';
    return `<div class="pc" data-status="${escAttr(st)}" data-asin="${escAttr(p.asin||'')}">
      ${badge}
      <div class="card-hd"><span class="src-badge">📡 雷达</span><div class="sig-badges">${sigs}${sd}</div><span class="score-badge ${escAttr(scCls)}">${sc}分</span></div>
      ${img}
      <div class="pc-name"><a href="${safeUrl(url)}" target="_blank" rel="noopener noreferrer">${esc(p.name)}</a></div>
      <div class="pc-meta"><span>💷 £${(p.price||0).toFixed(2)}</span><span>⭐ ${p.rating||'-'} (${p.reviews||0})</span>${p.first_seen?`<span>发现: ${p.first_seen}</span>`:''}</div>
      <div class="profit-bar-wrap"><div class="profit-bar-bg"><div class="profit-bar" style="width:${Math.min(margin,50)*2}%;background:${barC}"></div></div><span class="profit-txt ${mCls}">${margin}%</span></div>
      ${costH}
      <div class="status-btns">
        ${Object.entries(STATUS).map(([k,[l,c]])=>`<button class="st-btn ${st===k?'active':''}" style="--s-c:${c}" data-act="set-status" data-asin="${escAttr(p.asin)}" data-status="${escAttr(k)}">${l}</button>`).join('')}
        <a class="btn-amz" href="${safeUrl(url)}" target="_blank" rel="noopener noreferrer">🛒 Amazon</a>
      </div>
    </div>`;
  }).join('');
}

function setSt(asin,s,btn){
  saveSt(asin,s);
  const c=btn.closest('.pc');
  if(c){c.dataset.status=s;c.querySelectorAll('.st-btn').forEach(b=>b.classList.remove('active'));}
  btn.classList.add('active');
}

document.querySelector('.st-filter').addEventListener('click',e=>{const t=e.target.closest('.st-tab');if(!t)return;document.querySelectorAll('.st-tab').forEach(b=>b.classList.remove('active'));t.classList.add('active');radarStatus=t.dataset.status;renderRadar()});
['radarSearch','fMargin','fSort'].forEach(id=>{document.getElementById(id).addEventListener(id==='radarSearch'?'input':'change',renderRadar)});

function exportCSV(){
  const radarData=RADAR_ALL[curDate];if(!radarData)return;
  const sts=getSt();const rows=[['来源','ASIN','名称','价格','利润率','评分','状态','链接']];
  (radarData.products||[]).forEach(p=>{const s=sts[p.asin]||'pending';rows.push(['雷达',p.asin||'',p.name||'',(p.price||0).toFixed(2),((p.profit_margin||0)*100).toFixed(1)+'%',p.score||0,STATUS[s]?.[0]||s,p.amazon_url||''])});
  const csv=rows.map(r=>r.map(c=>'"'+String(c).replace(/"/g,'""')+'"').join(',')).join('\\n');
  const b=new Blob(['\\ufeff'+csv],{type:'text/csv;charset=utf-8;'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='选品平台_'+curDate+'.csv';a.click();
}

// ===== Kanban Board (V5.3 — Decision Inbox) =====
function renderKanban() {
  const metricsRow = document.getElementById('metricsRow');
  const board = document.getElementById('kanbanBoard');
  const sts = getSt();

  // --- Collect items from 3 sources ---
  const inbox = [];
  const now = new Date();
  const today = now.toISOString().slice(0,10);
  // Phase 2.4: 注入开关（前端可暂停）
  const _doInject = INJECT_CFG.enabled !== false && localStorage.getItem('kanban_pause_inject') !== '1';

  // Source 1: Festival Planner (highest priority — has deadlines)
  if (_doInject && typeof FESTIVALS !== 'undefined') {
    const eventCounts = {}; // limit per event
    FESTIVALS.forEach(f => {
      const fDate = new Date(f.date);
      if (fDate < now) return;
      const seaDeadline = new Date(fDate);
      seaDeadline.setDate(seaDeadline.getDate() - INJECT_CFG.festival.sea_deadline_days);
      const daysLeft = Math.ceil((seaDeadline - now) / 86400000);
      if (daysLeft > INJECT_CFG.festival.days_ahead || daysLeft < -10) return;
      eventCounts[f.id] = 0;

      (f.products || []).forEach(p => {
        if (eventCounts[f.id] >= INJECT_CFG.festival.max_per_event) return;
        const kw = (p.keywords || [])[0] || p.sku || '';
        if (!kw) return;
        const kbKey = 'kb_fest_' + f.id + '_' + kw.replace(/\\s+/g,'_').slice(0,20);
        if (sts[kbKey] === 'starred' || sts[kbKey] === 'verified' || sts[kbKey] === 'dismissed') return;

        eventCounts[f.id]++;
        inbox.push({
          id: kbKey,
          name: kw,
          nameCn: p.sku || '',
          source: 'festival',
          festivalId: f.id || '',
          score: p.matchScore ? p.matchScore * 20 : 50,
          profit: p.margin || '',
          deadline: f.date,
          deadlineLabel: f.icon + ' ' + f.name,
          daysLeft: daysLeft,
          eventName: f.name,
          eventIcon: f.icon || '📅',
          amazonKw: kw,
          aliUrl: p.aliUrl || '',
          sortWeight: daysLeft <= 7 ? 1000 : daysLeft <= 14 ? 500 : 100,
        });
      });
    });
  }

  // Source 2: Discovery keywords
  let discCount = 0;
  if (_doInject) Object.entries(DISC_ALL || {}).forEach(([date, dd]) => {
    (dd.insights || []).forEach(ins => {
      if (discCount >= INJECT_CFG.discovery.max_keywords) return;
      const kw = ins.keyword || '';
      if (!kw) return;
      const kbKey = 'kb_disc_' + kw.replace(/\\s+/g,'_').slice(0,30) + '_' + date;
      if (sts[kbKey] === 'starred' || sts[kbKey] === 'verified' || sts[kbKey] === 'dismissed') return;

      discCount++;
      const ss = ins.signal_scores || {};
      const aliKw = ins.search_1688 || '';
      inbox.push({
        id: kbKey,
        name: ins.amazon_keyword || kw,
        nameCn: ins.keyword_cn || '',
        source: 'discovery',
        score: ss.final || ins.trend_score || 0,
        profit: ss.profit_window || '',
        gapLevel: ss.gap_level || '',
        amazonKw: ins.amazon_keyword || kw,
        aliKw: aliKw,
        aliUrl: ins.search_1688_url || '',
        date: date,
        sortWeight: (ss.final || 0) + 50,
      });
    });
  });

  // Source 3: Radar products (only new)
  let radarCount = 0;
  if (_doInject) Object.entries(RADAR_ALL || {}).forEach(([date, rd]) => {
    (rd.products || []).forEach(p => {
      if (radarCount >= INJECT_CFG.radar.max_products) return;
      if (!p.asin || (INJECT_CFG.radar.new_only && p.is_new === false)) return;
      const kbKey = 'kb_radar_' + p.asin;
      if (sts[kbKey] === 'starred' || sts[kbKey] === 'verified' || sts[kbKey] === 'dismissed') return;

      radarCount++;
      inbox.push({
        id: kbKey,
        name: p.name || '',
        nameCn: '',
        source: 'radar',
        asin: p.asin,
        score: p.score || 0,
        profit: p.profit_margin ? (p.profit_margin * 100).toFixed(0) + '%' : '',
        amazonKw: '',
        amazonUrl: p.amazon_url || 'https://www.amazon.co.uk/dp/' + p.asin,
        aliKw: '',
        aliUrl: '',
        date: date,
        sortWeight: p.score || 0,
      });
    });
  });

  // --- Build starred and verified lists ---
  const starred = [];
  const verified = [];
  Object.entries(sts).forEach(([key, status]) => {
    if (!key.startsWith('kb_')) return;
    const item = inbox.find(i => i.id === key);
    if (status === 'starred') {
      if (item) starred.push(item);
      else starred.push({id: key, name: key.replace(/kb_[^_]+_/,'').replace(/_/g,' '), source: 'unknown', score: 0, sortWeight: 0, amazonKw:'', aliUrl:''});
    }
    if (status === 'verified') {
      if (item) verified.push(item);
      else verified.push({id: key, name: key.replace(/kb_[^_]+_/,'').replace(/_/g,' '), source: 'unknown', score: 0, sortWeight: 0, amazonKw:'', aliUrl:''});
    }
  });

  inbox.sort((a, b) => b.sortWeight - a.sortWeight);

  // --- Metrics ---
  const urgentCount = inbox.filter(i => i.source === 'festival' && i.daysLeft <= 7).length;
  const nearestDeadline = inbox.filter(i => i.deadline).sort((a,b) => a.daysLeft - b.daysLeft)[0];
  metricsRow.innerHTML = [
    {n: inbox.length, l: '📥 收件箱'},
    {n: starred.length, l: '⭐ 值得做'},
    {n: verified.length, l: '✅ 已验证'},
    {n: urgentCount, l: '🔴 紧急(≤7天)', cls: urgentCount > 0 ? 'urgent' : ''},
    {n: nearestDeadline ? nearestDeadline.eventIcon + ' ' + nearestDeadline.eventName + ' ' + nearestDeadline.daysLeft + '天' : '—', l: '📅 最近截止'},
  ].map(item => `<div class="metric-card ${item.cls||''}"><div class="big">${item.n}</div><div class="label">${item.l}</div></div>`).join('');

  // --- Unified card renderer ---
  function renderCard(item, colKey) {
    const srcCls = item.source || 'radar';
    const srcLabel = {festival:'📅 节日', discovery:'🔍 发现', radar:'📡 雷达'}[srcCls] || '📡 其他';

    let deadlineHtml = '';
    if (item.daysLeft !== undefined) {
      const dlCls = item.daysLeft <= 7 ? '' : 'ok';
      deadlineHtml = `<span class="kc-deadline ${dlCls}">${item.eventIcon||'📅'} ${item.daysLeft}天</span>`;
    }

    let metricsHtml = '';
    if (item.score) metricsHtml += `<span class="kc-tag score">${item.score}分</span>`;
    if (item.profit) metricsHtml += `<span class="kc-tag profit">${item.profit}</span>`;
    if (item.gapLevel) metricsHtml += `<span class="kc-tag gap">${item.gapLevel}</span>`;

    // URLs
    const amazonUrl = item.amazonUrl || (item.amazonKw ? 'https://www.amazon.co.uk/s?k=' + encodeURIComponent(item.amazonKw) : '');
    const aliUrl = item.aliUrl || '';

    // Action buttons (different per column)
    let actionsHtml = '';
    if (amazonUrl) actionsHtml += `<a class="kc-btn" href="${safeUrl(amazonUrl)}" target="_blank" rel="noopener noreferrer">🛒 Amazon</a>`;
    if (aliUrl) actionsHtml += `<a class="kc-btn" href="${safeUrl(aliUrl)}" target="_blank" rel="noopener noreferrer">🏭 1688</a>`;
    if (item.source === 'festival' && item.festivalId) actionsHtml += `<button class="kc-btn" data-act="goto-festival" data-festival-id="${escAttr(item.festivalId)}">📅 查看节日</button>`;

    if (colKey === 'inbox') {
      actionsHtml += `<button class="kc-btn primary" data-act="kanban" data-kanban-id="${escAttr(item.id)}" data-kanban-to="starred">⭐ 值得做</button>`;
      actionsHtml += `<button class="kc-btn danger" data-act="kanban" data-kanban-id="${escAttr(item.id)}" data-kanban-to="dismiss">✕</button>`;
    } else if (colKey === 'starred') {
      actionsHtml += `<button class="kc-btn primary" data-act="kanban" data-kanban-id="${escAttr(item.id)}" data-kanban-to="verified">✅ 待验证</button>`;
      actionsHtml += `<button class="kc-btn danger" data-act="kanban" data-kanban-id="${escAttr(item.id)}" data-kanban-to="dismiss">✕</button>`;
    } else { // verified
      actionsHtml += `<button class="kc-btn danger" data-act="kanban" data-kanban-id="${escAttr(item.id)}" data-kanban-to="dismiss">✕</button>`;
    }

    return `<div class="kanban-card src-${srcCls}" data-id="${item.id}">
      <div class="kc-top">
        <span class="kc-src ${srcCls}">${srcLabel}</span>
        ${deadlineHtml}
      </div>
      <div class="kc-name" title="${esc(item.name)}">${esc(item.name)}</div>
      ${item.nameCn ? `<div class="kc-cn">${esc(item.nameCn)}</div>` : ''}
      ${metricsHtml ? `<div class="kc-metrics">${metricsHtml}</div>` : ''}
      <div class="kc-actions">${actionsHtml}</div>
    </div>`;
  }

  // --- Build board ---
  const columns = [
    {key:'inbox', label:'📥 收件箱', color:'#007AFF', items:inbox, empty:'三源自动注入，每天更新'},
    {key:'starred', label:'⭐ 值得做', color:'#FF9500', items:starred, empty:'点击卡片的"⭐ 值得做"按钮'},
    {key:'verified', label:'✅ 已验证', color:'#34C759', items:verified, empty:'团队确认可做后标记'},
  ];

  board.innerHTML = columns.map(col => {
    const cardsHtml = col.items.length > 0
      ? col.items.map(item => renderCard(item, col.key)).join('')
      : `<div class="kanban-empty">${col.empty}</div>`;
    return `<div class="kanban-col" data-status="${escAttr(col.key)}">
      <div class="kanban-col-hd"><span class="dot" style="background:${col.color}"></span>${col.label}<span class="cnt">${col.items.length}</span></div>
      <div class="kanban-cards">${cardsHtml}</div>
    </div>`;
  }).join('');
}

function moveKanban(id, target) {
  const sts = getSt();
  if (target === 'dismiss') {
    sts[id] = 'dismissed';
  } else {
    sts[id] = target;
  }
  saveSt(null, null, sts);
  renderKanban();
}

document.getElementById('kanbanSearch')?.addEventListener('input', renderKanban);

// Phase 2.4: 暂停/恢复看板注入
function toggleInject() {
  var paused = localStorage.getItem('kanban_pause_inject') === '1';
  if (paused) { localStorage.removeItem('kanban_pause_inject'); }
  else { localStorage.setItem('kanban_pause_inject', '1'); }
  var btn = document.getElementById('pauseInjectBtn');
  if (btn) btn.textContent = paused ? '⏸️ 暂停注入' : '▶️ 恢复注入';
  renderKanban();
}
// 初始化按钮状态
(function(){var p=localStorage.getItem('kanban_pause_inject')==='1';var b=document.getElementById('pauseInjectBtn');if(b)b.textContent=p?'▶️ 恢复注入':'⏸️ 暂停注入';})();

function exportKanbanCSV(){
  const sts = getSt();
  const rows = [['状态','关键词','来源','评分','日期']];
  // Export inbox items
  Object.entries(DISC_ALL).forEach(([date, dd]) => {
    (dd.insights || []).forEach(ins => {
      const kbKey = 'kb_disc_' + (ins.keyword||'').replace(/\\s+/g,'_').slice(0,30) + '_' + date;
      rows.push([sts[kbKey]||'inbox', ins.keyword||'', 'discovery', ins.trend_score||0, date]);
    });
  });
  Object.entries(RADAR_ALL).forEach(([date, rd]) => {
    (rd.products || []).forEach(p => {
      const kbKey = 'kb_radar_' + (p.asin||'');
      rows.push([sts[kbKey]||'inbox', p.name||'', 'radar', p.score||0, date]);
    });
  });
  const csv = rows.map(r => r.map(c => '"'+String(c).replace(/"/g,'""')+'"').join(',')).join('\\n');
  const blob = new Blob(['\\uFEFF'+csv], {type:'text/csv;charset=utf-8'});
  const a = document.createElement('a');a.href=URL.createObjectURL(blob);a.download='kanban_'+new Date().toISOString().slice(0,10)+'.csv';a.click();
}

// ===== Global Search =====
function toggleSearch() {
  const overlay = document.getElementById('searchOverlay');
  const input = document.getElementById('globalSearchInput');
  if (overlay.classList.contains('open')) {
    overlay.classList.remove('open');
  } else {
    overlay.classList.add('open');
    setTimeout(() => input.focus(), 100);
    globalSearch('');
  }
}

document.getElementById('searchOverlay').addEventListener('click', e => {
  if (e.target === e.currentTarget) toggleSearch();
});

document.getElementById('globalSearchInput').addEventListener('input', e => {
  globalSearch(e.target.value);
});

function globalSearch(query) {
  const resultsEl = document.getElementById('searchResults');
  const q = (query || '').toLowerCase().trim();
  if (!q) {
    resultsEl.innerHTML = `<div class="search-empty">输入关键词开始搜索（共 ${SEARCH_INDEX.length} 条记录）</div>`;
    return;
  }
  const matches = SEARCH_INDEX.filter(e =>
    (e.keyword || '').toLowerCase().includes(q) ||
    (e.keyword_cn || '').toLowerCase().includes(q) ||
    (e.category || '').toLowerCase().includes(q) ||
    (e.reason || '').toLowerCase().includes(q)
  ).slice(0, 50);

  if (!matches.length) {
    resultsEl.innerHTML = `<div class="search-empty">没有找到匹配「${esc(query)}」的结果</div>`;
    return;
  }
  resultsEl.innerHTML = matches.map(e => {
    const typeLabel = e.type === 'discovery' ? '趋势' : '雷达';
    const typeCls = e.type === 'discovery' ? 'discovery' : 'radar';
    return `<div class="search-result" data-act="search-nav" data-nav-type="${escAttr(e.type)}" data-nav-date="${escAttr(e.date)}">
      <span class="sr-type ${typeCls}">${typeLabel}</span>
      <span class="sr-kw">${esc(e.keyword)}</span>
      <span class="sr-score">${e.score || 0}分</span>
      <span class="sr-date">${e.date}</span>
    </div>`;
  }).join('');
}

function searchNavigate(type, date) {
  toggleSearch();
  // Switch to the right tab
  const tabBtn = document.querySelector(`.main-tab[data-tab="${type === 'discovery' ? 'discovery' : 'radar'}"]`);
  if (tabBtn) {
    document.querySelectorAll('.main-tab').forEach(b => { b.classList.remove('active'); b.style.background='var(--card)'; b.style.color='var(--muted)' });
    tabBtn.classList.add('active'); tabBtn.style.background='var(--tc)'; tabBtn.style.color='#fff';
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById('sec-'+tabBtn.dataset.tab).classList.add('active');
  }
  // Switch date
  if (date && DATES.includes(date)) {
    curDate = date;
    picker.value = date;
    renderAll();
  }
}

// 从看板卡片跳回节日 Tab 里对应的详情卡片
function goToFestival(festivalId) {
  const tabBtn = document.querySelector('.main-tab[data-tab="festival"]');
  if (tabBtn) {
    document.querySelectorAll('.main-tab').forEach(b => { b.classList.remove('active'); b.style.background='var(--card)'; b.style.color='var(--muted)' });
    tabBtn.classList.add('active'); tabBtn.style.background='var(--tc)'; tabBtn.style.color='#fff';
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById('sec-festival').classList.add('active');
    curTab = 'festival';
  }
  const card = document.getElementById('festival-' + festivalId);
  if (card) {
    card.classList.add('expanded');
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// Keyboard shortcut: Ctrl+K / Cmd+K
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    toggleSearch();
  }
  if (e.key === 'Escape') {
    const overlay = document.getElementById('searchOverlay');
    if (overlay.classList.contains('open')) toggleSearch();
  }
});

function renderAll() {
  // Update stats
  const r = RADAR_ALL[curDate];
  const d = DISC_ALL[curDate];
  const rCnt = r ? (r.products||[]).length : 0;
  const dCnt = d ? (d.insights||[]).length : 0;
  const rTime = r ? r.scan_time : '';
  const dTime = d ? d.scan_time : '';
  let stats = [];
  if (dCnt) stats.push(`趋势发现 ${dCnt}个关键词 ${dTime}`);
  if (rCnt) stats.push(`雷达扫描 ${rCnt}个产品 ${rTime}`);
  document.getElementById('dateStats').textContent = stats.join(' · ') || '无数据';

  renderDiscovery();
  renderRadar();
}

renderAll();

// Phase 3 Step 4: postMessage 高度自适应 — 响应父窗口请求 + 主动发送
function oaSendHeight() {
    var h = Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.scrollHeight);
    if (window.parent && window.parent !== window) {
        window.parent.postMessage({type: 'oa-set-height', height: h}, '*');
    }
}
window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'oa-get-height') oaSendHeight();
});
oaSendHeight();
setTimeout(oaSendHeight, 500);
setTimeout(oaSendHeight, 2000);

/* ════════════════════════════════════════════
   事件委托
   原来这些是内联 onclick，产品 ASIN / 看板 id 等外部数据会被直接拼进
   onclick 的 JS 字符串里 —— 数据里一个单引号就能跳出字符串执行代码。
   改成 data-* 传值 + 委托后，这些值只经过属性转义，永远不进 JS 语法。
   ════════════════════════════════════════════ */

document.addEventListener('click', function (e) {
  var el = e.target.closest('[data-act]');
  if (!el) return;

  switch (el.dataset.act) {
    case 'toggle-insight':
      el.parentElement.classList.toggle('open');
      break;

    case 'toggle-cost':
      if (el.nextElementSibling) el.nextElementSibling.classList.toggle('show');
      break;

    case 'set-status':
      setSt(el.dataset.asin, el.dataset.status, el);
      break;

    case 'kanban':
      e.stopPropagation();
      moveKanban(el.dataset.kanbanId, el.dataset.kanbanTo);
      break;

    case 'goto-festival':
      e.stopPropagation();
      goToFestival(el.dataset.festivalId);
      break;

    case 'search-nav':
      searchNavigate(el.dataset.navType, el.dataset.navDate);
      break;

    case 'export-csv':
      exportCSV();
      break;

    case 'export-kanban':
      exportKanbanCSV();
      break;

    case 'toggle-inject':
      toggleInject();
      break;

    case 'toggle-search':
      toggleSearch();
      break;
  }
});

/* 向门户上报页面高度，让 iframe 自适应。
   收发两端都校验 origin/source，不用 '*'（audit P2）。 */
(function () {
  window.addEventListener('message', function (e) {
    if (e.origin !== window.location.origin) return;
    if (e.source !== window.parent) return;
    var d = e.data;
    if (!d || typeof d !== 'object') return;
    if (d.type === 'oa-get-height') {
      var h = document.documentElement.scrollHeight;
      if (isFinite(h) && h > 0) {
        window.parent.postMessage({ type: 'oa-set-height', height: h }, e.origin);
      }
    }
  });
})();

})();
