// The explorer: two views of the languages, a switch between them (List, Map) and the
// conditions they share (markup from tools/explore_panel.py). It runs on the element
// marked "explorer": data-base is the path to the site root, and data-langs (record
// pages) the Glottocodes of the languages it narrows; without it, every language.
// Top page (tools/build_home.py):
//   List  the top-level records under their continents (static; works without
//         JavaScript). Each row opens into its members, as the outline of a record page
//         does (dist/tree.js, LangLogTree.members); the list and the former Tree view
//         are one (owner, issue #93), and the tree's Download menu sits above the list.
//         Conditions hide the records no matching language belongs to, and the opened
//         members keep only the matching languages, their ancestors and their dialects.
//   Map   every Glottolog language with a point, coloured by one feature if chosen.
// Record pages (record_views() in tools/build_paths.py; owner, 2026-11-24):
//   List  the tree of the record's descendants (dist/tree.js), narrowed like the top
//         page's opened rows.
//   Map   the record's map (tools/build_paths.py). With a condition or a colour, its own
//         points give way to the record's matching languages, drawn as on the top page.
// The view shown when the address names none is the one pressed in the markup.
// Data: dist/data/features/ written by tools/build_wals_map.py (WALS features and
// Lang Log's own evidence features).
//
// Every language starts in. Conditions narrow it: each
// condition is one feature and what to keep. A feature's type (tools/condition_features.py)
// says what that is: values to keep (joined by OR; "No data" is one of them), a range
// of numbers (Minimum, Maximum and "No data"), text in the name, or a range of a number
// worked out for a chosen language (WALS values shared with it, distance from it).
// Conditions are joined by AND unless the visitor switches the joint to OR;
// conditions joined by OR form one group, and the groups are joined by AND, so
// "A and B or C" reads "A and (B or C)". NOT turns one condition round. With a
// minimum number of conditions set, a language passes when it matches at least that
// many, and the joints are not used. Colouring is separate: one feature, or none.
//
// State lives in the address: ?view=map&c=81A:1,5&c=|!6A:2,4,0&c=lat:10~40&k=81A&m=2
// (view: the shown view, left out for the first one; one c per condition, in order; "|"
// joins it to the previous one by OR, "!" is NOT; values are left out when all are kept
// and 0 is "No data"; a range is lo~hi, either end may be empty, and ,0 adds "No data";
// text is URL-encoded; @<Glottocode> names the chosen language; k is the colour feature;
// m the minimum number of conditions). Other parameters are kept as they are. The
// former ?view=tree opens the list (on record pages it is dist/tree.js's drawn tree,
// inside the list, and is kept).
(function () {
  'use strict';
  var $ = function (id) {
    return document.getElementById(id);
  };
  var NS = 'http://www.w3.org/2000/svg';
  // Categorical colours in fixed order (style.css --c-* variables). A feature with more
  // values than slots gives the slots to its most common values and the rest are grey.
  var SLOTS = [
    '--c-2a78d6',
    '--c-eb6834',
    '--c-1baf7a',
    '--c-eda100',
    '--c-e87ba4',
    '--c-008300',
    '--c-6250d6',
    '--c-e34948',
  ];
  var OTHER = '--c-9ba8a4';
  var PLAIN = '--c-386e6d';
  var NODATA = '--c-a5aeb0'; // colour of a dot without a value
  // A list of values longer than this gets a "Find a value" box above it.
  var FIND_MIN = 20;
  // Kilometres in the Earth's mean radius, for the distance between two points.
  var EARTH_KM = 6371;
  var L = null,
    ROOT = -1, // index of the "root" field in the rows of languages.json
    NAME = -1, // index of the "name" field
    F = null,
    byId = {},
    cache = {},
    vals = {},
    names = {}, // feature id -> {value number: name}, filled when its values are known
    folded = null, // every language's name, folded for the Name condition
    walsTable = null; // wals.json, for "WALS values shared with a language"
  // {id, or (joined to the previous by OR), not, shown: Set of values (0 = No data),
  //  lo, hi (a range; null = open), text, ref (Glottocode of the chosen language), calc}
  var conds = [];
  var minMatch = 0; // 0: AND / OR as set
  var colourBy = '',
    colour = {};
  var root = document.querySelector('.explorer');
  if (!root) return;
  var svg = root.querySelector('svg.lmap'),
    layer = $('points'),
    BASE = root.dataset.base || '',
    // The record's languages (record pages): a Set of Glottocodes, or null for all.
    scope = root.dataset.langs ? new Set(root.dataset.langs.split(' ')) : null,
    idx = [], // indexes of the rows of languages.json the explorer narrows
    mounted = false,
    lastMatch = '';
  if (!svg) return;
  var viewButtons = root.querySelectorAll('.explore-views button[data-view]');
  var VIEWS = Array.prototype.map.call(viewButtons, function (b) {
    return b.dataset.view;
  });
  var FIRST = (root.querySelector('.explore-views button[aria-pressed="true"]') || viewButtons[0])
    .dataset.view;
  var view = FIRST;
  // A record map keeps its own points (tools/build_paths.py) until a condition or a colour
  // asks for the languages: they are drawn in a layer of their own, as on the top page.
  // While they give way, they are taken out of the map, so dist/map-zoom.js sizes and steps
  // through the drawn points only.
  var own = layer ? [] : Array.prototype.slice.call(svg.querySelectorAll('.lmap-main, .lmap-self'));
  if (!layer) {
    layer = document.createElementNS(NS, 'g');
    layer.setAttribute('class', 'explore-points');
    (own[0] ? own[0].parentNode : svg).insertBefore(layer, own[0] || null);
  }
  // The radius a record map gives its points (data-r, tools/languoid_map.py); the top
  // page's map has none.
  var UNIT_R = svg.getAttribute('data-r');

  function get(url) {
    if (!cache[url])
      cache[url] = fetch(url).then(function (r) {
        if (!r.ok) throw new Error(url);
        return r.json();
      });
    return cache[url];
  }

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }

  function type(id) {
    return byId[id].type || 'category';
  }

  // Load what a feature needs: its values per language (f/<id>.json), its list of values
  // when features.json leaves it out (f/<id>.values.json), and for a relative feature the
  // data it is worked out from.
  function load(id) {
    if (!id) return Promise.resolve();
    var f = byId[id],
      t = type(id),
      jobs = [];
    if (t === 'relative')
      return f.measure === 'shared'
        ? get(BASE + 'data/features/wals.json').then(function (w) {
            walsTable = w;
          })
        : Promise.all([load('lat'), load('lon')]);
    if (t !== 'text' && !vals[id])
      jobs.push(
        get(BASE + 'data/features/f/' + id + '.json').then(function (v) {
          vals[id] = v;
        }),
      );
    if (t === 'category' && !f.values)
      jobs.push(
        get(BASE + 'data/features/f/' + id + '.values.json').then(function (v) {
          f.values = v;
        }),
      );
    return Promise.all(jobs).then(function () {
      if (f.values && !names[id]) {
        names[id] = {};
        f.values.forEach(function (v) {
          names[id][v.n] = v.name;
        });
      }
    });
  }

  function allValues(id) {
    return byId[id].values.map(function (x) {
      return x.n;
    });
  }

  // The name of a value as the page shows it. Region codes are named by the browser in
  // the page's language (Intl), so they need no dictionary.
  var regions = null,
    regionsLang = '';
  function valueName(f, v) {
    if (f.names !== 'region') return v.name;
    var lang = document.documentElement.lang || 'en';
    if (regionsLang !== lang) {
      regionsLang = lang;
      try {
        regions = new Intl.DisplayNames([lang], { type: 'region' });
      } catch {
        regions = null;
      }
    }
    try {
      return (regions && regions.of(v.name)) || v.name;
    } catch {
      return v.name;
    }
  }

  // One c parameter -> a condition (values are checked once the feature has loaded).
  function parseCond(s) {
    var c = { or: false, not: false, shown: null, lo: null, hi: null, text: '', ref: '' };
    if (s.charAt(0) === '|') {
      c.or = true;
      s = s.slice(1);
    }
    if (s.charAt(0) === '!') {
      c.not = true;
      s = s.slice(1);
    }
    var at = s.indexOf(':'),
      id = at < 0 ? s : s.slice(0, at),
      spec = at < 0 ? '' : s.slice(at + 1);
    var ref = id.indexOf('@');
    if (ref >= 0) {
      c.ref = id.slice(ref + 1);
      id = id.slice(0, ref);
    }
    if (!byId[id]) return null;
    c.id = id;
    c.spec = spec;
    return c;
  }

  // Fill a parsed condition from its spec, now that its feature has loaded.
  function fillCond(c) {
    var t = type(c.id),
      spec = c.spec || '';
    delete c.spec;
    if (t === 'text') {
      try {
        c.text = decodeURIComponent(spec);
      } catch {
        c.text = spec;
      }
      return;
    }
    var parts = spec ? spec.split(',') : [];
    if (t === 'number' || t === 'relative') {
      c.shown = new Set(parts.indexOf('0') >= 0 ? [0] : []);
      var range = parts.filter(function (x) {
        return x.indexOf('~') >= 0;
      })[0];
      if (range) {
        var ends = range.split('~');
        c.lo = num(ends[0]);
        c.hi = num(ends[1]);
      }
      return;
    }
    var known = new Set(allValues(c.id).concat([0])),
      keep = parts.map(Number).filter(function (n) {
        return known.has(n);
      });
    c.shown = new Set(keep.length ? keep : allValues(c.id));
  }

  function num(x) {
    return x === '' || x == null || isNaN(Number(x)) ? null : Number(x);
  }

  function readURL() {
    var p = new URLSearchParams(location.search),
      out = [];
    p.getAll('c').forEach(function (s) {
      var c = parseCond(s);
      if (!c) return;
      if (!out.length) c.or = false;
      out.push(c);
    });
    var m = parseInt(p.get('m'), 10);
    return {
      conds: out,
      k: byId[p.get('k')] && colourable(byId[p.get('k')]) ? p.get('k') : '',
      m: m > 0 ? m : 0,
      view: viewOf(p.get('view')),
    };
  }

  // The view an address names: one of the switch's, or the list for the former (top page)
  // or drawn (record pages) tree; otherwise the first.
  function viewOf(v) {
    if (v === 'tree' && VIEWS.indexOf('list') >= 0) return 'list';
    return VIEWS.indexOf(v) >= 0 ? v : FIRST;
  }

  function condParam(c) {
    var t = type(c.id),
      head = (c.or ? '|' : '') + (c.not ? '!' : '') + c.id + (c.ref ? '@' + c.ref : ''),
      spec;
    if (t === 'text') spec = c.text ? encodeURIComponent(c.text) : '';
    else if (t === 'number' || t === 'relative') {
      var bits = [];
      if (c.lo != null || c.hi != null)
        bits.push((c.lo != null ? c.lo : '') + '~' + (c.hi != null ? c.hi : ''));
      if (c.shown.has(0)) bits.push('0');
      spec = bits.join(',');
    } else {
      var all = allValues(c.id),
        on = all.filter(function (n) {
          return c.shown.has(n);
        });
      if (c.shown.has(0)) on.push(0);
      spec = on.length === all.length && !c.shown.has(0) ? '' : on.join(',');
    }
    return head + (spec ? ':' + spec : '');
  }

  function writeURL() {
    var p = new URLSearchParams(location.search),
      drawnTree = scope && view === 'list' && p.get('view') === 'tree';
    ['view', 'c', 'k', 'm'].forEach(function (key) {
      p.delete(key);
    });
    if (drawnTree) p.set('view', 'tree');
    else if (view !== FIRST) p.set('view', view);
    conds.forEach(function (c) {
      if (c.id) p.append('c', condParam(c));
    });
    if (colourBy) p.set('k', colourBy);
    if (minMatch) p.set('m', String(minMatch));
    var q = p
      .toString()
      .replace(/%2C/g, ',')
      .replace(/%3A/g, ':')
      .replace(/%7C/g, '|')
      .replace(/%7E/g, '~')
      .replace(/%40/g, '@')
      .replace(/%21/g, '!');
    // Keep the #map-view of the full-screen map (dist/map-zoom.js) and its history entry.
    history.replaceState(history.state, '', (q ? '?' + q : location.pathname) + location.hash);
  }

  // Only a feature with one value from a list per language can colour the map.
  function colourable(f) {
    return !f.type && !f.multi;
  }

  function featureSelect(value, emptyLabel, only) {
    var s = el('select', { class: 'wm-feature' }),
      groups = {};
    s.appendChild(el('option', { value: '' }, emptyLabel));
    F.features.forEach(function (f) {
      if (only && !only(f)) return;
      if (!groups[f.area]) {
        groups[f.area] = el('optgroup', { label: f.area });
        s.appendChild(groups[f.area]);
      }
      // The menu shows the feature name only, without the WALS id or the number of
      // languages (the owner's choice, 2026-11-08).
      groups[f.area].appendChild(el('option', { value: f.id }, f.name));
    });
    s.value = value || '';
    return s;
  }

  function colours(f) {
    var out = {},
      vs = f.values.slice();
    var top =
      vs.length <= SLOTS.length
        ? vs
        : vs
            .slice()
            .sort(function (x, y) {
              return y.count - x.count;
            })
            .slice(0, SLOTS.length - 1);
    var keep = new Set(
        top.map(function (x) {
          return x.n;
        }),
      ),
      i = 0;
    vs.forEach(function (x) {
      out[x.n] = keep.has(x.n) ? SLOTS[i++] : OTHER;
    });
    return out;
  }

  // Text folded for the Name condition: lower case, without accents.
  function fold(text) {
    return String(text).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  // Whether a condition narrows anything yet: a chosen feature, and for text or a chosen
  // language, the text or the language.
  function active(c) {
    if (!c.id) return false;
    var t = type(c.id);
    if (t === 'text') return !!c.text;
    if (t === 'relative') return !!c.calc;
    return true;
  }

  function inRange(c, v, wrap) {
    if (wrap && c.lo != null && c.hi != null && c.lo > c.hi) return v >= c.lo || v <= c.hi;
    return (c.lo == null || v >= c.lo) && (c.hi == null || v <= c.hi);
  }

  // Whether language i matches condition c (before NOT).
  function matches(c, i) {
    var f = byId[c.id],
      t = type(c.id);
    if (t === 'text') return folded[i].indexOf(fold(c.text)) >= 0;
    if (t === 'number' || t === 'relative') {
      var x = t === 'relative' ? c.calc[i] : vals[c.id][i];
      return x == null ? c.shown.has(0) : inRange(c, x, f.wrap);
    }
    var v = vals[c.id][i];
    if (f.multi) {
      if (!v.length) return c.shown.has(0);
      for (var k = 0; k < v.length; k++) if (c.shown.has(v[k])) return true;
      return false;
    }
    return c.shown.has(v || 0);
  }

  // Whether language i passes the conditions: every group of them, or with a minimum
  // number set, at least that many.
  function passes(i) {
    var groupOk = null,
      hits = 0;
    for (var j = 0; j < conds.length; j++) {
      var c = conds[j];
      if (!active(c)) continue;
      var ok = matches(c, i) !== c.not;
      if (minMatch) {
        if (ok) hits++;
        continue;
      }
      if (groupOk === null || !c.or) {
        if (groupOk === false) return false;
        groupOk = ok;
      } else {
        groupOk = groupOk || ok;
      }
    }
    return minMatch ? hits >= minMatch : groupOk !== false;
  }

  function anyCondition() {
    return conds.some(active);
  }

  // Work out a relative feature for the chosen language: the number of WALS values each
  // language shares with it, or the distance from it in kilometres (null: no data).
  function calc(c) {
    c.calc = null;
    if (!c.ref) return;
    var f = byId[c.id],
      ref = -1;
    for (var i = 0; i < L.rows.length; i++)
      if (L.rows[i][0] === c.ref) {
        ref = i;
        break;
      }
    if (ref < 0) return;
    var out = new Array(L.rows.length).fill(null);
    if (f.measure === 'shared') {
      var W = walsTable,
        me = W.rows[ref];
      if (!me) return;
      for (var k in W.rows) {
        var row = W.rows[k],
          n = 0;
        for (var m = 0; m < me.length; m++) if (me[m] && row[m] === me[m]) n++;
        out[k] = n;
      }
    } else {
      var lat = vals.lat,
        lon = vals.lon;
      if (lat[ref] == null) return;
      var rad = Math.PI / 180,
        a1 = lat[ref] * rad,
        b1 = lon[ref] * rad;
      for (var j = 0; j < out.length; j++) {
        if (lat[j] == null) continue;
        var a2 = lat[j] * rad,
          d =
            Math.sin((a2 - a1) / 2) ** 2 +
            Math.cos(a1) * Math.cos(a2) * Math.sin((lon[j] * rad - b1) / 2) ** 2;
        out[j] = Math.round(2 * EARTH_KM * Math.asin(Math.sqrt(d)));
      }
    }
    c.calc = out;
  }

  // Apply the conditions to every view: the count, the list (with its opened rows) and the
  // map.
  function apply() {
    var rows = L.rows,
      n = 0,
      roots = new Set(),
      ids = [];
    idx.forEach(function (j) {
      if (passes(j)) {
        n++;
        roots.add(rows[j][ROOT]);
        ids.push(rows[j][0]);
      }
    });
    $('count').textContent = 'Showing ' + n + ' of ' + idx.length + ' languages';
    var on = anyCondition();
    root.querySelectorAll('.explore-view li[data-root]').forEach(function (li) {
      li.hidden = on && !roots.has(li.dataset.root);
    });
    root.querySelectorAll('.explore-view .continent').forEach(function (box) {
      box.hidden = !box.querySelector('li[data-root]:not([hidden])');
    });
    var outgroups = root.querySelector('.outgroups');
    if (outgroups) outgroups.hidden = on;
    // Colouring alone changes nothing in the list: only a new set of languages
    // redraws the tree and closes the opened rows.
    var match = on ? ids.join(',') : '';
    if (match !== lastMatch) {
      lastMatch = match;
      if (window.LangLogTree) window.LangLogTree.setMatch(on ? ids : null);
      closeRows();
    }
    if (view === 'map') draw();
  }

  function draw() {
    if (!L) return;
    layer.textContent = '';
    var rows = L.rows,
      frag = document.createDocumentFragment();
    var cv = colourBy ? vals[colourBy] : null,
      perValue = {};
    // A record map shows its own points until a condition or a colour is set.
    var ownPoints = own.length && !colourBy && !anyCondition();
    own.forEach(function (g) {
      if (ownPoints && !g.parentNode) layer.parentNode.insertBefore(g, layer);
      else if (!ownPoints && g.parentNode) g.remove();
    });
    if (ownPoints) {
      colourLegend(perValue);
      if (svg.__lmap) svg.__lmap.refresh();
      return;
    }
    for (var x = 0; x < idx.length; x++) {
      var i = idx[x];
      // A language without coordinates has no point.
      if (rows[i][4] == null || !passes(i)) continue;
      var c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', rows[i][4]);
      c.setAttribute('cy', rows[i][5]);
      if (UNIT_R) c.setAttribute('r', UNIT_R);
      var v = cv ? cv[i] : 0;
      c.setAttribute('fill', 'var(' + (cv ? (v ? colour[v] : NODATA) : PLAIN) + ')');
      if (cv && !v) c.setAttribute('class', 'wm-nodata');
      // Its value (0: no data), for the legend entries that step through their points.
      if (cv) c.setAttribute('data-v', v);
      if (cv) perValue[v] = (perValue[v] || 0) + 1;
      // Its Glottocode: dist/map-zoom.js shows the record box of a tapped dot, as on
      // the record maps.
      c.setAttribute('data-g', rows[i][0]);
      // Dots with no colour value go underneath.
      if (cv && !v) frag.insertBefore(c, frag.firstChild);
      else frag.appendChild(c);
    }
    layer.appendChild(frag);
    colourLegend(perValue);
    // map-zoom.js sizes the dots, moves each to the copy of the world in view, and makes
    // the new key entries buttons.
    if (svg.__lmap) svg.__lmap.refresh();
  }

  // The key of the colours under the map: the same key as on the record maps
  // (tools/build_paths.py). Each entry names its points (data-points), so dist/map-zoom.js
  // makes it a button that goes to the first of them, after which the map's < and > buttons
  // step through that value's points. The mark takes the value's colour (--key-colour).
  function keyEntry(n, colourVar, name, count, data) {
    var li = el('li', { class: 'lmap-key-value' });
    li.style.setProperty('--key-colour', 'var(' + colourVar + ')');
    if (count) li.setAttribute('data-points', '.explore-points circle[data-v="' + n + '"]');
    li.appendChild(el('span', data ? { class: 'notranslate' } : null, name));
    li.appendChild(el('small', null, String(count)));
    return li;
  }

  // The top page has a key of its own for the colours (#colour-legend); a record map adds the
  // entries to its key, in place of the entries of its own points while they are hidden.
  function colourLegend(perValue) {
    var key = $('colour-legend') || svg.parentNode.querySelector('.lmap-key');
    if (!key) return;
    Array.prototype.forEach.call(key.querySelectorAll('.lmap-key-value'), function (li) {
      li.remove();
    });
    if (key.id === 'colour-legend') key.hidden = !colourBy;
    else
      Array.prototype.forEach.call(key.children, function (li) {
        li.hidden = !!colourBy;
      });
    if (!colourBy) return;
    var f = byId[colourBy];
    f.values.forEach(function (v) {
      key.appendChild(keyEntry(v.n, colour[v.n], valueName(f, v), perValue[v.n] || 0, !!f.names));
    });
    if (perValue[0]) key.appendChild(keyEntry(0, NODATA, 'No data', perValue[0]));
  }

  function update() {
    apply();
    writeURL();
    var box = root.querySelector('.wm-min');
    if (box)
      box.hidden =
        conds.filter(function (c) {
          return c.id;
        }).length < 2;
  }

  // Show one view. The map is mounted the first time it is shown, when its box has a size.
  function showView(v) {
    view = v;
    viewButtons.forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.view === v));
    });
    root.querySelectorAll('.explore-view').forEach(function (box) {
      box.hidden = box.dataset.view !== v;
    });
    // Colouring and the area in view belong to the map only.
    root.querySelector('.explore-colour').hidden = v !== 'map';
    // The tree is drawn the first time the list is shown (the top page: its Download menu).
    if (v === 'list' && window.LangLogTree) window.LangLogTree.start();
    if (v === 'map') {
      draw();
      if (!mounted && window.LangLogMap) {
        mounted = true;
        window.LangLogMap.mount(svg);
      }
    }
  }

  // Each row of the list opens into its members (issue #93). The static row (its link,
  // native names and notes) becomes the summary of a <details>; the members are drawn by
  // dist/tree.js the first time it opens, so the data loads only when a row is opened.
  var rows = [];
  function openableRows() {
    if (!window.LangLogTree) return;
    root.querySelectorAll('.explore-view li[data-root]').forEach(function (li) {
      var box = el('details', { class: 'tree-node' }),
        sum = el('summary');
      while (li.firstChild) sum.appendChild(li.firstChild);
      box.appendChild(sum);
      li.appendChild(box);
      li.classList.add('openable');
      var row = { box: box, id: li.dataset.root, drawn: null };
      box.addEventListener('toggle', function () {
        if (box.open && !row.drawn) fill(row);
      });
      rows.push(row);
    });
  }
  function fill(row) {
    var drawn = window.LangLogTree.members(row.id).then(function (kids) {
      // A change of conditions while the data loaded closed the row: draw nothing.
      if (row.drawn !== drawn) return;
      row.box.appendChild(kids);
    });
    row.drawn = drawn;
    drawn.catch(function (e) {
      if (row.drawn === drawn) row.drawn = null;
      console.error(e);
    });
  }
  // Conditions changed: close every opened row, so it is drawn again with the new ones.
  function closeRows() {
    rows.forEach(function (row) {
      if (!row.drawn) return;
      row.drawn = null;
      row.box.open = false;
      var kids = row.box.querySelector(':scope > .node-children');
      if (kids) kids.remove();
    });
  }

  // A checkbox row: a label with the box, the text and a count (or none).
  function checkRow(text, count, data) {
    var li = el('li'),
      lab = el('label'),
      cb = el('input', { type: 'checkbox' });
    lab.appendChild(cb);
    lab.appendChild(el('span', data ? { class: 'notranslate' } : null, text));
    if (count != null) lab.appendChild(el('small', null, String(count)));
    li.appendChild(lab);
    return { li: li, cb: cb };
  }

  // The "No data" box of a condition, for the languages without a value.
  function noDataRow(c) {
    var r = checkRow('No data', null);
    r.li.classList.add('wm-nodata-row');
    r.cb.checked = c.shown.has(0);
    r.cb.addEventListener('change', function () {
      if (r.cb.checked) c.shown.add(0);
      else c.shown.delete(0);
      update();
    });
    return r.li;
  }

  // Minimum and Maximum of a number condition.
  function rangeBox(c, f) {
    var box = el('div', { class: 'wm-range' });
    [
      ['lo', 'Minimum', f.min],
      ['hi', 'Maximum', f.max],
    ].forEach(function (end) {
      var lab = el('label', null, end[1] + ' '),
        input = el('input', { type: 'number', step: 'any', inputmode: 'decimal' });
      // The range of the data, as a hint in the box (numbers, not text).
      if (end[2] != null) input.setAttribute('placeholder', String(end[2]));
      if (c[end[0]] != null) input.value = String(c[end[0]]);
      input.addEventListener('input', function () {
        c[end[0]] = num(input.value);
        update();
      });
      lab.appendChild(input);
      box.appendChild(lab);
    });
    return box;
  }

  // The language a relative condition is worked out for.
  function languageBox(c, f) {
    var lab = el('label', { class: 'wm-language' }, 'Choose a language '),
      sel = el('select', { class: 'notranslate' });
    sel.appendChild(el('option', { value: '' }, ''));
    var W = f.measure === 'shared' ? walsTable : null,
      opts = [];
    L.rows.forEach(function (r, i) {
      if (W ? W.rows[i] : vals.lat[i] != null) opts.push(r);
    });
    opts.sort(function (a, b) {
      return a[NAME].localeCompare(b[NAME]);
    });
    opts.forEach(function (r) {
      sel.appendChild(el('option', { value: r[0] }, r[NAME]));
    });
    sel.value = c.ref || '';
    sel.addEventListener('change', function () {
      c.ref = sel.value;
      calc(c);
      update();
    });
    lab.appendChild(sel);
    return lab;
  }

  // The number of the record's languages with each value of a feature (0: no data).
  function scopeCounts(id) {
    var out = {},
      v = vals[id],
      multi = byId[id].multi;
    idx.forEach(function (i) {
      var x = v[i];
      (multi ? (x && x.length ? x : [0]) : [x || 0]).forEach(function (n) {
        out[n] = (out[n] || 0) + 1;
      });
    });
    return out;
  }

  // The values of a category condition: "Select all", one box per value and "No data".
  function valueBoxes(c, f, box) {
    var all = allValues(c.id),
      boxes = [],
      data = !!f.names;
    var allLab = el('label', { class: 'wm-selectall' }),
      allCb = el('input', { type: 'checkbox' });
    allLab.appendChild(allCb);
    allLab.appendChild(el('span', null, 'Select all'));
    box.appendChild(allLab);
    var sync = function () {
      boxes.forEach(function (b) {
        b.cb.checked = c.shown.has(b.n);
      });
      var on = all.filter(function (n) {
        return c.shown.has(n);
      }).length;
      allCb.checked = on === all.length;
      allCb.indeterminate = on > 0 && on < all.length;
    };
    allCb.addEventListener('change', function () {
      var nodata = c.shown.has(0);
      c.shown = new Set(allCb.checked ? all : []);
      if (nodata) c.shown.add(0);
      sync();
      update();
    });
    var ul = el('ul', { class: f.values.length > FIND_MIN ? 'wm-long' : '' });
    if (f.values.length > FIND_MIN) {
      var find = el('input', {
        type: 'search',
        class: 'wm-find',
        placeholder: 'Find a value',
        'aria-label': 'Find a value',
      });
      find.addEventListener('input', function () {
        var q = fold(find.value);
        boxes.forEach(function (b) {
          b.li.hidden = q !== '' && b.name.indexOf(q) < 0;
        });
      });
      box.appendChild(find);
    }
    // The number of languages with each value: the feature's own counts, or on a record
    // page the record's languages counted here.
    var counts = scope ? scopeCounts(c.id) : null;
    // Country names are sorted as the page names them, in its language.
    var shown = f.values.slice();
    if (f.names === 'region')
      shown.sort(function (a, b) {
        return valueName(f, a).localeCompare(valueName(f, b), document.documentElement.lang);
      });
    shown.forEach(function (v) {
      var name = valueName(f, v),
        r = checkRow(name, counts ? counts[v.n] || 0 : v.count, data);
      boxes.push({ cb: r.cb, n: v.n, li: r.li, name: fold(name) });
      r.cb.addEventListener('change', function () {
        if (r.cb.checked) c.shown.add(v.n);
        else c.shown.delete(v.n);
        sync();
        update();
      });
      ul.appendChild(r.li);
    });
    box.appendChild(ul);
    // Only a feature some languages lack offers "No data".
    if (counts ? counts[0] : f.languages < L.rows.length) {
      var rest = el('ul');
      rest.appendChild(noDataRow(c));
      box.appendChild(rest);
    }
    sync();
  }

  // One condition: feature menu, NOT, remove button and what to keep.
  function condBox(c, idx) {
    var box = el('section', { class: 'wm-cond' });
    var head = el('div', { class: 'wm-cond-head' });
    var sel = featureSelect(c.id, 'Choose a feature');
    sel.addEventListener('change', function () {
      var id = sel.value;
      load(id).then(function () {
        c.id = id;
        c.shown = new Set(id && type(id) === 'category' ? allValues(id) : []);
        c.lo = c.hi = null;
        c.text = c.ref = '';
        c.calc = null;
        renderConds();
        update();
      });
    });
    head.appendChild(sel);
    if (c.id) {
      var not = el(
        'button',
        { type: 'button', class: 'wm-not', 'aria-pressed': String(c.not) },
        'NOT',
      );
      not.addEventListener('click', function () {
        c.not = !c.not;
        not.setAttribute('aria-pressed', String(c.not));
        update();
      });
      head.appendChild(not);
    }
    var rm = el(
      'button',
      { type: 'button', class: 'wm-remove', 'aria-label': 'Remove this condition' },
      '×',
    );
    rm.addEventListener('click', function () {
      conds.splice(idx, 1);
      if (conds.length) conds[0].or = false;
      renderConds();
      update();
    });
    head.appendChild(rm);
    box.appendChild(head);
    if (!c.id) return box;
    var f = byId[c.id],
      t = type(c.id);
    if (t === 'text') {
      var lab = el('label', { class: 'wm-language' }, 'Text in the name '),
        input = el('input', { type: 'search', class: 'wm-find' });
      input.value = c.text;
      input.addEventListener('input', function () {
        c.text = input.value;
        update();
      });
      lab.appendChild(input);
      box.appendChild(lab);
    } else if (t === 'number' || t === 'relative') {
      if (t === 'relative') box.appendChild(languageBox(c, f));
      box.appendChild(rangeBox(c, f));
      var ul = el('ul');
      ul.appendChild(noDataRow(c));
      box.appendChild(ul);
    } else valueBoxes(c, f, box);
    return box;
  }

  function renderConds() {
    var box = $('conditions');
    box.textContent = '';
    conds.forEach(function (c, i) {
      if (i > 0) {
        var join = el('div', { class: 'wm-join' });
        ['and', 'or'].forEach(function (k) {
          var b = el(
            'button',
            { type: 'button', 'aria-pressed': String((k === 'or') === c.or) },
            k === 'and' ? 'AND' : 'OR',
          );
          b.addEventListener('click', function () {
            c.or = k === 'or';
            renderConds();
            update();
          });
          join.appendChild(b);
        });
        box.appendChild(join);
      }
      var cb = condBox(c, i);
      // Conditions joined by OR are drawn as one group.
      if (c.or) cb.classList.add('wm-or');
      if (conds[i + 1] && conds[i + 1].or) cb.classList.add('wm-or-next');
      box.appendChild(cb);
    });
  }

  function setColour(id) {
    return load(id).then(function () {
      colourBy = id;
      colour = id ? colours(byId[id]) : {};
      $('colour').value = id;
    });
  }

  // "Use the area in view": the part of the map in view as a Latitude and a Longitude
  // condition, worked back from the map's Web Mercator units (tools/languoid_map.py:
  // x = SCALE * longitude, y = -SCALE * ln(tan(pi / 4 + latitude / 2)), with the world
  // WORLD_W = 2 * pi * SCALE wide, as data-world gives it).
  function useArea() {
    if (!svg.__lmap) return;
    var v = svg.__lmap.view(),
      world = parseFloat((svg.getAttribute('data-world') || '').split(' ')[2]),
      scale = world / (2 * Math.PI),
      deg = 180 / Math.PI,
      lat = function (y) {
        return Math.round((2 * Math.atan(Math.exp(-y / scale)) - Math.PI / 2) * deg * 100) / 100;
      },
      lon = function (x) {
        return Math.round((((((x / scale) * deg + 180) % 360) + 360) % 360) - 180);
      };
    var add = [{ id: 'lat', lo: lat(v.y + v.h), hi: lat(v.y) }];
    // A view as wide as the world or wider holds every longitude.
    if (v.w < world) add.push({ id: 'lon', lo: lon(v.x), hi: lon(v.x + v.w) });
    conds = conds.filter(function (c) {
      return c.id !== 'lat' && c.id !== 'lon';
    });
    if (conds.length) conds[0].or = false;
    Promise.all([load('lat'), load('lon')]).then(function () {
      add.forEach(function (a) {
        conds.push({
          id: a.id,
          or: false,
          not: false,
          shown: new Set(),
          lo: a.lo,
          hi: a.hi,
          text: '',
          ref: '',
        });
      });
      renderConds();
      update();
    });
  }

  // The rows open, the views switch and the tree works even when the feature data cannot
  // load.
  openableRows();
  view = viewOf(new URLSearchParams(location.search).get('view'));
  showView(view);
  viewButtons.forEach(function (b) {
    b.addEventListener('click', function () {
      showView(b.dataset.view);
      if (L) writeURL();
      else {
        // Before the data has loaded, only the view changes in the address.
        var u = new URL(location.href);
        u.searchParams.delete('view');
        if (b.dataset.view !== FIRST) u.searchParams.set('view', b.dataset.view);
        history.replaceState(history.state, '', u);
      }
    });
  });
  Promise.all([
    get(BASE + 'data/features/languages.json'),
    get(BASE + 'data/features/features.json'),
  ])
    .then(function (res) {
      L = res[0];
      ROOT = L.fields.indexOf('root');
      NAME = L.fields.indexOf('name');
      folded = L.rows.map(function (r) {
        return fold(r[NAME]);
      });
      L.rows.forEach(function (r, i) {
        if (!scope || scope.has(r[0])) idx.push(i);
      });
      F = res[1];
      F.features.forEach(function (f) {
        byId[f.id] = f;
      });
      var s = readURL();
      conds = s.conds;
      minMatch = s.m;
      if (s.view !== view) showView(s.view);
      var colourMenu = featureSelect(s.k, 'None (one colour)', colourable);
      colourMenu.id = 'colour';
      $('colour-slot').appendChild(colourMenu);
      var ids = conds
        .map(function (c) {
          return c.id;
        })
        .concat([s.k]);
      return Promise.all(ids.map(load)).then(function () {
        conds.forEach(function (c) {
          fillCond(c);
          if (type(c.id) === 'relative') calc(c);
        });
        return setColour(s.k);
      });
    })
    .then(function () {
      renderConds();
      // Zoom, pan, borders, detailed tiles, the size of the dots and the buttons of the
      // key come from the shared dist/map-zoom.js (mounted in showView), as on the record maps.
      var min = $('min-match');
      if (min) {
        min.value = minMatch ? String(minMatch) : '';
        min.addEventListener('input', function () {
          var m = parseInt(min.value, 10);
          minMatch = m > 0 ? m : 0;
          update();
        });
      }
      update();
      $('colour').addEventListener('change', function () {
        setColour(this.value).then(update);
      });
      $('use-area').addEventListener('click', useArea);
      $('add-condition').addEventListener('click', function () {
        conds.push({
          id: '',
          or: false,
          not: false,
          shown: new Set(),
          lo: null,
          hi: null,
          text: '',
          ref: '',
        });
        renderConds();
        var sels = document.querySelectorAll('#conditions .wm-feature');
        sels[sels.length - 1].focus();
      });
      // Country names follow the interface language.
      document.addEventListener('langchange', function () {
        renderConds();
        if (view === 'map') draw();
      });
    })
    .catch(function () {
      $('count').textContent = 'The map data could not be loaded.';
    });
})();
