// Zoom and pan for the maps drawn by tools/languoid_map.py (svg.lmap on the record pages)
// and for the language feature map. Without JavaScript the map is a still picture; this
// script only adds movement.
//
// - The map goes round the world: dragging east or west never reaches an edge. The
//   background is drawn three times side by side (the world and one copy on each side),
//   the view's centre is kept on the middle copy, and every point is moved to the copy
//   nearest the centre of the view. North and south the map ends, as on other web maps.
// - Drag (mouse or one finger), pinch, Ctrl/Cmd + wheel or trackpad pinch, double click,
//   the + / - buttons (only with a mouse or trackpad), Reset, and the keyboard
//   (+ - arrows 0) move the view. Reset and the buttons glide to the new view instead of
//   jumping, unless the visitor asked for reduced motion.
// - Points keep their size on screen at every zoom (their r is rescaled), and border lines
//   keep their width (vector-effect in the map files), so nothing grows blurry or blobby.
// - Once the view is narrower than TILE_BELOW, the 1:10m tiles in map/tiles/<name>/ for the
//   part in view are drawn over the 1:50m world map (see tools/build_land.py).
//
// Other pages can reuse it: window.LangLogMap.mount(svg) on an <svg> with the attributes
// languoid_map.py writes (viewBox, data-map, data-base, data-min, data-world). The svg receives an
// "lmap:view" event, detail {k, x, y, w, h}, after every change; k is the view width
// divided by the starting width, so a point of radius r0 should be drawn at r0 * k. A page
// that adds or replaces points after mounting calls refresh() on the object mount returns.
(function () {
  'use strict';
  var TILE_BELOW = 700;          // view width (SVG units) below which tiles are drawn
  var LAYERS = [['sphere', 'lmap-sphere'], ['land', 'lmap-land'], ['borders', 'lmap-border'], ['disputed', 'lmap-disputed']];
  var TILE_LAYERS = [['sea', 'lmap-sphere'], ['land', 'lmap-land'], ['borders', 'lmap-border'], ['disputed', 'lmap-disputed']];
  var STEP = 1.6;                 // zoom factor of one button press or key press
  var GLIDE_MS = 550;             // length of the Reset animation
  var STEP_MS = 220;              // length of the + / - animation
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

  function reducedMotion() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

  function mount(svg) {
    if (svg.__lmap) return svg.__lmap;
    var vb = svg.viewBox.baseVal;
    var home = { x: vb.x, y: vb.y, w: vb.width, h: vb.height };
    var aspect = home.w / home.h;
    var name = svg.getAttribute('data-map') || 'land';
    var base = svg.getAttribute('data-base') || 'map/';
    var minW = parseFloat(svg.getAttribute('data-min')) || 30;
    var wb = (svg.getAttribute('data-world') || '-973.9 -973.9 1947.8 1947.8').split(' ').map(parseFloat);
    var world = { x: wb[0], y: wb[1], w: wb[2], h: wb[3] };
    var W = world.w;
    // The starting view may lie east of the 180th meridian (languoid_map.py keeps a group of
    // points together); measure it on the middle copy of the world, as clamp() does.
    home.x -= W * Math.floor((home.x + home.w / 2 - world.x) / W);
    var view = { x: home.x, y: home.y, w: home.w, h: home.h };
    var raf = 0, glide = 0;

    // Background: every layer three times, one world apart.
    var bg = svg.querySelector('.lmap-bg');
    if (!bg) {
      bg = el('g', { 'class': 'lmap-bg' });
      svg.insertBefore(bg, svg.querySelector(':scope > use'));
    }
    var hrefs = {};
    Array.prototype.forEach.call(svg.querySelectorAll(':scope > use, .lmap-bg > use'), function (u) {
      hrefs[u.getAttribute('class')] = u.getAttribute('href').split('#')[0];
      u.parentNode.removeChild(u);
    });
    LAYERS.forEach(function (p) {
      var href = hrefs[p[1]] || base + name + '.svg';
      [-1, 0, 1].forEach(function (k) {
        var u = el('use', { href: href + '#' + p[0], 'class': p[1] });
        if (k) u.setAttribute('x', k * W);
        bg.appendChild(u);
      });
    });
    var tiles = el('g', { 'class': 'lmap-tiles' });
    TILE_LAYERS.forEach(function () { tiles.appendChild(el('g', {})); });
    // Tiles cover the whole world map under them, borders included, and carry their own.
    bg.appendChild(tiles);
    var shown = {};

    // Points: the radius of the ones written in the page, and their own x.
    var scaled = Array.prototype.map.call(svg.querySelectorAll('.lmap-ctx circle, .lmap-main circle, .lmap-self circle'), function (c) {
      return [c, parseFloat(c.getAttribute('r'))];
    });
    var points = null;
    function allPoints() {
      if (!points) {
        points = Array.prototype.slice.call(svg.querySelectorAll('circle'));
        points.forEach(function (c) {
          if (c.__x0 === undefined) { c.__x0 = parseFloat(c.getAttribute('cx')); c.__k = 0; }
        });
      }
      return points;
    }

    var inset = svg.querySelector('.lmap-inset > svg');
    var insetRects = inset ? Array.prototype.slice.call(inset.querySelectorAll('rect')) : [];
    if (inset && insetRects.length === 1) {
      insetRects.push(insetRects[0].cloneNode(false));
      inset.appendChild(insetRects[1]);
    }

    function clamp() {
      view.w = Math.min(Math.max(view.w, minW), W);
      view.h = view.w / aspect;
      // East and west: keep the centre on the middle copy of the world.
      var c = view.x + view.w / 2;
      view.x -= W * Math.floor((c - world.x) / W);
      if (view.h >= world.h) view.y = world.y + (world.h - view.h) / 2;
      else view.y = Math.min(Math.max(view.y, world.y), world.y + world.h - view.h);
    }

    function draw() {
      raf = 0;
      svg.setAttribute('viewBox', [view.x, view.y, view.w, view.h].map(function (v) { return +v.toFixed(2); }).join(' '));
      var k = view.w / home.w;
      for (var i = 0; i < scaled.length; i++) scaled[i][0].setAttribute('r', +(scaled[i][1] * k).toFixed(3));
      // Each point goes to the copy of the world nearest the centre of the view.
      var cx = view.x + view.w / 2, ps = allPoints();
      for (var j = 0; j < ps.length; j++) {
        var p = ps[j], n = Math.round((cx - p.__x0) / W);
        if (n !== p.__k) { p.__k = n; p.setAttribute('cx', +(p.__x0 + n * W).toFixed(2)); }
      }
      if (inset) {
        var show = view.w < W * 0.5;
        inset.parentNode.style.display = show ? '' : 'none';
        if (show) {
          var iw = view.w * 0.22, ih = iw / 2;
          inset.setAttribute('x', view.x + view.w - iw - view.w * 0.015);
          inset.setAttribute('y', view.y + view.h - ih - view.w * 0.015);
          inset.setAttribute('width', iw);
          inset.setAttribute('height', ih);
          var nx = view.x - W * Math.floor((view.x - world.x) / W);
          insetRects.forEach(function (r, i) {
            r.setAttribute('x', nx - i * W); r.setAttribute('y', view.y);
            r.setAttribute('width', view.w); r.setAttribute('height', view.h);
          });
        }
      }
      var moved = Math.abs(view.w - home.w) > 0.01 || Math.abs(view.x - home.x) > 0.01 || Math.abs(view.y - home.y) > 0.01;
      svg.classList.toggle('lmap-moved', moved);
      svg.classList.toggle('lmap-in', view.w < home.w - 0.01);
      updateTiles();
      svg.dispatchEvent(new CustomEvent('lmap:view', { detail: { k: k, x: view.x, y: view.y, w: view.w, h: view.h } }));
    }

    function schedule() { clamp(); if (!raf) raf = requestAnimationFrame(draw); }

    function updateTiles() {
      if (view.w >= TILE_BELOW) { tiles.style.display = 'none'; return; }
      tiles.style.display = '';
      loadManifest(base, function (m) {
        var have = m.tiles[name] || [];
        var gx = m.grid[0], gy = m.grid[1], b = m.bounds, tw = b[2] / gx, th = b[3] / gy;
        // Columns run on past the edge of the world; column c is tile c mod gx, one world over.
        var c0 = Math.floor((view.x - b[0]) / tw), c1 = Math.floor((view.x + view.w - b[0]) / tw);
        var r0 = Math.max(0, Math.floor((view.y - b[1]) / th)), r1 = Math.min(gy - 1, Math.floor((view.y + view.h - b[1]) / th));
        for (var c = c0; c <= c1; c++) for (var r = r0; r <= r1; r++) {
          var col = ((c % gx) + gx) % gx, shift = Math.floor(c / gx) * b[2];
          var id = col + '-' + r, key = id + '@' + Math.round(shift);
          if (shown[key] || have.indexOf(id) < 0) continue;
          shown[key] = true;
          var href = base + 'tiles/' + name + '/' + id + '.svg';
          // One group per layer, so no tile's sea covers the edge of its neighbour's land.
          TILE_LAYERS.forEach(function (p, i) {
            var u = el('use', { href: href + '#' + p[0], 'class': p[1] });
            if (shift) u.setAttribute('x', shift);
            tiles.childNodes[i].appendChild(u);
          });
        }
      });
    }

    function stop() { if (glide) { cancelAnimationFrame(glide); glide = 0; } }

    // Move smoothly to the view {x, y, w}: the centre slides along the shorter way round
    // the world while the width changes at an even rate of zoom.
    function glideTo(to, ms) {
      stop();
      to.w = Math.min(Math.max(to.w, minW), W);
      if (reducedMotion()) { view = { x: to.x, y: to.y, w: to.w, h: to.w / aspect }; schedule(); return; }
      var fw = view.w, tw = to.w;
      var fx = view.x + view.w / 2, tx = to.x + to.w / 2;
      fx -= W * Math.round((fx - tx) / W);
      var fy = view.y + view.h / 2, ty = to.y + to.w / aspect / 2;
      var t0 = performance.now();
      function frame(now) {
        var t = Math.min(1, (now - t0) / ms), e = ease(t);
        var w = Math.exp(Math.log(fw) + (Math.log(tw) - Math.log(fw)) * e);
        var cx = fx + (tx - fx) * e, cy = fy + (ty - fy) * e;
        view = { x: cx - w / 2, y: cy - w / aspect / 2, w: w, h: w / aspect };
        clamp();
        draw();
        glide = t < 1 ? requestAnimationFrame(frame) : 0;
      }
      glide = requestAnimationFrame(frame);
    }

    // The view after zooming by factor f (>1 zooms in) keeping the SVG point (px, py) where it is.
    function zoomed(f, px, py) {
      if (px === undefined) { px = view.x + view.w / 2; py = view.y + view.h / 2; }
      var w = Math.min(Math.max(view.w / f, minW), W);
      var s = w / view.w;
      return { x: px - (px - view.x) * s, y: py - (py - view.y) * s, w: w };
    }
    function zoom(f, px, py) {
      stop();
      var v = zoomed(f, px, py);
      view.x = v.x; view.y = v.y; view.w = v.w;
      schedule();
    }
    function zoomSmooth(f) { glideTo(zoomed(f), STEP_MS); }

    function toSvg(clientX, clientY) {
      var r = svg.getBoundingClientRect();
      // preserveAspectRatio meet: the view fills the box when the box has the same aspect.
      var scale = Math.max(view.w / r.width, view.h / r.height);
      var ox = (r.width - view.w / scale) / 2, oy = (r.height - view.h / scale) / 2;
      return [view.x + (clientX - r.left - ox) * scale, view.y + (clientY - r.top - oy) * scale, scale];
    }

    function reset() { glideTo({ x: home.x, y: home.y, w: home.w }, GLIDE_MS); }

    // Pointers: one pans (a finger too, from the start: touch-action is none on the map,
    // so the page scrolls from outside the map), two pinch.
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
      stop();
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
      var a = pts[ids[0]], b = pts[ids[1]] || a;
      var mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      var f = ids.length > 1 ? Math.hypot(a[0] - b[0], a[1] - b[1]) / start.dist : 1;
      var w = Math.min(Math.max(start.view.w / f, minW), W), s = w / start.view.w;
      var scale = start.at[2] * s;
      view.w = w;
      view.x = start.at[0] - (start.at[0] - start.view.x) * s - (mid[0] - start.mid[0]) * scale;
      view.y = start.at[1] - (start.at[1] - start.view.y) * s - (mid[1] - start.mid[1]) * scale;
      schedule();
      e.preventDefault();
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
    svg.addEventListener('gesturestart', function (e) { e.preventDefault(); stop(); g0 = { w: view.w, at: toSvg(e.clientX, e.clientY) }; });
    svg.addEventListener('gesturechange', function (e) {
      if (!g0) return;
      e.preventDefault();
      var w = Math.min(Math.max(g0.w / e.scale, minW), W);
      zoom(view.w / w, g0.at[0], g0.at[1]);
    });
    svg.addEventListener('gestureend', function () { g0 = null; });
    svg.addEventListener('dblclick', function (e) {
      var p = toSvg(e.clientX, e.clientY);
      glideTo(zoomed(e.shiftKey ? 1 / STEP : STEP, p[0], p[1]), STEP_MS);
    });
    svg.setAttribute('tabindex', '0');
    svg.addEventListener('keydown', function (e) {
      var d = view.w * 0.15, used = true;
      if (e.key === '+' || e.key === '=') zoomSmooth(STEP);
      else if (e.key === '-' || e.key === '_') zoomSmooth(1 / STEP);
      else if (e.key === '0') reset();
      else if (e.key === 'ArrowLeft') { stop(); view.x -= d; schedule(); }
      else if (e.key === 'ArrowRight') { stop(); view.x += d; schedule(); }
      else if (e.key === 'ArrowUp') { stop(); view.y -= d; schedule(); }
      else if (e.key === 'ArrowDown') { stop(); view.y += d; schedule(); }
      else used = false;
      if (used) e.preventDefault();
    });

    // Buttons, placed over the top right corner of the map.
    var bar = document.createElement('div');
    bar.className = 'lmap-tools';
    // + and - only where a mouse or trackpad exists; on phones and tablets people pinch.
    var fine = !window.matchMedia || window.matchMedia('(any-pointer: fine)').matches;
    (fine ? [['+', 'Zoom in', function () { zoomSmooth(STEP); }], ['−', 'Zoom out', function () { zoomSmooth(1 / STEP); }]] : [])
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

    var api = {
      svg: svg, zoom: zoom, reset: reset,
      refresh: function () { points = null; schedule(); },
      view: function () { return { x: view.x, y: view.y, w: view.w, h: view.h }; }
    };
    svg.__lmap = api;
    schedule();
    return api;
  }

  window.LangLogMap = { mount: mount };
  function all() { Array.prototype.forEach.call(document.querySelectorAll('svg.lmap[data-map]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
