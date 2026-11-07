// Zoom and pan for the maps drawn by tools/languoid_map.py (svg.lmap on the record pages).
// Without JavaScript the map is a still picture; this script only adds movement.
//
// - Drag (mouse or one finger once zoomed in), pinch, Ctrl/Cmd + wheel or trackpad pinch,
//   double click, the + / - buttons (only with a mouse or trackpad), Reset, and the keyboard (+ - arrows 0) move the view.
// - Points keep their size on screen at every zoom (their r is rescaled), and border lines
//   keep their width (vector-effect in the map files), so nothing grows blurry or blobby.
// - Once the view is narrower than TILE_BELOW, the 1:10m tiles in map/tiles/<name>/ for the
//   part in view are drawn over the 1:50m world map (see tools/build_land.py), once the
//   visitor has zoomed in past the starting view.
//
// Other pages can reuse it: window.LangLogMap.mount(svg) on an <svg> with the attributes
// languoid_map.py writes (viewBox, data-map, data-base, data-min, data-world). The svg receives an
// "lmap:view" event, detail {k, x, y, w, h}, after every change; k is the view width
// divided by the starting width, so a point of radius r0 should be drawn at r0 * k.
(function () {
  'use strict';
  var TILE_BELOW = 300;          // view width (SVG units) below which tiles are drawn, once zoomed in
  var LAYERS = [['sea', 'lmap-sphere'], ['land', 'lmap-land'], ['borders', 'lmap-border'], ['disputed', 'lmap-disputed']];
  var STEP = 1.6;                 // zoom factor of one button press or key press
  var manifest = null, manifestWait = [];

  function loadManifest(base, done) {
    if (manifest) return done(manifest);
    manifestWait.push(done);
    if (manifestWait.length > 1) return;
    fetch(base + 'tiles.json').then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (m) {
        manifest = m || { grid: [1, 1], bounds: [0, 0, 1, 1], tiles: {} };
        manifestWait.splice(0).forEach(function (f) { f(manifest); });
      });
  }

  function el(name, attrs) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }

  function mount(svg) {
    if (svg.__lmap) return svg.__lmap;
    var vb = svg.viewBox.baseVal;
    var home = { x: vb.x, y: vb.y, w: vb.width, h: vb.height };
    var aspect = home.w / home.h;
    var name = svg.getAttribute('data-map') || 'land';
    var base = svg.getAttribute('data-base') || 'map/';
    var minW = parseFloat(svg.getAttribute('data-min')) || 30;
    var wb = (svg.getAttribute('data-world') || '-974.4 -487.2 1948.8 974.4').split(' ').map(parseFloat);
    var world = { x: wb[0], y: wb[1], w: wb[2], h: wb[3] };
    var view = { x: home.x, y: home.y, w: home.w, h: home.h };
    var raf = 0;

    var circles = Array.prototype.filter.call(svg.querySelectorAll('circle'), function (c) {
      return !c.closest('.lmap-inset');
    }).map(function (c) { return [c, parseFloat(c.getAttribute('r'))]; });
    var inset = svg.querySelector('.lmap-inset > svg');
    var insetRect = inset && inset.querySelector('rect');
    var tiles = el('g', { 'class': 'lmap-tiles' });
    LAYERS.forEach(function () { tiles.appendChild(el('g', {})); });
    var lastBase = svg.querySelectorAll(':scope > use');
    lastBase = lastBase[lastBase.length - 1];
    svg.insertBefore(tiles, lastBase ? lastBase.nextSibling : svg.firstChild);
    var shown = {};

    function clamp() {
      view.w = Math.min(Math.max(view.w, minW), world.w);
      view.h = view.w / aspect;
      if (view.w >= world.w) view.x = world.x;
      else view.x = Math.min(Math.max(view.x, world.x), world.x + world.w - view.w);
      if (view.h >= world.h) view.y = world.y + (world.h - view.h) / 2;
      else view.y = Math.min(Math.max(view.y, world.y), world.y + world.h - view.h);
    }

    function draw() {
      raf = 0;
      svg.setAttribute('viewBox', [view.x, view.y, view.w, view.h].map(function (v) { return +v.toFixed(2); }).join(' '));
      var k = view.w / home.w;
      for (var i = 0; i < circles.length; i++) circles[i][0].setAttribute('r', +(circles[i][1] * k).toFixed(3));
      if (inset) {
        var show = view.w < world.w * 0.5;
        inset.parentNode.style.display = show ? '' : 'none';
        if (show) {
          var iw = view.w * 0.22, ih = iw / 2;
          inset.setAttribute('x', view.x + view.w - iw - view.w * 0.015);
          inset.setAttribute('y', view.y + view.h - ih - view.w * 0.015);
          inset.setAttribute('width', iw);
          inset.setAttribute('height', ih);
          insetRect.setAttribute('x', view.x); insetRect.setAttribute('y', view.y);
          insetRect.setAttribute('width', view.w); insetRect.setAttribute('height', view.h);
        }
      }
      var zoomed = Math.abs(view.w - home.w) > 0.01 || Math.abs(view.x - home.x) > 0.01 || Math.abs(view.y - home.y) > 0.01;
      svg.classList.toggle('lmap-moved', zoomed);
      svg.classList.toggle('lmap-in', view.w < home.w - 0.01);
      updateTiles();
      svg.dispatchEvent(new CustomEvent('lmap:view', { detail: { k: k, x: view.x, y: view.y, w: view.w, h: view.h } }));
    }

    function schedule() { clamp(); if (!raf) raf = requestAnimationFrame(draw); }

    function updateTiles() {
      // Only after the visitor zooms in, so opening a page never downloads tiles.
      if (view.w >= TILE_BELOW || view.w >= home.w - 0.01) { tiles.style.display = 'none'; return; }
      tiles.style.display = '';
      loadManifest(base, function (m) {
        var have = m.tiles[name] || [];
        var gx = m.grid[0], gy = m.grid[1], b = m.bounds, tw = b[2] / gx, th = b[3] / gy;
        var c0 = Math.max(0, Math.floor((view.x - b[0]) / tw)), c1 = Math.min(gx - 1, Math.floor((view.x + view.w - b[0]) / tw));
        var r0 = Math.max(0, Math.floor((view.y - b[1]) / th)), r1 = Math.min(gy - 1, Math.floor((view.y + view.h - b[1]) / th));
        for (var c = c0; c <= c1; c++) for (var r = r0; r <= r1; r++) {
          var id = c + '-' + r;
          if (shown[id] || have.indexOf(id) < 0) continue;
          shown[id] = true;
          var href = base + 'tiles/' + name + '/' + id + '.svg';
          // One group per layer, so no tile's sea covers the edge of its neighbour's land.
          LAYERS.forEach(function (p, i) {
            tiles.childNodes[i].appendChild(el('use', { href: href + '#' + p[0], 'class': p[1] }));
          });
        }
      });
    }

    // Zoom by factor f (>1 zooms in) keeping the SVG point (px, py) where it is.
    function zoom(f, px, py) {
      if (px === undefined) { px = view.x + view.w / 2; py = view.y + view.h / 2; }
      var w = Math.min(Math.max(view.w / f, minW), world.w);
      var s = w / view.w;
      view.x = px - (px - view.x) * s;
      view.y = py - (py - view.y) * s;
      view.w = w;
      schedule();
    }

    function toSvg(clientX, clientY) {
      var r = svg.getBoundingClientRect();
      // preserveAspectRatio meet: the view fills the box when the box has the same aspect.
      var scale = Math.max(view.w / r.width, view.h / r.height);
      var ox = (r.width - view.w / scale) / 2, oy = (r.height - view.h / scale) / 2;
      return [view.x + (clientX - r.left - ox) * scale, view.y + (clientY - r.top - oy) * scale, scale];
    }

    function reset() { view = { x: home.x, y: home.y, w: home.w, h: home.h }; schedule(); }

    // Pointers: one pans, two pinch.
    var pts = {}, start = null;
    function snapshot() {
      var ids = Object.keys(pts);
      if (!ids.length) { start = null; return; }
      var a = pts[ids[0]], b = pts[ids[1]] || a;
      start = { n: ids.length, view: { x: view.x, y: view.y, w: view.w }, mid: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2],
        dist: Math.hypot(a[0] - b[0], a[1] - b[1]) || 1 };
      start.at = toSvg(start.mid[0], start.mid[1]);
    }
    svg.addEventListener('pointerdown', function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      // At the starting view a single finger keeps scrolling the page (touch-action: pan-y).
      if (e.pointerType === 'touch' && !svg.classList.contains('lmap-in') && !Object.keys(pts).length) {
        pts[e.pointerId] = [e.clientX, e.clientY]; snapshot(); return;
      }
      pts[e.pointerId] = [e.clientX, e.clientY];
      try { svg.setPointerCapture(e.pointerId); } catch (_) {}
      svg.classList.add('lmap-drag');
      snapshot();
    });
    svg.addEventListener('pointermove', function (e) {
      if (!pts[e.pointerId] || !start) return;
      pts[e.pointerId] = [e.clientX, e.clientY];
      var ids = Object.keys(pts);
      if (start.n !== ids.length) snapshot();
      if (ids.length === 1 && e.pointerType === 'touch' && !svg.classList.contains('lmap-in')) return;
      var a = pts[ids[0]], b = pts[ids[1]] || a;
      var mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      var f = ids.length > 1 ? Math.hypot(a[0] - b[0], a[1] - b[1]) / start.dist : 1;
      var w = Math.min(Math.max(start.view.w / f, minW), world.w), s = w / start.view.w;
      var scale = start.at[2] * s;
      view.w = w;
      view.x = start.at[0] - (start.at[0] - start.view.x) * s - (mid[0] - start.mid[0]) * scale;
      view.y = start.at[1] - (start.at[1] - start.view.y) * s - (mid[1] - start.mid[1]) * scale;
      schedule();
      if (ids.length > 1 || e.pointerType !== 'touch' || svg.classList.contains('lmap-in')) e.preventDefault();
    });
    function up(e) {
      delete pts[e.pointerId];
      if (!Object.keys(pts).length) svg.classList.remove('lmap-drag');
      snapshot();
    }
    svg.addEventListener('pointerup', up);
    svg.addEventListener('pointercancel', up);
    svg.addEventListener('wheel', function (e) {
      // Plain wheel scrolls the page; Ctrl/Cmd + wheel (and trackpad pinch, which browsers
      // report as Ctrl + wheel) zooms the map.
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      var p = toSvg(e.clientX, e.clientY);
      zoom(Math.exp(-e.deltaY * (e.deltaMode === 1 ? 0.05 : 0.0025)), p[0], p[1]);
    }, { passive: false });
    // Safari trackpad pinch.
    var g0 = null;
    svg.addEventListener('gesturestart', function (e) { e.preventDefault(); g0 = { w: view.w, at: toSvg(e.clientX, e.clientY) }; });
    svg.addEventListener('gesturechange', function (e) {
      if (!g0) return;
      e.preventDefault();
      var w = Math.min(Math.max(g0.w / e.scale, minW), world.w);
      zoom(view.w / w, g0.at[0], g0.at[1]);
    });
    svg.addEventListener('gestureend', function () { g0 = null; });
    svg.addEventListener('dblclick', function (e) {
      var p = toSvg(e.clientX, e.clientY);
      zoom(e.shiftKey ? 1 / STEP : STEP, p[0], p[1]);
    });
    svg.setAttribute('tabindex', '0');
    svg.addEventListener('keydown', function (e) {
      var d = view.w * 0.15, used = true;
      if (e.key === '+' || e.key === '=') zoom(STEP);
      else if (e.key === '-' || e.key === '_') zoom(1 / STEP);
      else if (e.key === '0') reset();
      else if (e.key === 'ArrowLeft') { view.x -= d; schedule(); }
      else if (e.key === 'ArrowRight') { view.x += d; schedule(); }
      else if (e.key === 'ArrowUp') { view.y -= d; schedule(); }
      else if (e.key === 'ArrowDown') { view.y += d; schedule(); }
      else used = false;
      if (used) e.preventDefault();
    });

    // Buttons, placed over the top right corner of the map.
    var bar = document.createElement('div');
    bar.className = 'lmap-tools';
    // + and - only where a mouse or trackpad exists; on phones and tablets people pinch.
    var fine = !window.matchMedia || window.matchMedia('(any-pointer: fine)').matches;
    (fine ? [['+', 'Zoom in', function () { zoom(STEP); }], ['−', 'Zoom out', function () { zoom(1 / STEP); }]] : [])
      .concat([['Reset', 'Reset view', reset]]).forEach(function (b) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = b[0];
      btn.setAttribute('aria-label', b[1]);
      btn.title = b[1];
      btn.addEventListener('click', b[2]);
      if (b[0] === 'Reset') btn.className = 'lmap-reset';
      bar.appendChild(btn);
    });
    var host = svg.parentNode;
    var wrap = document.createElement('div');
    wrap.className = 'lmap-wrap';
    host.insertBefore(wrap, svg);
    wrap.appendChild(svg);
    wrap.appendChild(bar);

    var api = { svg: svg, zoom: zoom, reset: reset, view: function () { return { x: view.x, y: view.y, w: view.w, h: view.h }; } };
    svg.__lmap = api;
    return api;
  }

  window.LangLogMap = { mount: mount };
  function all() { Array.prototype.forEach.call(document.querySelectorAll('svg.lmap[data-map]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
