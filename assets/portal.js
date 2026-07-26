/* ════════════════════════════════════════════
   OA 门户壳 v4.0
   配套 templates/portal.html，由 generate_portal.py 装配

   相比 v3 修掉的：
   - iframe 的 error 事件识别不了 HTTP 404/500（audit P2），
     改成探针 + 超时 + 四态区分
   - postMessage 用 '*' 且收发两端都不校验（audit P2）
   - 内联 onclick，改 addEventListener
   - 只靠 localStorage 记忆当前板块，链接不可分享，
     改 hash 路由
   ════════════════════════════════════════════ */
(function () {
  'use strict';

  var CFG = window.OA_PORTAL || {};
  var MODULES = CFG.modules || [];
  var SITE_ORIGIN = CFG.siteOrigin || window.location.origin;
  var DASHBOARD_KEY = CFG.dashboardKey || 'dashboard';

  /* iframe 加载超时。跨境雷达是外部仓库的 Pages，慢的时候几秒是正常的，
     8s 是「还没白到该报错」和「用户已经在怀疑是不是挂了」之间的折中。 */
  var LOAD_TIMEOUT_MS = 8000;
  /* 子页面上报的高度上限。没有上限的话，一个坏值就能把 iframe
     撑到几十万像素，浏览器直接卡死。 */
  var MAX_FRAME_HEIGHT = 20000;

  var el = {
    sidebar: document.getElementById('sidebar'),
    overlay: document.getElementById('sidebar-overlay'),
    menuBtn: document.getElementById('menuBtn'),
    nav: document.getElementById('nav'),
    frame: document.getElementById('content-frame'),
    dashboard: document.getElementById('dashboard'),
    loading: document.getElementById('loading'),
    error: document.getElementById('frameError'),
    feIcon: document.getElementById('feIcon'),
    feTitle: document.getElementById('feTitle'),
    feDesc: document.getElementById('feDesc'),
    feDetail: document.getElementById('feDetail'),
    feRetry: document.getElementById('feRetry'),
    feOpen: document.getElementById('feOpen'),
    title: document.getElementById('current-module'),
    update: document.getElementById('last-update'),
    clock: document.getElementById('clock'),
    statusDot: document.getElementById('statusDot'),
    themeToggle: document.getElementById('themeToggle')
  };

  var byKey = {};
  MODULES.forEach(function (m) { byKey[m.key] = m; });

  var currentKey = null;
  var loadTimer = null;
  var showTimer = null;
  var loadToken = 0;   // 防竞态：快速切换时，晚回来的旧请求不许改 UI

  /* ── 主题 ───────────────────────────────── */

  function currentTheme() {
    var explicit = document.documentElement.getAttribute('data-oa-theme');
    if (explicit) return explicit;
    return window.matchMedia &&
           window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-oa-theme', theme);
    try { localStorage.setItem('oa_theme', theme); } catch (e) {}
    broadcastTheme(theme);
  }

  /* 同源子页面通过 postMessage 跟随主题。
     跨域的跨境雷达收不到（也读不到我们的 localStorage），
     只能在 URL 上带 ?theme=，对方仓库不实现就无效——
     这是同源策略的硬限制，记在 DESIGN-DECISIONS 已知限制里。 */
  function broadcastTheme(theme) {
    var mod = byKey[currentKey];
    if (!mod || mod.inline || mod.cross_origin) return;
    try {
      el.frame.contentWindow.postMessage(
        { type: 'oa-set-theme', theme: theme }, window.location.origin);
    } catch (e) {}
  }

  if (el.themeToggle) {
    el.themeToggle.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  }

  /* ── 侧栏（移动端抽屉）─────────────────── */

  function setSidebar(open) {
    el.sidebar.classList.toggle('open', open);
    el.overlay.classList.toggle('show', open);
    if (el.menuBtn) el.menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  if (el.menuBtn) {
    el.menuBtn.addEventListener('click', function () {
      setSidebar(!el.sidebar.classList.contains('open'));
    });
  }
  el.overlay.addEventListener('click', function () { setSidebar(false); });

  /* ── 加载状态 ───────────────────────────── */

  function clearTimers() {
    clearTimeout(loadTimer);
    clearTimeout(showTimer);
  }

  function showLoading() {
    el.error.classList.remove('show');
    // 延迟 150ms 再显示，避免快速加载时闪一下
    showTimer = setTimeout(function () { el.loading.classList.add('show'); }, 150);
  }

  function hideLoading() {
    clearTimeout(showTimer);
    el.loading.classList.remove('show');
  }

  /**
   * 四种加载结果，每种都有自己的 UI。
   * 关键点：绝不把「iframe 触发了 load」直接当成功——
   * 服务器返回 404/500 页面时浏览器照样触发 load，
   * v3 就是因此把空白页显示成「已加载」。
   */
  var FAILURES = {
    'http-error': {
      icon: '🚫',
      title: '板块返回错误',
      desc: '服务器有响应，但返回的不是正常页面。可能是文件还没部署，或者路径变了。'
    },
    'network-error': {
      icon: '📡',
      title: '连不上板块',
      desc: '网络请求失败。可能是断网，或者该板块的站点当前不可达。'
    },
    'timeout': {
      icon: '⏱️',
      title: '板块加载超时',
      desc: '超过 ' + (LOAD_TIMEOUT_MS / 1000) + ' 秒没有加载完成。远端可能很慢或已经挂了。'
    }
  };

  function showError(kind, detail, mod) {
    hideLoading();
    var info = FAILURES[kind] || FAILURES['network-error'];
    el.feIcon.textContent = info.icon;
    el.feTitle.textContent = info.title;
    el.feDesc.textContent = info.desc;
    el.feDetail.textContent = detail || '';
    el.feOpen.href = mod ? mod.url : '#';
    el.error.classList.add('show');
    el.frame.hidden = true;
    setStatusDot('error');
    el.update.textContent = '加载失败';
  }

  function setStatusDot(state) {
    if (!el.statusDot) return;
    el.statusDot.style.background =
      state === 'error' ? 'var(--oa-status-error)' :
      state === 'warn' ? 'var(--oa-status-warn)' :
      state === 'unknown' ? 'var(--oa-status-unknown)' :
      'var(--oa-status-ok)';
  }

  /**
   * 加载前先探一次，拿到 iframe 本身给不了的信息（HTTP 状态码）。
   *
   * 同源：能读到真实状态码，404/500 直接报错，不用等 iframe 白屏。
   * 跨域：只能 no-cors，响应是 opaque —— 读不到状态码，只能区分
   *       「请求发出去了」和「网络层就失败了」。所以跨域板块的健康度
   *       最多只能是「未知」，这一点如实显示，不伪装成正常。
   */
  function probe(mod) {
    var target = mod.probe || mod.url;
    if (mod.cross_origin) {
      return fetch(target, { method: 'GET', mode: 'no-cors', cache: 'no-store' })
        .then(function () { return { ok: true, status: null, opaque: true }; })
        .catch(function (e) { return { ok: false, status: null, error: String(e) }; });
    }
    return fetch(target, { method: 'HEAD', cache: 'no-store' })
      .then(function (r) { return { ok: r.ok, status: r.status }; })
      .catch(function (e) { return { ok: false, status: null, error: String(e) }; });
  }

  /* ── 路由 ───────────────────────────────── */

  function switchModule(key, opts) {
    var mod = byKey[key];
    if (!mod) return false;
    opts = opts || {};

    clearTimers();
    loadToken += 1;
    var token = loadToken;
    currentKey = key;

    if (window.innerWidth <= 768) setSidebar(false);

    document.querySelectorAll('.oa-nav-item').forEach(function (a) {
      var active = a.dataset.key === key;
      a.classList.toggle('active', active);
      if (active) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });

    el.title.textContent = mod.label;
    document.title = mod.label + ' · ' + (CFG.systemName || 'OA');
    try { localStorage.setItem('oa_module', key); } catch (e) {}
    if (!opts.fromHash) {
      var hash = '#/' + key;
      if (window.location.hash !== hash) window.location.hash = hash;
    }

    // 今日概览：同源直渲染，没有加载过程
    if (mod.inline) {
      el.error.classList.remove('show');
      hideLoading();
      el.frame.hidden = true;
      el.frame.removeAttribute('src');
      el.dashboard.hidden = false;
      setStatusDot('ok');
      el.update.textContent = CFG.builtAt ? ('生成于 ' + CFG.builtAt) : '';
      return false;
    }

    el.dashboard.hidden = true;
    el.error.classList.remove('show');
    showLoading();
    setStatusDot('warn');

    probe(mod).then(function (res) {
      if (token !== loadToken) return;   // 用户已经切走了
      if (!res.ok) {
        showError(res.status ? 'http-error' : 'network-error',
                  res.status ? ('HTTP ' + res.status + ' · ' + (mod.probe || mod.url))
                             : (res.error || mod.url),
                  mod);
        return;
      }
      if (res.status && res.status >= 400) {
        showError('http-error', 'HTTP ' + res.status + ' · ' + (mod.probe || mod.url), mod);
        return;
      }
      loadFrame(mod, token);
    });

    return false;
  }

  function loadFrame(mod, token) {
    el.frame.hidden = false;
    var src = mod.url;
    // 跨域板块塞一个主题参数，对方实现了就跟随，没实现也无害
    if (mod.cross_origin) {
      src += (src.indexOf('?') === -1 ? '?' : '&') + 'theme=' + currentTheme();
    }
    el.frame.src = src;

    loadTimer = setTimeout(function () {
      if (token !== loadToken) return;
      showError('timeout', mod.url, mod);
    }, LOAD_TIMEOUT_MS);
  }

  el.frame.addEventListener('load', function () {
    clearTimeout(loadTimer);
    var mod = byKey[currentKey];
    if (!mod || mod.inline) return;

    /* 同源时再确认一次：iframe 里到底有没有渲染出东西。
       探针过了但页面是空的（比如 JS 报错炸了），这里能兜住。 */
    if (!mod.cross_origin) {
      try {
        var doc = el.frame.contentDocument;
        if (doc && doc.body && doc.body.children.length === 0) {
          showError('http-error', '页面加载完成但内容为空 · ' + mod.url, mod);
          return;
        }
      } catch (e) { /* 读不到就算了，不是错误 */ }
    }

    hideLoading();
    el.error.classList.remove('show');
    // 跨域拿不到内部状态，如实标「未知」而不是绿灯
    setStatusDot(mod.cross_origin ? 'unknown' : 'ok');
    el.update.textContent = '已加载 ' + new Date().toLocaleTimeString('zh-CN',
      { hour: '2-digit', minute: '2-digit' });
    broadcastTheme(currentTheme());
    if (!mod.cross_origin) {
      try {
        el.frame.contentWindow.postMessage(
          { type: 'oa-get-height' }, window.location.origin);
      } catch (e) {}
    }
  });

  el.frame.addEventListener('error', function () {
    clearTimeout(loadTimer);
    var mod = byKey[currentKey];
    showError('network-error', mod ? mod.url : '', mod);
  });

  el.feRetry.addEventListener('click', function () {
    if (currentKey) switchModule(currentKey, { fromHash: true });
  });

  /* ── 子页面消息 ─────────────────────────
     audit P2：原来发送用 '*'，接收端不校验 origin、source、
     类型和数值范围。任意页面都能伪造高度消息。
     现在四层都校验，任何一层不过直接丢弃。 */
  window.addEventListener('message', function (e) {
    if (e.origin !== window.location.origin && e.origin !== SITE_ORIGIN) return;
    if (e.source !== el.frame.contentWindow) return;
    var data = e.data;
    if (!data || typeof data !== 'object') return;
    if (data.type !== 'oa-set-height') return;
    var h = data.height;
    if (typeof h !== 'number' || !isFinite(h) || h <= 100 || h > MAX_FRAME_HEIGHT) return;
    el.frame.style.height = h + 'px';
  });

  /* ── 导航绑定 ───────────────────────────── */

  el.nav.addEventListener('click', function (e) {
    var link = e.target.closest('.oa-nav-item');
    if (!link) return;
    e.preventDefault();
    switchModule(link.dataset.key);
  });

  window.addEventListener('hashchange', function () {
    var key = (window.location.hash || '').replace(/^#\/?/, '');
    if (key && byKey[key] && key !== currentKey) {
      switchModule(key, { fromHash: true });
    }
  });

  /* ── 键盘 ───────────────────────────────── */

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && el.sidebar.classList.contains('open')) {
      setSidebar(false);
      return;
    }
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    // 输入框里的方向键不该翻板块
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;

    var items = Array.prototype.slice.call(document.querySelectorAll('.oa-nav-item'));
    var idx = items.findIndex(function (a) { return a.classList.contains('active'); });
    var next = e.key === 'ArrowDown' ? idx + 1 : idx - 1;
    if (next < 0 || next >= items.length) return;
    e.preventDefault();
    items[next].focus();
    switchModule(items[next].dataset.key);
  });

  /* ── 时钟 ───────────────────────────────── */

  function pad(n) { return String(n).padStart(2, '0'); }
  function tick() {
    var d = new Date();
    el.clock.textContent = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' +
      pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) +
      ':' + pad(d.getSeconds());
  }
  tick();
  setInterval(tick, 1000);

  /* ── 启动 ───────────────────────────────
     优先级：URL hash > 上次访问 > 今日概览。
     hash 排第一，这样分享出去的链接落在对的板块上。 */

  function initialKey() {
    var fromHash = (window.location.hash || '').replace(/^#\/?/, '');
    if (fromHash && byKey[fromHash]) return fromHash;
    try {
      var saved = localStorage.getItem('oa_module');
      if (saved && byKey[saved]) return saved;
    } catch (e) {}
    return byKey[DASHBOARD_KEY] ? DASHBOARD_KEY : (MODULES[0] && MODULES[0].key);
  }

  var start = initialKey();
  if (start) switchModule(start, { fromHash: true });
})();
