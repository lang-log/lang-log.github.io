// The two views of every top-level record on the top page (markup from
// tools/build_home.py): a switch between them (List, Map), the conditions they share,
// and the view itself.
//   List  the top-level records under their continents (static; works without
//         JavaScript). Each row opens into its members, as the outline of a record page
//         does (dist/tree.js, LangLogTree.members); the list and the former Tree view
//         are one (owner, issue #93), and the tree's Download menu sits above the list.
//         Conditions hide the records no matching language belongs to, and the opened
//         members keep only the matching languages, their ancestors and their dialects.
//   Map   every Glottolog language with a point, coloured by one feature if chosen.
// Data: dist/data/features/ written by tools/build_wals_map.py (WALS features and
// Lang Log's own evidence features).
//
// Every language starts in. Conditions narrow it: each
// condition is one feature and the values to keep (values in one condition are joined
// by OR). Conditions are joined by AND unless the visitor switches the joint to OR;
// conditions joined by OR form one group, and the groups are joined by AND, so
// "A and B or C" reads "A and (B or C)". A language with no data for a condition's
// feature does not match it. Colouring is separate: one feature, or none.
//
// State lives in the address: ?view=map&c=81A:1,5&c=|6A:2,4&k=81A (view: the shown
// view, left out for the list; one c per condition, in order; "|" joins it to the
// previous one by OR; the values are left out when all are kept; k is the colour
// feature). Other parameters are kept as they are. The former ?view=tree opens the list.
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
  var L = null,
    ROOT = -1, // index of the "root" field in the rows of languages.json
    F = null,
    byId = {},
    cache = {},
    vals = {};
  var conds = []; // {id, shown: Set, or: bool (joined to the previous by OR)}
  var colourBy = '',
    colour = {};
  var svg = $('map'),
    layer = $('points'),
    root = $('families'),
    view = 'list',
    mounted = false,
    lastMatch = '';
  if (!svg || !root) return;
  var viewButtons = root.querySelectorAll('.explore-views button[data-view]');
  var VIEWS = Array.prototype.map.call(viewButtons, function (b) {
    return b.dataset.view;
  });

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

  function load(id) {
    return id && !vals[id]
      ? get('data/features/f/' + id + '.json').then(function (v) {
          vals[id] = v;
        })
      : Promise.resolve();
  }

  function allValues(id) {
    return byId[id].values.map(function (x) {
      return x.n;
    });
  }

  function readURL() {
    var p = new URLSearchParams(location.search),
      out = [];
    p.getAll('c').forEach(function (s) {
      var or = s.charAt(0) === '|';
      if (or) s = s.slice(1);
      var parts = s.split(':'),
        id = parts[0];
      if (!byId[id]) return;
      var keep = parts[1]
        ? parts[1]
            .split(',')
            .map(Number)
            .filter(function (n) {
              return n > 0;
            })
        : [];
      out.push({
        id: id,
        or: or && out.length > 0,
        shown: new Set(keep.length ? keep : allValues(id)),
      });
    });
    return {
      conds: out,
      k: byId[p.get('k')] ? p.get('k') : '',
      view: VIEWS.indexOf(p.get('view')) > 0 ? p.get('view') : VIEWS[0],
    };
  }

  function writeURL() {
    var p = new URLSearchParams(location.search);
    ['view', 'c', 'k'].forEach(function (key) {
      p.delete(key);
    });
    if (view !== VIEWS[0]) p.set('view', view);
    conds.forEach(function (c) {
      if (!c.id) return;
      var all = allValues(c.id),
        on = all.filter(function (n) {
          return c.shown.has(n);
        });
      p.append('c', (c.or ? '|' : '') + c.id + (on.length < all.length ? ':' + on.join(',') : ''));
    });
    if (colourBy) p.set('k', colourBy);
    var q = p.toString().replace(/%2C/g, ',').replace(/%3A/g, ':').replace(/%7C/g, '|');
    // Keep the #map-view of the full-screen map (dist/map-zoom.js) and its history entry.
    history.replaceState(history.state, '', (q ? '?' + q : location.pathname) + location.hash);
  }

  function featureSelect(value, emptyLabel) {
    var s = el('select', { class: 'wm-feature' }),
      groups = {};
    s.appendChild(el('option', { value: '' }, emptyLabel));
    F.features.forEach(function (f) {
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

  // Whether language i passes every group of conditions.
  function passes(i) {
    var groupOk = null;
    for (var j = 0; j < conds.length; j++) {
      var c = conds[j];
      if (!c.id) continue;
      var v = vals[c.id][i],
        ok = !!v && c.shown.has(v);
      if (groupOk === null || !c.or) {
        if (groupOk === false) return false;
        groupOk = ok;
      } else {
        groupOk = groupOk || ok;
      }
    }
    return groupOk !== false;
  }

  function anyCondition() {
    return conds.some(function (c) {
      return c.id;
    });
  }

  // Apply the conditions to every view: the count, the list (with its opened rows) and the
  // map.
  function apply() {
    var rows = L.rows,
      n = 0,
      roots = new Set(),
      ids = [];
    for (var j = 0; j < rows.length; j++)
      if (passes(j)) {
        n++;
        roots.add(rows[j][ROOT]);
        ids.push(rows[j][0]);
      }
    $('count').textContent = 'Showing ' + n + ' of ' + rows.length + ' languages';
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
    layer.textContent = '';
    var rows = L.rows,
      frag = document.createDocumentFragment();
    var cv = colourBy ? vals[colourBy] : null,
      perValue = {};
    for (var i = 0; i < rows.length; i++) {
      if (!passes(i)) continue;
      var c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', rows[i][4]);
      c.setAttribute('cy', rows[i][5]);
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
  function keyEntry(n, colourVar, name, count) {
    var li = el('li', { class: 'lmap-key-value' });
    li.style.setProperty('--key-colour', 'var(' + colourVar + ')');
    if (count) li.setAttribute('data-points', '#points circle[data-v="' + n + '"]');
    li.appendChild(el('span', null, name));
    li.appendChild(el('small', null, String(count)));
    return li;
  }

  function colourLegend(perValue) {
    var key = $('colour-legend');
    key.textContent = '';
    key.hidden = !colourBy;
    if (!colourBy) return;
    byId[colourBy].values.forEach(function (v) {
      key.appendChild(keyEntry(v.n, colour[v.n], v.name, perValue[v.n] || 0));
    });
    if (perValue[0]) key.appendChild(keyEntry(0, NODATA, 'No data', perValue[0]));
  }

  function update() {
    apply();
    writeURL();
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
    // Colouring is drawn on the map only.
    root.querySelector('.explore-colour').hidden = v !== 'map';
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

  // One condition: feature menu, remove button, "Select all" and one checkbox per value.
  function condBox(c, idx) {
    var box = el('section', { class: 'wm-cond' });
    var head = el('div', { class: 'wm-cond-head' });
    var sel = featureSelect(c.id, 'Choose a feature');
    sel.addEventListener('change', function () {
      var id = sel.value;
      load(id).then(function () {
        c.id = id;
        c.shown = new Set(id ? allValues(id) : []);
        renderConds();
        update();
      });
    });
    head.appendChild(sel);
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
      all = allValues(c.id),
      boxes = [];
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
      c.shown = new Set(allCb.checked ? all : []);
      sync();
      update();
    });
    var ul = el('ul');
    f.values.forEach(function (v) {
      var li = el('li'),
        lab = el('label'),
        cb = el('input', { type: 'checkbox' });
      boxes.push({ cb: cb, n: v.n });
      cb.addEventListener('change', function () {
        if (cb.checked) c.shown.add(v.n);
        else c.shown.delete(v.n);
        sync();
        update();
      });
      lab.appendChild(cb);
      lab.appendChild(el('span', null, v.name));
      lab.appendChild(el('small', null, String(v.count)));
      li.appendChild(lab);
      ul.appendChild(li);
    });
    box.appendChild(ul);
    sync();
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

  // The rows open and the tree downloads work even when the feature data cannot load.
  openableRows();
  if (window.LangLogTree) window.LangLogTree.start();
  Promise.all([get('data/features/languages.json'), get('data/features/features.json')])
    .then(function (res) {
      L = res[0];
      ROOT = L.fields.indexOf('root');
      F = res[1];
      F.features.forEach(function (f) {
        byId[f.id] = f;
      });
      var s = readURL();
      conds = s.conds;
      view = s.view;
      var colourMenu = featureSelect(s.k, 'None (one colour)');
      colourMenu.id = 'colour';
      $('colour-slot').appendChild(colourMenu);
      var ids = conds
        .map(function (c) {
          return c.id;
        })
        .concat([s.k]);
      return Promise.all(ids.map(load)).then(function () {
        return setColour(s.k);
      });
    })
    .then(function () {
      renderConds();
      viewButtons.forEach(function (b) {
        b.addEventListener('click', function () {
          showView(b.dataset.view);
          writeURL();
        });
      });
      // Zoom, pan, borders, detailed tiles, the size of the dots and the buttons of the
      // key come from the shared dist/map-zoom.js (mounted in showView), as on the record maps.
      showView(view);
      apply();
      writeURL();
      $('colour').addEventListener('change', function () {
        setColour(this.value).then(update);
      });
      $('add-condition').addEventListener('click', function () {
        conds.push({ id: '', or: false, shown: new Set() });
        renderConds();
        var sels = document.querySelectorAll('#conditions .wm-feature');
        sels[sels.length - 1].focus();
      });
    })
    .catch(function () {
      $('count').textContent = 'The map data could not be loaded.';
    });
})();
