'use strict';
// The Random row on the top page (the only page that has Random). Each
// button opens the page of a record drawn from random.json, which
// tools/build_home.py writes: {language: [page paths], sign: [ids], scripts: [ids]}.
// The row stays hidden without JavaScript.
(() => {
  const row = document.querySelector('.home-random');
  if (!row) return;
  let pools = null;
  const load = () =>
    pools ||
    (pools = fetch('random.json').then((r) => {
      if (!r.ok) throw Error('Could not load random.json');
      return r.json();
    }));
  row.hidden = false;
  for (const b of row.querySelectorAll('button[data-domain]')) {
    b.addEventListener('click', async () => {
      b.disabled = true;
      try {
        const all = await load();
        const pick = (a) => a[Math.floor(Math.random() * a.length)];
        let domain = b.dataset.domain;
        if (domain === 'any') domain = pick(Object.keys(all).filter((k) => (all[k] || []).length));
        const ids = (domain && all[domain]) || [];
        if (!ids.length) return;
        const id = pick(ids);
        location.href =
          domain === 'language'
            ? id
            : 'record.html?domain=' + encodeURIComponent(domain) + '&id=' + encodeURIComponent(id);
      } catch {
        pools = null;
      } finally {
        b.disabled = false;
      }
    });
  }
})();

// The search box is a plain GET form to the results page, dist/q.html at <site>/q?q=<terms>
// (dist/search.js), so it works without this script. Old links to the top page with
// ?q=<terms> go there too, and an empty box does not leave the page.
(() => {
  const form = document.querySelector('form.home-search');
  if (!form) return;
  const old = new URLSearchParams(location.search).get('q');
  if (old !== null && old.trim()) {
    location.replace(form.getAttribute('action') + location.search);
    return;
  }
  form.addEventListener('submit', (e) => {
    if (form.elements.q.value.trim()) return;
    e.preventDefault();
    form.elements.q.focus();
  });
})();
