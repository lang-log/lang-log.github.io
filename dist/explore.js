// The three views of every top-level record on the top page (owner, 2026-11-08;
// markup from tools/build_home.py): a switch between them (List, Map, Tree), the
// conditions they share, and the view itself.
//   List  the top-level records under their continents (static; works without
//         JavaScript). Conditions hide the records no matching language belongs to.
//   Map   every Glottolog language with a point, coloured by one feature if chosen.
//   Tree  the zoomable tree of every root (dist/tree.js, started when first shown),
//         narrowed to the matching languages, their ancestors and their dialects.
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
// feature). Other parameters (the tree's x/y/z, dist/tree.js) are kept as they are.
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
  // Dot radius on screen in CSS pixels, whatever the zoom: the record maps' point size
  // (LangLogMap.POINT_PX in map-zoom.js), smaller on narrow maps, and smaller again when
  // many dots (no conditions yet) would overlap.
  var shown = 0;
  var dotPx = function () {
    return (
      window.LangLogMap.POINT_PX * (svg.clientWidth < 600 ? 0.65 : 1) * (shown > 3000 ? 0.7 : 1)
    );
  };

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
    treeStarted = false;
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

  // Apply the conditions to every view: the count, the list, the tree and the map.
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
    shown = n;
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
    if (window.LangLogTree) window.LangLogTree.setMatch(on ? ids : null);
    if (view === 'map') draw();
  }

  function draw() {
    layer.textContent = '';
    var rows = L.rows,
      frag = document.createDocumentFragment();
    var r = radius();
    var cv = colourBy ? vals[colourBy] : null,
      perValue = {};
    for (var i = 0; i < rows.length; i++) {
      if (!passes(i)) continue;
      var c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', rows[i][4]);
      c.setAttribute('cy', rows[i][5]);
      c.setAttribute('r', r);
      var v = cv ? cv[i] : 0;
      c.setAttribute('fill', 'var(' + (cv ? (v ? colour[v] : '--c-a5aeb0') : PLAIN) + ')');
      if (cv && !v) c.setAttribute('class', 'wm-nodata');
      if (cv) perValue[v] = (perValue[v] || 0) + 1;
      // Its Glottocode: dist/map-zoom.js shows the record box of a tapped dot, as on
      // the record maps.
      c.setAttribute('data-g', rows[i][0]);
      // Dots with no colour value go underneath.
      if (cv && !v) frag.insertBefore(c, frag.firstChild);
      else frag.appendChild(c);
    }
    layer.appendChild(frag);
    // map-zoom.js moves each dot to the copy of the world in view.
    if (svg.__lmap) svg.__lmap.refresh();
    colourLegend(perValue);
  }

  // WALS names are quoted from WALS and never translated; Lang Log's own feature and
  // value names are interface text (dist/i18n.js).
  function quoted(fid) {
    return byId[fid].source === 'wals' ? 'notranslate' : '';
  }

  function colourLegend(perValue) {
    var box = $('colour-legend');
    box.textContent = '';
    if (!colourBy) return;
    var ul = el('ul');
    byId[colourBy].values.forEach(function (v) {
      var li = el('li');
      var dot = el('i', { class: 'wm-dot', 'aria-hidden': 'true' });
      dot.style.background = 'var(' + colour[v.n] + ')';
      li.appendChild(dot);
      li.appendChild(el('span', { class: quoted(colourBy) }, v.name));
      li.appendChild(el('small', null, String(perValue[v.n] || 0)));
      ul.appendChild(li);
    });
    if (perValue[0]) {
      var li = el('li'),
        dot = el('i', { class: 'wm-dot wm-dot-nodata', 'aria-hidden': 'true' });
      li.appendChild(dot);
      li.appendChild(el('span', null, 'No data'));
      li.appendChild(el('small', null, String(perValue[0])));
      ul.appendChild(li);
    }
    box.appendChild(ul);
  }

  function update() {
    apply();
    writeURL();
  }

  // Show one view. The map is mounted and the tree started the first time each is shown,
  // when their box has a size.
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
      onZoom();
    }
    if (v === 'tree' && !treeStarted && window.LangLogTree) {
      treeStarted = true;
      window.LangLogTree.start();
    }
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
      lab.appendChild(el('span', { class: quoted(c.id) }, v.name));
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

  function radius() {
    var vb = svg.viewBox.baseVal;
    return (dotPx() * vb.width) / (svg.clientWidth || 1);
  }

  function onZoom() {
    var r = radius(),
      cs = layer.childNodes;
    for (var i = 0; i < cs.length; i++) cs[i].setAttribute('r', r);
    svg.style.setProperty('--unit', String(r / dotPx()));
  }

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
      root.querySelector('.explore-views').hidden = false;
      root.querySelector('.explore-filter').hidden = false;
      viewButtons.forEach(function (b) {
        b.addEventListener('click', function () {
          showView(b.dataset.view);
          writeURL();
        });
      });
      // Zoom, pan, borders and detailed tiles come from the shared dist/map-zoom.js
      // (mounted in showView); it changes the viewBox, so the dots are resized after
      // every change.
      showView(view);
      apply();
      writeURL();
      svg.addEventListener('lmap:view', onZoom);
      window.addEventListener('resize', onZoom);
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
