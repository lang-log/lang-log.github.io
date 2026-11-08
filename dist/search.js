'use strict';
// The search results page of Lang Log, at <site>/q=<terms> (owner, 2026-11-07),
// such as https://lang-log.github.io/q=mxi. Browsers can save it as a search
// engine with %s in place of the terms (dist/opensearch.xml says the same).
//
// GitHub Pages has no file at that address, so it serves dist/404.html; this
// script turns that page into the list of results: a search box at the top and
// every matching record below it, one per row, each linking to its own page.
// Searching again from the box changes the address to the new /q=<terms>.
// The top page sends its search box and old ?q= links here (dist/home.js).
//
// Ranking: exact name, ISO code or Glottocode; then names that start with the
// query; then a word in the name that starts with it; then any other match.
// Languages come before families and dialects (the order only; no record is
// labelled by its kind, .claude/rules/interface-text.md).
(() => {
  const where = () => location.pathname.match(/^(.*\/)q=([^/]*)$/);
  const m = where(),
    page = document.getElementById('search-page');
  if (!m || !page) return;
  // Site root: '/' on the live site, '/preview/pr-<n>/' in a pull request preview.
  const base = m[1];
  // Keep the title suffix 404.html was written with (tools/site_brand.py).
  const titleSuffix = document.title.slice(document.title.lastIndexOf(' · '));
  const $ = (id) => document.getElementById(id),
    fmt = (n) => n.toLocaleString(),
    esc = (s) =>
      String(s ?? '').replace(
        /[&<>"']/g,
        (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
      );
  const input = $('search-q'),
    out = $('search-results');
  $('not-found').hidden = true;
  page.hidden = false;
  document.documentElement.classList.add('search-route');

  const termsOf = (raw) => {
    try {
      return decodeURIComponent(raw.replace(/\+/g, ' ')).trim();
    } catch {
      return raw.trim();
    }
  };
  const urlOf = (q) => base + 'q=' + encodeURIComponent(q);
  const ALIASES = {
    '日本語族': 'japonic',
    '印欧': 'indo-european',
    'インドヨーロッパ': 'indo-european',
    '琉球': 'ryukyuan',
    '手話': 'sign language',
  };
  const rankLevel = { language: 0, family: 1, genus: 2, dialect: 3 };
  const kindRank = (n) => (n.isolate ? 0 : (rankLevel[n.level] ?? 4));
  function matchRank(n, q) {
    const nm = n.name.toLowerCase();
    if (nm === q || (n.iso || '').toLowerCase() === q || n.id.toLowerCase() === q) return 0;
    if (nm.startsWith(q)) return 1;
    if (nm.split(/[\s\-‑'’()]+/).some((w) => w.startsWith(q))) return 2;
    return 3;
  }
  // Matches shown at once; the message below the list says the same number.
  const SEARCH_LIMIT = 150;

  let data = null,
    unified = null,
    nodes = null,
    sourcePaths = {};
  function pageURL(id) {
    if (data.nodes[id]) return base + window.LineagePaths.url(id);
    if (sourcePaths[id]) return base + sourcePaths[id];
    return base + 'record.html?domain=language&id=' + encodeURIComponent(id);
  }
  function ancestors(id) {
    const a = [],
      seen = new Set();
    while (data.nodes[id] && !seen.has(id)) {
      seen.add(id);
      a.unshift(id);
      id = data.nodes[id].parent;
    }
    return a;
  }
  function hitPath(n) {
    if (data.nodes[n.id]) {
      const a = ancestors(n.id).slice(0, -1);
      return a.length ? a.map((id) => esc(nodes[id].name)).join(' › ') : '';
    }
    return esc(unified.sources[n.source]?.title || n.source || '');
  }

  function render() {
    const q0 = termsOf(where()?.[2] || '');
    if (document.activeElement !== input) input.value = q0;
    document.title = (q0 ? q0 + ' · ' : '') + 'Search results' + titleSuffix;
    if (!q0) {
      out.replaceChildren();
      input.focus();
      return;
    }
    const head = `<div class="search-head"><h1>Search results</h1>`;
    if (!data) {
      out.innerHTML = head + `</div><p class="empty">Loading records…</p>`;
      return;
    }
    const q0l = q0.toLowerCase(),
      q = ALIASES[q0l] || q0l;
    const all = Object.values(nodes).filter((n) => n.level !== 'clade' && n.searchText.includes(q));
    const r = new Map(all.map((n) => [n.id, matchRank(n, q)]));
    all.sort(
      (a, b) =>
        r.get(a.id) - r.get(b.id) ||
        kindRank(a) - kindRank(b) ||
        (data.nodes[a.id] ? 0 : 1) - (data.nodes[b.id] ? 0 : 1) ||
        a.name.localeCompare(b.name),
    );
    const shown = all.slice(0, SEARCH_LIMIT);
    out.innerHTML =
      head +
      `<p class="hit-count">${all.length === 1 ? '1 matching record' : fmt(all.length) + ' matching records'}</p><span class="hit-query notranslate" dir="auto">${esc(q0)}</span></div>` +
      (shown.length
        ? `<ol class="hits">${shown
            .map((n) => {
              const path = hitPath(n);
              return `<li><a class="hit" href="${esc(pageURL(n.id))}"><span class="dot"></span><span class="hit-main"><span class="hit-name notranslate" dir="auto">${esc(n.name)}</span><span class="hit-meta"><code class="notranslate">${esc(n.iso || n.id)}</code>${unified.conflictIndex[n.id] ? ' · competing branches' : ''}</span>${path ? `<span class="hit-path notranslate" dir="auto">${path}</span>` : ''}</span></a></li>`;
            })
            .join('')}</ol>` +
          (all.length > SEARCH_LIMIT
            ? `<p class="small">First ${fmt(SEARCH_LIMIT)} matches. Refine your search.</p>`
            : '')
        : '<p class="empty">No matching records.</p>');
  }

  $('search-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) {
      input.focus();
      return;
    }
    const u = urlOf(q);
    if (u !== location.pathname) {
      try {
        history.pushState(null, '', u);
      } catch {
        location.href = u;
        return;
      }
    }
    input.blur();
    render();
    scrollTo(0, 0);
  });
  window.addEventListener('popstate', render);
  render();

  window.AtlasData.base = base + 'data/';
  Promise.all([
    window.AtlasData.load(),
    fetch(base + 'source-paths.json')
      .then((r) => (r.ok ? r.json() : {}))
      .catch(() => ({})),
    window.AtlasData.search().catch((e) => {
      console.error(e);
      return {};
    }),
  ])
    .then(async ([{ d, u }, sp, text]) => {
      await window.LineagePaths.init(d.nodes, d.roots, base);
      nodes = { ...d.nodes, ...u.extraNodes };
      for (const n of Object.values(nodes))
        n.searchText = [n.name, n.id, n.iso, ...(n.names || []).map((r) => r.text)]
          .join(' ')
          .toLowerCase();
      for (const [id, s] of Object.entries(text)) if (nodes[id]) nodes[id].searchText += ' ' + s;
      data = d;
      unified = u;
      sourcePaths = sp;
      render();
    })
    .catch((e) => {
      out.innerHTML = `<p class="load-error">${esc(e.message)}. Reload to retry.</p>`;
      console.error(e);
    });
})();
