// WALS feature map (wals-map.html). Data: dist/wals/ written by tools/build_wals_map.py.
// State lives in the address: ?f=<feature>&v=<shown values>&g=<second feature>&w=<its shown values>
// (v and w are left out when every value is shown).
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var NS = 'http://www.w3.org/2000/svg';
  // Categorical colours in fixed order (style.css --c-* variables). A feature with more
  // values than slots gives the slots to its most common values and the rest are grey.
  var SLOTS = ['--c-2a78d6', '--c-eb6834', '--c-1baf7a', '--c-eda100', '--c-e87ba4', '--c-008300', '--c-6250d6', '--c-e34948'];
  var OTHER = '--c-9ba8a4';
  // Dot radius on screen in CSS pixels, whatever the zoom; smaller on narrow maps.
  var dotPx = function () { return svg.clientWidth < 600 ? 2.6 : 4; };
  var WORLD = [-974.4, -487.2, 1948.8, 974.4];

  var L = null, F = null, byId = {}, cache = {};
  var a = { id: '', vals: null, shown: null, colour: {} };
  var b = { id: '', vals: null, shown: null };
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

  function readURL() {
    var p = new URLSearchParams(location.search);
    var list = function (s) { return s ? s.split(',').map(Number).filter(function (n) { return n > 0; }) : null; };
    return { f: p.get('f'), v: list(p.get('v')), g: p.get('g'), w: list(p.get('w')) };
  }

  function writeURL() {
    var p = new URLSearchParams();
    var put = function (key, s, all) { var on = all.filter(function (n) { return s.shown.has(n); }); if (on.length < all.length) p.set(key, on.join(',')); };
    p.set('f', a.id);
    put('v', a, byId[a.id].values.map(function (x) { return x.n; }));
    if (b.id) { p.set('g', b.id); put('w', b, byId[b.id].values.map(function (x) { return x.n; })); }
    history.replaceState(null, '', '?' + p.toString().replace(/%2C/g, ','));
  }

  function fillSelects() {
    var s1 = $('feature'), s2 = $('feature2'), groups = {};
    F.features.forEach(function (f) {
      if (!groups[f.area]) {
        groups[f.area] = [el('optgroup', { label: f.area }), el('optgroup', { label: f.area })];
        s1.appendChild(groups[f.area][0]); s2.appendChild(groups[f.area][1]);
      }
      var label = f.id + ' ' + f.name + ' (' + f.languages + ')';
      groups[f.area][0].appendChild(el('option', { value: f.id }, label));
      groups[f.area][1].appendChild(el('option', { value: f.id }, label));
    });
  }

  function colours(f) {
    var out = {}, vals = f.values.slice();
    var top = vals.length <= SLOTS.length ? vals : vals.slice().sort(function (x, y) { return y.count - x.count; }).slice(0, SLOTS.length - 1);
    var keep = new Set(top.map(function (x) { return x.n; })), i = 0;
    vals.forEach(function (x) { out[x.n] = keep.has(x.n) ? SLOTS[i++] : OTHER; });
    return out;
  }

  // The legend is the filter: one checkbox per value, and a "Select all" box above them
  // (checked, unchecked or mixed). Double-click a row, or press and hold it on a touch
  // screen, to keep only that value (as in Plotly's legends).
  var HOLD_MS = 500;
  function legend(box, f, state, coloured) {
    box.textContent = '';
    var all = f.values.map(function (x) { return x.n; }), boxes = [];
    box.appendChild(el('h2', { class: 'notranslate' }, f.id + ' ' + f.name));
    var allLab = el('label', { class: 'wm-selectall' }), allCb = el('input', { type: 'checkbox' });
    allLab.appendChild(allCb); allLab.appendChild(el('span', null, 'Select all'));
    box.appendChild(allLab);
    var sync = function () {
      boxes.forEach(function (b) { b.cb.checked = state.shown.has(b.n); });
      var on = all.filter(function (n) { return state.shown.has(n); }).length;
      allCb.checked = on === all.length; allCb.indeterminate = on > 0 && on < all.length;
    };
    var only = function (n) { state.shown = new Set([n]); sync(); update(); };
    allCb.addEventListener('change', function () { state.shown = new Set(allCb.checked ? all : []); sync(); update(); });
    var ul = el('ul');
    f.values.forEach(function (v) {
      var li = el('li'), lab = el('label', { title: 'Double-click or press and hold to show only this value' });
      var cb = el('input', { type: 'checkbox' });
      boxes.push({ cb: cb, n: v.n });
      cb.addEventListener('change', function () { if (cb.checked) state.shown.add(v.n); else state.shown.delete(v.n); sync(); update(); });
      lab.appendChild(cb);
      var dot = el('i', { class: coloured ? 'wm-dot' : 'wm-dot wm-ring', 'aria-hidden': 'true' });
      if (coloured) dot.style.background = 'var(' + a.colour[v.n] + ')';
      lab.appendChild(dot);
      lab.appendChild(el('span', { class: 'notranslate' }, v.name));
      lab.appendChild(el('small', null, String(v.count)));
      lab.addEventListener('dblclick', function (e) { e.preventDefault(); only(v.n); });
      var timer = null, held = false;
      lab.addEventListener('pointerdown', function (e) {
        if (e.pointerType === 'mouse') return;
        held = false;
        timer = setTimeout(function () { held = true; only(v.n); if (navigator.vibrate) navigator.vibrate(15); }, HOLD_MS);
      });
      var cancel = function () { clearTimeout(timer); };
      lab.addEventListener('pointerup', cancel); lab.addEventListener('pointercancel', cancel); lab.addEventListener('pointerleave', cancel);
      lab.addEventListener('contextmenu', function (e) { if (held || timer) e.preventDefault(); });
      lab.addEventListener('click', function (e) { if (held) { e.preventDefault(); held = false; } });
      li.appendChild(lab);
      ul.appendChild(li);
    });
    box.appendChild(ul);
    box.appendChild(el('p', { class: 'wm-tip' }, 'Double-click a row, or press and hold it, to show only that value.'));
    sync();
  }

  function radius() {
    var vb = svg.viewBox.baseVal;
    return dotPx() * vb.width / (svg.clientWidth || 1);
  }

  function draw() {
    layer.textContent = '';
    var rows = L.rows, r = radius(), n = 0, frag = document.createDocumentFragment();
    for (var i = 0; i < rows.length; i++) {
      var v = a.vals[i];
      if (!v || !a.shown.has(v)) continue;
      if (b.id) { var w = b.vals[i]; if (!w || !b.shown.has(w)) continue; }
      var c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', rows[i][5]); c.setAttribute('cy', rows[i][6]); c.setAttribute('r', r);
      c.setAttribute('fill', 'var(' + a.colour[v] + ')');
      c.dataset.i = i;
      frag.appendChild(c);
      n++;
    }
    layer.appendChild(frag);
    var total = a.vals.filter(function (x, i) { return x && (!b.id || b.vals[i]); }).length;
    $('count').textContent = 'Showing ' + n + ' of ' + total + ' languages';
  }

  function update() { card.hidden = true; draw(); writeURL(); }

  function setFeature(state, id, shown) {
    var f = byId[id];
    state.id = id;
    state.shown = new Set(shown && shown.length ? shown : f.values.map(function (x) { return x.n; }));
    return get('wals/f/' + id + '.json').then(function (vals) { state.vals = vals; });
  }

  function render() {
    a.colour = colours(byId[a.id]);
    legend($('legend1'), byId[a.id], a, true);
    $('legend2').hidden = !b.id;
    if (b.id) legend($('legend2'), byId[b.id], b, false);
    update();
  }

  function valueName(fid, n) {
    var v = byId[fid].values.filter(function (x) { return x.n === n; })[0];
    return v ? v.name : '';
  }

  function showCard(i, evt) {
    var row = L.rows[i];
    card.textContent = '';
    card.appendChild(el('h3', { class: 'notranslate' }, row[1]));
    card.appendChild(el('p', { class: 'notranslate wm-sub' }, [row[2], row[3]].filter(Boolean).join(' · ')));
    var dl = el('dl');
    [[a.id, a.vals[i]], [b.id, b.id && b.vals[i]]].forEach(function (p) {
      if (!p[0]) return;
      dl.appendChild(el('dt', { class: 'notranslate' }, p[0] + ' ' + byId[p[0]].name));
      dl.appendChild(el('dd', { class: 'notranslate' }, valueName(p[0], p[1])));
    });
    card.appendChild(dl);
    var links = el('p', { class: 'wm-links' });
    links.appendChild(el('a', { href: 'https://wals.info/languoid/lect/wals_code_' + encodeURIComponent(row[0]), target: '_blank', rel: 'noopener' }, 'WALS page'));
    if (row[4]) links.appendChild(el('a', { href: 'record.html?id=' + encodeURIComponent(row[4]) }, 'Lang Log record'));
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

  Promise.all([get('wals/languages.json'), get('wals/features.json')]).then(function (res) {
    L = res[0]; F = res[1];
    F.features.forEach(function (f) { byId[f.id] = f; });
    fillSelects();
    var s = readURL();
    var f1 = byId[s.f] ? s.f : '81A', f2 = byId[s.g] && s.g !== f1 ? s.g : '';
    $('feature').value = f1; $('feature2').value = f2;
    var jobs = [setFeature(a, f1, s.v)];
    if (f2) jobs.push(setFeature(b, f2, s.w));
    return Promise.all(jobs);
  }).then(function () {
    render();
    zoomable(onZoom);
    window.addEventListener('resize', onZoom);
    $('feature').addEventListener('change', function () {
      var id = this.value;
      if (id === b.id) { b.id = ''; $('feature2').value = ''; }
      setFeature(a, id).then(render);
    });
    $('feature2').addEventListener('change', function () {
      var id = this.value;
      if (!id || id === a.id) { b.id = ''; this.value = ''; render(); return; }
      setFeature(b, id).then(render);
    });
    layer.addEventListener('click', function (e) { var i = e.target.dataset && e.target.dataset.i; if (i != null) showCard(+i, e); });
  }).catch(function () {
    $('count').textContent = 'The map data could not be loaded.';
  });
})();
