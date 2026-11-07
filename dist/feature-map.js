// Language feature map (feature-map.html). Data: dist/data/features/ written by tools/build_wals_map.py.
//
// The map starts with every language that has a point. Conditions narrow it: each
// condition is one feature and the values to keep (values in one condition are joined
// by OR). Conditions are joined by AND unless the visitor switches the joint to OR;
// conditions joined by OR form one group, and the groups are joined by AND, so
// "A and B or C" reads "A and (B or C)". A language with no data for a condition's
// feature does not match it. Colouring is separate: one feature, or none.
//
// State lives in the address: ?c=81A:1,5&c=|6A:2,4&k=81A (one c per condition, in
// order; "|" joins it to the previous one by OR; the values are left out when all are
// kept; k is the colour feature).
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var NS = 'http://www.w3.org/2000/svg';
  // Categorical colours in fixed order (style.css --c-* variables). A feature with more
  // values than slots gives the slots to its most common values and the rest are grey.
  var SLOTS = ['--c-2a78d6', '--c-eb6834', '--c-1baf7a', '--c-eda100', '--c-e87ba4', '--c-008300', '--c-6250d6', '--c-e34948'];
  var OTHER = '--c-9ba8a4';
  var PLAIN = '--c-386e6d';
  // Dot radius on screen in CSS pixels, whatever the zoom; smaller on narrow maps.
  // Many dots (no conditions yet) are drawn a little smaller so they overlap less.
  var shown = 0;
  var dotPx = function () { return (svg.clientWidth < 600 ? 2.6 : 4) * (shown > 3000 ? 0.7 : 1); };
  var WORLD = [-974.4, -487.2, 1948.8, 974.4];

  var L = null, F = null, byId = {}, cache = {}, vals = {};
  var conds = [];            // {id, shown: Set, or: bool (joined to the previous by OR)}
  var colourBy = '', colour = {};
  var svg = $('map'), layer = $('points'), card = $('card');

  function get(url) {
    if (!cache[url]) cache[url] = fetch(url).then(function (r) { if (!r.ok) throw new Error(url); return r.json(); });
    return cache[url];
  }

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }

  function load(id) {
    return id && !vals[id] ? get('data/features/f/' + id + '.json').then(function (v) { vals[id] = v; }) : Promise.resolve();
  }

  function allValues(id) { return byId[id].values.map(function (x) { return x.n; }); }

  function readURL() {
    var p = new URLSearchParams(location.search), out = [];
    p.getAll('c').forEach(function (s) {
      var or = s.charAt(0) === '|'; if (or) s = s.slice(1);
      var parts = s.split(':'), id = parts[0];
      if (!byId[id]) return;
      var keep = parts[1] ? parts[1].split(',').map(Number).filter(function (n) { return n > 0; }) : [];
      out.push({ id: id, or: or && out.length > 0, shown: new Set(keep.length ? keep : allValues(id)) });
    });
    return { conds: out, k: byId[p.get('k')] ? p.get('k') : '' };
  }

  function writeURL() {
    var p = new URLSearchParams();
    conds.forEach(function (c) {
      if (!c.id) return;
      var all = allValues(c.id), on = all.filter(function (n) { return c.shown.has(n); });
      p.append('c', (c.or ? '|' : '') + c.id + (on.length < all.length ? ':' + on.join(',') : ''));
    });
    if (colourBy) p.set('k', colourBy);
    var q = p.toString().replace(/%2C/g, ',').replace(/%3A/g, ':').replace(/%7C/g, '|');
    history.replaceState(null, '', q ? '?' + q : location.pathname);
  }

  function featureSelect(value, emptyLabel) {
    var s = el('select', { class: 'wm-feature' }), groups = {};
    s.appendChild(el('option', { value: '' }, emptyLabel));
    F.features.forEach(function (f) {
      if (!groups[f.area]) { groups[f.area] = el('optgroup', { label: f.area }); s.appendChild(groups[f.area]); }
      groups[f.area].appendChild(el('option', { value: f.id }, f.id + ' ' + f.name + ' (' + f.languages + ')'));
    });
    s.value = value || '';
    return s;
  }

  function colours(f) {
    var out = {}, vs = f.values.slice();
    var top = vs.length <= SLOTS.length ? vs : vs.slice().sort(function (x, y) { return y.count - x.count; }).slice(0, SLOTS.length - 1);
    var keep = new Set(top.map(function (x) { return x.n; })), i = 0;
    vs.forEach(function (x) { out[x.n] = keep.has(x.n) ? SLOTS[i++] : OTHER; });
    return out;
  }

  // Whether language i passes every group of conditions.
  function passes(i) {
    var groupOk = null;
    for (var j = 0; j < conds.length; j++) {
      var c = conds[j];
      if (!c.id) continue;
      var v = vals[c.id][i], ok = !!v && c.shown.has(v);
      if (groupOk === null || !c.or) {
        if (groupOk === false) return false;
        groupOk = ok;
      } else {
        groupOk = groupOk || ok;
      }
    }
    return groupOk !== false;
  }

  function draw() {
    layer.textContent = '';
    var rows = L.rows, n = 0, frag = document.createDocumentFragment();
    for (var j = 0; j < rows.length; j++) if (passes(j)) n++;
    shown = n; n = 0;
    var r = radius();
    var cv = colourBy ? vals[colourBy] : null, perValue = {};
    for (var i = 0; i < rows.length; i++) {
      if (!passes(i)) continue;
      var c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', rows[i][4]); c.setAttribute('cy', rows[i][5]); c.setAttribute('r', r);
      var v = cv ? cv[i] : 0;
      c.setAttribute('fill', 'var(' + (cv ? (v ? colour[v] : '--c-a5aeb0') : PLAIN) + ')');
      if (cv && !v) c.setAttribute('class', 'wm-nodata');
      if (cv) perValue[v] = (perValue[v] || 0) + 1;
      c.dataset.i = i;
      // Dots with no colour value go underneath.
      if (cv && !v) frag.insertBefore(c, frag.firstChild); else frag.appendChild(c);
      n++;
    }
    layer.appendChild(frag);
    $('count').textContent = 'Showing ' + n + ' of ' + rows.length + ' languages';
    colourLegend(perValue);
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
      li.appendChild(el('span', { class: 'notranslate' }, v.name));
      li.appendChild(el('small', null, String(perValue[v.n] || 0)));
      ul.appendChild(li);
    });
    if (perValue[0]) {
      var li = el('li'), dot = el('i', { class: 'wm-dot wm-dot-nodata', 'aria-hidden': 'true' });
      li.appendChild(dot); li.appendChild(el('span', null, 'No data')); li.appendChild(el('small', null, String(perValue[0])));
      ul.appendChild(li);
    }
    box.appendChild(ul);
  }

  function update() { card.hidden = true; draw(); writeURL(); }

  // One condition: feature menu, remove button, "Select all" and one checkbox per value.
  function condBox(c, idx) {
    var box = el('section', { class: 'wm-cond' });
    var head = el('div', { class: 'wm-cond-head' });
    var sel = featureSelect(c.id, 'Choose a feature');
    sel.addEventListener('change', function () {
      var id = sel.value;
      load(id).then(function () { c.id = id; c.shown = new Set(id ? allValues(id) : []); renderConds(); update(); });
    });
    head.appendChild(sel);
    var rm = el('button', { type: 'button', class: 'wm-remove', 'aria-label': 'Remove this condition' }, '×');
    rm.addEventListener('click', function () {
      conds.splice(idx, 1);
      if (conds.length) conds[0].or = false;
      renderConds(); update();
    });
    head.appendChild(rm);
    box.appendChild(head);
    if (!c.id) return box;
    var f = byId[c.id], all = allValues(c.id), boxes = [];
    var allLab = el('label', { class: 'wm-selectall' }), allCb = el('input', { type: 'checkbox' });
    allLab.appendChild(allCb); allLab.appendChild(el('span', null, 'Select all'));
    box.appendChild(allLab);
    var sync = function () {
      boxes.forEach(function (b) { b.cb.checked = c.shown.has(b.n); });
      var on = all.filter(function (n) { return c.shown.has(n); }).length;
      allCb.checked = on === all.length; allCb.indeterminate = on > 0 && on < all.length;
    };
    allCb.addEventListener('change', function () { c.shown = new Set(allCb.checked ? all : []); sync(); update(); });
    var ul = el('ul');
    f.values.forEach(function (v) {
      var li = el('li'), lab = el('label'), cb = el('input', { type: 'checkbox' });
      boxes.push({ cb: cb, n: v.n });
      cb.addEventListener('change', function () { if (cb.checked) c.shown.add(v.n); else c.shown.delete(v.n); sync(); update(); });
      lab.appendChild(cb);
      lab.appendChild(el('span', { class: 'notranslate' }, v.name));
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
          var b = el('button', { type: 'button', 'aria-pressed': String((k === 'or') === c.or) }, k === 'and' ? 'AND' : 'OR');
          b.addEventListener('click', function () { c.or = k === 'or'; renderConds(); update(); });
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
    $('no-conditions').hidden = conds.length > 0;
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
    return dotPx() * vb.width / (svg.clientWidth || 1);
  }

  function valueName(fid, n) {
    var v = byId[fid].values.filter(function (x) { return x.n === n; })[0];
    return v ? v.name : '';
  }

  function showCard(i, evt) {
    var row = L.rows[i];
    card.textContent = '';
    card.appendChild(el('h3', { class: 'notranslate' }, row[1]));
    if (row[2]) card.appendChild(el('p', { class: 'notranslate wm-sub' }, row[2]));
    var dl = el('dl');
    var seen = {};
    conds.map(function (c) { return c.id; }).concat([colourBy]).forEach(function (id) {
      if (!id || seen[id]) return;
      seen[id] = true;
      dl.appendChild(el('dt', { class: 'notranslate' }, id + ' ' + byId[id].name));
      var v = vals[id][i];
      dl.appendChild(v ? el('dd', { class: 'notranslate' }, valueName(id, v)) : el('dd', { class: 'wm-none' }, 'No data'));
    });
    card.appendChild(dl);
    var links = el('p', { class: 'wm-links' });
    links.appendChild(el('a', { href: 'record.html?id=' + encodeURIComponent(row[0]) }, 'Lang Log record'));
    if (row[3]) links.appendChild(el('a', { href: 'https://wals.info/languoid/lect/wals_code_' + encodeURIComponent(row[3]), target: '_blank', rel: 'noopener' }, 'WALS page'));
    card.appendChild(links);
    var close = el('button', { type: 'button', class: 'wm-close', 'aria-label': 'Close' }, '×');
    close.addEventListener('click', function () { card.hidden = true; });
    card.appendChild(close);
    var box = svg.parentNode.getBoundingClientRect();
    card.hidden = false;
    var x = Math.min(evt.clientX - box.left + 10, box.width - card.offsetWidth - 8);
    var y = Math.min(evt.clientY - box.top + 10, box.height - card.offsetHeight - 8);
    card.style.left = Math.max(8, x) + 'px';
    card.style.top = Math.max(8, y) + 'px';
  }

  // Zoom and pan. Temporary: to be replaced by the shared dist/map-zoom.js once it is on main.
  function zoomable(onZoom) {
    var vb = WORLD.slice(), pointers = new Map(), last = null, moved = false;
    var set = function () {
      vb[2] = Math.min(Math.max(vb[2], WORLD[2] / 60), WORLD[2]); vb[3] = vb[2] / 2;
      vb[0] = Math.min(Math.max(vb[0], WORLD[0]), WORLD[0] + WORLD[2] - vb[2]);
      vb[1] = Math.min(Math.max(vb[1], WORLD[1]), WORLD[1] + WORLD[3] - vb[3]);
      svg.setAttribute('viewBox', vb.map(function (n) { return n.toFixed(2); }).join(' '));
      onZoom();
    };
    var toMap = function (cx, cy) {
      var r = svg.getBoundingClientRect();
      return [vb[0] + (cx - r.left) / r.width * vb[2], vb[1] + (cy - r.top) / r.height * vb[3]];
    };
    var zoomAt = function (k, cx, cy) {
      var p = toMap(cx, cy), w = Math.min(Math.max(vb[2] / k, WORLD[2] / 60), WORLD[2]), s = w / vb[2];
      vb[0] = p[0] - (p[0] - vb[0]) * s; vb[1] = p[1] - (p[1] - vb[1]) * s; vb[2] = w;
      set();
    };
    var centre = function () { var r = svg.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
    svg.addEventListener('wheel', function (e) { e.preventDefault(); zoomAt(Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY); }, { passive: false });
    svg.addEventListener('pointerdown', function (e) { pointers.set(e.pointerId, [e.clientX, e.clientY]); moved = false; last = null; });
    svg.addEventListener('pointermove', function (e) {
      if (!pointers.has(e.pointerId)) return;
      var prev = pointers.get(e.pointerId);
      pointers.set(e.pointerId, [e.clientX, e.clientY]);
      var r = svg.getBoundingClientRect();
      if (pointers.size === 1) {
        var dx = e.clientX - prev[0], dy = e.clientY - prev[1];
        moved = moved || Math.abs(dx) + Math.abs(dy) > 2;
        // Capture only once the pointer drags, so a plain tap still reaches the dot under it.
        if (moved && !svg.hasPointerCapture(e.pointerId)) svg.setPointerCapture(e.pointerId);
        vb[0] -= dx / r.width * vb[2]; vb[1] -= dy / r.height * vb[3]; set();
      } else if (pointers.size === 2) {
        var p = Array.from(pointers.values()), d = Math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1]);
        if (last) zoomAt(d / last, (p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2);
        last = d; moved = true;
      }
    });
    var up = function (e) { pointers.delete(e.pointerId); last = null; };
    svg.addEventListener('pointerup', up); svg.addEventListener('pointercancel', up);
    svg.addEventListener('click', function (e) { if (moved) e.stopPropagation(); }, true);
    $('zoom-in').addEventListener('click', function () { var c = centre(); zoomAt(2, c[0], c[1]); });
    $('zoom-out').addEventListener('click', function () { var c = centre(); zoomAt(0.5, c[0], c[1]); });
    $('zoom-reset').addEventListener('click', function () { vb = WORLD.slice(); set(); });
  }


  function onZoom() {
    var r = radius(), cs = layer.childNodes;
    for (var i = 0; i < cs.length; i++) cs[i].setAttribute('r', r);
    svg.style.setProperty('--unit', String(r / dotPx()));
  }

  Promise.all([get('data/features/languages.json'), get('data/features/features.json')]).then(function (res) {
    L = res[0]; F = res[1];
    F.features.forEach(function (f) { byId[f.id] = f; });
    var s = readURL();
    conds = s.conds;
    var colourMenu = featureSelect(s.k, 'None (one colour)');
    colourMenu.id = 'colour';
    $('colour-slot').appendChild(colourMenu);
    var ids = conds.map(function (c) { return c.id; }).concat([s.k]);
    return Promise.all(ids.map(load)).then(function () { return setColour(s.k); });
  }).then(function () {
    renderConds();
    draw(); writeURL();
    zoomable(onZoom);
    window.addEventListener('resize', onZoom);
    $('colour').addEventListener('change', function () { setColour(this.value).then(update); });
    $('add-condition').addEventListener('click', function () {
      conds.push({ id: '', or: false, shown: new Set() });
      renderConds();
      var sels = document.querySelectorAll('#conditions .wm-feature');
      sels[sels.length - 1].focus();
    });
    layer.addEventListener('click', function (e) { var i = e.target.dataset && e.target.dataset.i; if (i != null) showCard(+i, e); });
  }).catch(function () {
    $('count').textContent = 'The map data could not be loaded.';
  });
})();
