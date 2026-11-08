'use strict';
// The search results page of Lang Log, dist/q.html, at <site>/q?q=<terms> (owner,
// 2026-11-08), such as https://lang-log.github.io/q?q=mxi. GitHub Pages serves q.html at
// /q. Browsers can save it as a search engine with %s in place of the terms
// (dist/opensearch.xml says the same), and the search boxes here and on the top page are
// plain GET forms to it, so they need no script to reach it.
//
// q.html is the search page itself: the box, the heading and "Loading records…" are in its
// HTML. This script, loaded in the <head>, sets the title and puts the terms in the box as
// soon as the parser adds it, so nothing is drawn that is not the search page; once the
// page is parsed it lists every matching record, one per row, each linking to its own
// page. Searching again from the box changes the address to the new ?q=<terms>.
// The top page's old ?q= links come here too (dist/home.js).
//
// Ranking: exact name, ISO code or Glottocode; then names that start with the
// query; then a word in the name that starts with it; then any other match.
// Languages come before families and dialects (the order only; no record is
// labelled by its kind, .claude/rules/interface-text.md).
(() => {
  // The page is at the site root, so every address here is relative to it (the live site
  // and a pull request preview under /preview/pr-<n>/ alike).
  const PARAM = 'q';
  const termsNow = () => (new URLSearchParams(location.search).get(PARAM) || '').trim();
  const urlOf = (q) => '?' + new URLSearchParams({ [PARAM]: q });
  // Keep the title suffix q.html was written with (tools/site_brand.py).
  const titleSuffix = document.title.slice(document.title.lastIndexOf(' · '));
  const setTitle = (q) => {
    document.title = (q ? q + ' · ' : '') + 'Search results' + titleSuffix;
  };
  setTitle(termsNow());
  // As soon as the parser adds them: put the terms in the box, so it is never drawn empty,
  // and show the "Loading records…" part of q.html (hidden in its HTML, so a browser
  // without scripts never shows it) only when there is something to load.
  const prepare = () => {
    const box = document.getElementById('search-q'),
      out = document.getElementById('search-results');
    if (box) box.value = termsNow();
    if (out) out.hidden = !termsNow();
    return !!(box && out);
  };
  const watch = new MutationObserver(() => {
    if (prepare()) watch.disconnect();
  });
  watch.observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener('DOMContentLoaded', () => {
    watch.disconnect();
    prepare();
    start();
  });

  function start() {
    const $ = (id) => document.getElementById(id),
      fmt = (n) => n.toLocaleString(),
      esc = (s) =>
        String(s ?? '').replace(
          /[&<>"']/g,
          (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
        );
    const input = $('search-q'),
      out = $('search-results');
    // What the page shows until the records are loaded, written once in dist/q.html.
    const loading = [...out.childNodes].map((n) => n.cloneNode(true));
    out.hidden = false;
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
      if (data.nodes[id]) return window.LineagePaths.url(id);
      if (sourcePaths[id]) return sourcePaths[id];
      return 'record.html?domain=language&id=' + encodeURIComponent(id);
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
      const q0 = termsNow();
      if (document.activeElement !== input) input.value = q0;
      setTitle(q0);
      if (!q0) {
        out.replaceChildren();
        input.focus();
        return;
      }
      if (!data) {
        out.replaceChildren(...loading.map((n) => n.cloneNode(true)));
        return;
      }
      const head = `<div class="search-head"><h1>Search results</h1>`;
      const q0l = q0.toLowerCase(),
        q = ALIASES[q0l] || q0l;
      const all = Object.values(nodes).filter(
        (n) => n.level !== 'clade' && n.searchText.includes(q),
      );
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
      if (u !== location.search) {
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

    Promise.all([
      window.AtlasData.load(),
      fetch('source-paths.json')
        .then((r) => (r.ok ? r.json() : {}))
        .catch(() => ({})),
      window.AtlasData.search().catch((e) => {
        console.error(e);
        return {};
      }),
    ])
      .then(async ([{ d, u }, sp, text]) => {
        await window.LineagePaths.init(d.nodes, d.roots);
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
  }
})();
