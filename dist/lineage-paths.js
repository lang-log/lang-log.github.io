'use strict';
// URL of each Glottolog record's own page, which follows its classification:
// <family>/<subgroup>/.../<language>/ below the atlas root. Same rules as build_paths.py:
// ASCII slugs of names, and "-<glottocode>" on both siblings when slugs collide.
window.LineagePaths = (() => {
  let nodes = {},
    roots = [];
  const seg = new Map(),
    cache = new Map();
  const slug = (s) =>
    String(s)
      .normalize('NFKD')
      // eslint-disable-next-line no-control-regex -- [^\x00-\x7f] drops every non-ASCII character
      .replace(/[^\x00-\x7f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  function fill(ids) {
    const base = new Map(ids.map((i) => [i, slug(nodes[i].name) || i])),
      count = new Map();
    for (const s of base.values()) count.set(s, (count.get(s) || 0) + 1);
    for (const [i, s] of base) seg.set(i, count.get(s) === 1 ? s : s + '-' + i);
  }
  function segment(i) {
    if (!seg.has(i)) {
      const p = nodes[i].parent;
      fill(p ? nodes[p].children : roots);
    }
    return seg.get(i);
  }
  function raw(i) {
    if (cache.has(i)) return cache.get(i);
    const parent = nodes[i].parent;
    const p = (parent ? raw(parent) + '/' : '') + segment(i);
    cache.set(i, p);
    return p;
  }
  return {
    // Async so that callers can await it, as when it also loaded a file.
    async init(n, r) {
      nodes = n;
      roots = r;
    },
    // Relative URL from the atlas root, or '' for records without a page.
    url(i) {
      if (!nodes[i]) return '';
      return raw(i) + '/';
    },
  };
})();
