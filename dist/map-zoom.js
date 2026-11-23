// Zoom and pan for the maps drawn by tools/languoid_map.py (svg.lmap on the record pages)
// and for the map view of the top page (dist/explore.js). Without JavaScript the map is a still picture; this
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
// - Points keep one size on screen at every zoom and in the map view, by one rule on every
//   map (pointPx()): a member point has radius POINT_PX in CSS pixels, smaller on a narrow
//   map and when many points are shown. The other points keep their size relative to it
//   (data-r on the svg is the member radius languoid_map.py wrote; without it, as on the top
//   page, every point is a member point). Border lines keep their width (vector-effect in
//   the map files), so nothing grows blurry or blobby.
// - The locator (languoid_map.py) shows the whole world in the corner while the view is
//   narrower than half the world, on every map.
// - Once the view is narrower than TILE_BELOW, the 1:10m tiles in map/tiles/<name>/ for the
//   part in view are drawn over the 1:50m world map (see tools/build_land.py).
// - The three copies of the world and the 1:10m tiles overlap their neighbours with the
//   same land and sea (tools/build_land.py makes them so), so no seam shows between them
//   and nothing is outlined to hide one. The copies draw the sea that reaches into the
//   neighbours (#sea) instead of the square world (#sphere).
//
// - Map view: the button in the corner opens the map over the whole window, with nothing
//   else on screen; the close button, Esc or the browser's Back button closes it. The page
//   cannot scroll meanwhile, so a plain wheel zooms too. The view keeps its scale on screen
//   when it opens and closes, and takes the shape of the window. The address gets
//   #map-view (one history entry), so a shared link opens the map view at once.
// - Points: a tap (or click) near a point (circle or square) with data-g (Glottocodes, written by
//   languoid_map.py, and by dist/explore.js on the top page's map view), within TAP_PX on
//   screen, shows a box with the names of its records, each a link to the record's page.
//   Names and addresses come from dist/atlas-data.js and dist/lineage-paths.js, loaded on
//   the first tap. The box moves with its point when the view moves, and is out of sight
//   while the point is outside the map. Every map that mounts this script shows the same box.
// - Stepping through points (issue #94): the < and > buttons glide to the previous or next
//   point, west to east, and show its box. A key entry under the map (data-points, a
//   selector written by build_paths.py) or a legend entry of the top page's map
//   (showGroup(), called by dist/explore.js) makes its points the ones stepped through, and
//   goes to the first of them.
// - PNG: the PNG button downloads the map as it is on screen (land, borders, points), drawn
//   on a canvas from the same map files and the colours the page's CSS gives them.
//
// Other pages can reuse it: window.LangLogMap.mount(svg) on an <svg> with the attributes
// languoid_map.py writes (viewBox, data-map, data-base, data-min, data-world, data-r). The
// svg receives an "lmap:view" event, detail {k, x, y, w, h}, after every change; k is the
// view width divided by the starting width. A page that adds or replaces points, or the
// entries of its key, after mounting calls refresh() on the object mount returns; this
// script sizes the new points and makes the new key entries buttons.
(function () {
  'use strict';
  var TILE_BELOW = 700; // view width (SVG units) below which tiles are drawn
  var STEP = 1.6; // zoom factor of one button press or key press
  var GLIDE_MS = 550; // length of the Reset animation
  var STEP_MS = 220; // length of the + / - animation
  var HASH = '#map-view'; // address of the map view
  var TAP_PX = 14; // how far from a point (screen pixels) a tap still hits it
  var DRAG_PX = 4; // how far (screen pixels) a press may move and still be a tap
  // Radius on screen (CSS pixels) of a member point, at every zoom, on every map.
  var POINT_PX = 4;
  // On a map narrower than NARROW_MAP_PX (CSS pixels), points are NARROW_SHARE of that size,
  // and with more than MANY_POINTS points shown, MANY_SHARE of it again, so dense maps and
  // phone screens do not turn into one blot.
  var NARROW_MAP_PX = 600;
  var NARROW_SHARE = 0.65;
  var MANY_POINTS = 3000;
  var MANY_SHARE = 0.7;
  function pointPx(mapPx, count) {
    return (
      POINT_PX * (mapPx < NARROW_MAP_PX ? NARROW_SHARE : 1) * (count > MANY_POINTS ? MANY_SHARE : 1)
    );
  }
  // A point stepped to is shown in a view at most 1/FOCUS_SHARE of the world wide, so the
  // glide to it is visible even from the whole world.
  var FOCUS_SHARE = 4;
  // Pixels of the PNG per CSS pixel of the map on screen.
  var PNG_SCALE = 2;
  var PNG_NAME = 'lang-log-map.png';
  // Points are circles, or squares (<rect>) for the other members of a record's parent
  // (languoid_map.py). These read and change a point's centre and its radius (half the
  // side of a square), whichever shape it has.
  function isSquare(p) {
    return p.tagName.toLowerCase() === 'rect';
  }
  function pointR(p) {
    return isSquare(p) ? parseFloat(p.getAttribute('width')) / 2 : parseFloat(p.getAttribute('r'));
  }
  function pointXY(p) {
    if (!isSquare(p)) return [parseFloat(p.getAttribute('cx')), parseFloat(p.getAttribute('cy'))];
    var r = pointR(p);
    return [parseFloat(p.getAttribute('x')) + r, parseFloat(p.getAttribute('y')) + r];
  }
  function setPointR(p, r) {
    if (!isSquare(p)) {
      p.setAttribute('r', r);
      return;
    }
    var c = pointXY(p);
    p.setAttribute('x', +(c[0] - r).toFixed(3));
    p.setAttribute('y', +(c[1] - r).toFixed(3));
    p.setAttribute('width', 2 * r);
    p.setAttribute('height', 2 * r);
  }
  function setPointX(p, x) {
    if (isSquare(p)) p.setAttribute('x', +(x - pointR(p)).toFixed(2));
    else p.setAttribute('cx', x);
  }
  // Every point a page draws: the circles, and the squares of languoid_map.py.
  var POINTS = 'circle, .lmap-ctx rect';

  var manifest = null,
    manifestWait = [],
    atlas = null,
    opened = null;

  // [{id, name, url}] of Glottocodes; url is '' for a record without its own page. root is
  // the site root relative to the page ("../../").
  function records(ids, root) {
    var A = window.AtlasData,
      P = window.LineagePaths;
    if (!A || !P)
      return Promise.resolve(
        ids.map(function (id) {
          return { id: id, name: id, url: '' };
        }),
      );
    if (!atlas) {
      A.base = root + 'data/';
      atlas = A.load().then(function (r) {
        return P.init(r.d.nodes, r.d.roots, root).then(function () {
          return r.d.nodes;
        });
      });
      atlas.catch(function () {
        atlas = null;
      });
    }
    return atlas.then(function (nodes) {
      return ids.map(function (id) {
        var n = nodes[id];
        return { id: id, name: n ? n.name : id, url: n ? root + P.url(id) : '' };
      });
    });
  }

  function icon(d) {
    var s = el('svg', {
      viewBox: '0 0 16 16',
      width: '16',
      height: '16',
      'aria-hidden': 'true',
      focusable: 'false',
    });
    s.appendChild(
      el('path', {
        d: d,
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': '1.6',
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      }),
    );
    return s;
  }
  var ICON_OPEN = 'M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4';
  var ICON_CLOSE = 'M3.5 3.5l9 9M12.5 3.5l-9 9';
  // The bar's symbols are drawn, not typed, so they look the same in every font and browser
  // (the owner's request, 2026-11-23). PREV, NEXT and RESET point left or right; record.css
  // mirrors them on right-to-left pages, as the < and > characters were mirrored there.
  var ICON_ZOOM_IN = 'M8 3v10M3 8h10';
  var ICON_ZOOM_OUT = 'M3 8h10';
  var ICON_PREV = 'M10 3L5 8l5 5';
  var ICON_NEXT = 'M6 3l5 5-5 5';
  // A back arrow that turns (↩), for Reset.
  var ICON_RESET = 'M6 3L3 6l3 3M3 6h6.5a3.5 3.5 0 0 1 0 7H6';
  var ICON_DOWNLOAD = 'M8 2v8M4.5 6.5L8 10l3.5-3.5M3 13.5h10';

  function loadManifest(base, done) {
    if (manifest) return done(manifest);
    manifestWait.push(done);
    if (manifestWait.length > 1) return;
    fetch(base + 'tiles.json')
      .then(function (r) {
        return r.ok ? r.json() : null;
      })
      .catch(function () {
        return null;
      })
      .then(function (m) {
        manifest = m || { grid: [1, 1], bounds: [0, 0, 1, 1], tiles: {} };
        manifestWait.splice(0).forEach(function (f) {
          f(manifest);
        });
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

  function ease(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function mount(svg) {
    if (svg.__lmap) return svg.__lmap;
    var vb = svg.viewBox.baseVal;
    var home = { x: vb.x, y: vb.y, w: vb.width, h: vb.height };
    var homeAspect = home.w / home.h,
      aspect = homeAspect;
    // Map view: px is the width of the map on screen divided by its width in the page, so
    // points, tiles and zoom limits keep their size on screen.
    var full = false,
      px = 1,
      pageW = 0;
    // Sizes come only from the attributes languoid_map.py writes; a map without them is not mounted.
    var name = svg.getAttribute('data-map');
    var base = svg.getAttribute('data-base');
    var minW = parseFloat(svg.getAttribute('data-min'));
    var wb = (svg.getAttribute('data-world') || '').split(' ').map(parseFloat);
    if (!name || base === null || !(minW > 0) || wb.length !== 4 || wb.some(isNaN)) return null;
    var world = { x: wb[0], y: wb[1], w: wb[2], h: wb[3] };
    var W = world.w;
    // The starting view may lie east of the 180th meridian (languoid_map.py keeps a group of
    // points together); measure it on the middle copy of the world, as clamp() does.
    home.x -= W * Math.floor((home.x + home.w / 2 - world.x) / W);
    var view = { x: home.x, y: home.y, w: home.w, h: home.h };
    var raf = 0,
      glide = 0;

    // Background: every layer three times, one world apart.
    var bg = svg.querySelector('.lmap-bg');
    if (!bg) {
      bg = el('g', { 'class': 'lmap-bg' });
      svg.insertBefore(bg, svg.querySelector(':scope > use'));
    }
    // The layers, in the order the page draws them (LAYERS in languoid_map.py): each <use>
    // names its file, its layer (#sphere, #land, ...) and its class. Copies of a layer share a class.
    var layers = [],
      seen = {};
    Array.prototype.forEach.call(
      svg.querySelectorAll(':scope > use, .lmap-bg > use'),
      function (u) {
        var cls = u.getAttribute('class'),
          href = u.getAttribute('href').split('#');
        if (!seen[cls]) {
          seen[cls] = true;
          layers.push({ file: href[0], id: href[1], cls: cls });
        }
        u.parentNode.removeChild(u);
      },
    );
    // The copies of the world and the tiles (tools/build_land.py) hold the same layers, with
    // a sea that overlaps the neighbours in place of the square world.
    var tileLayers = layers.map(function (p) {
      return { id: p.id === 'sphere' ? 'sea' : p.id, cls: p.cls };
    });
    tileLayers.forEach(function (p, i) {
      [-1, 0, 1].forEach(function (k) {
        var u = el('use', { href: layers[i].file + '#' + p.id, 'class': p.cls });
        if (k) u.setAttribute('x', k * W);
        bg.appendChild(u);
      });
    });
    var tiles = el('g', { 'class': 'lmap-tiles' });
    tileLayers.forEach(function () {
      tiles.appendChild(el('g', {}));
    });
    // Tiles cover the whole world map under them, borders included, and carry their own.
    bg.appendChild(tiles);
    var shown = {};

    // Every point with its size relative to a member point (data-r: the member radius the
    // page was written with; without it every point is a member point), and their own x.
    var unitR = parseFloat(svg.getAttribute('data-r'));
    var scaled = null;
    function scaledPoints() {
      if (!scaled)
        scaled = allPoints().map(function (c) {
          if (c.__share === undefined) c.__share = unitR ? pointR(c) / unitR : 1;
          return [c, c.__share];
        });
      return scaled;
    }
    var points = null;
    function allPoints() {
      if (!points) {
        points = Array.prototype.slice.call(svg.querySelectorAll(POINTS));
        points.forEach(function (c) {
          if (c.__x0 === undefined) {
            c.__x0 = pointXY(c)[0];
            c.__k = 0;
          }
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

    // Widest view: the whole world once, and never taller than the world.
    function lim(w) {
      return Math.min(Math.max(w, minW * px), W, world.h * aspect);
    }

    function fit(v) {
      v.w = lim(v.w);
      v.h = v.w / aspect;
      // East and west: keep the centre on the middle copy of the world.
      var c = v.x + v.w / 2;
      v.x -= W * Math.floor((c - world.x) / W);
      if (v.h >= world.h) v.y = world.y + (world.h - v.h) / 2;
      else v.y = Math.min(Math.max(v.y, world.y), world.y + world.h - v.h);
      return v;
    }
    function clamp() {
      fit(view);
    }
    // The starting view at the present size: its centre, at its scale on screen.
    function homeView() {
      var w = lim(home.w * px);
      return fit({ x: home.x + home.w / 2 - w / 2, y: home.y + home.h / 2 - w / aspect / 2, w: w });
    }

    function draw() {
      raf = 0;
      svg.setAttribute(
        'viewBox',
        [view.x, view.y, view.w, view.h]
          .map(function (v) {
            return +v.toFixed(2);
          })
          .join(' '),
      );
      var k = view.w / (home.w * px),
        e = view.w / px;
      // SVG units per CSS pixel; nothing to size while the map is not laid out.
      var box = svg.getBoundingClientRect(),
        unit = box.width && box.height ? Math.max(view.w / box.width, view.h / box.height) : 0;
      var sized = scaledPoints(),
        size = unit ? pointPx(box.width, sized.length) * unit : 0;
      for (var i = 0; size && i < sized.length; i++)
        setPointR(sized[i][0], +(size * sized[i][1]).toFixed(3));
      // Each point goes to the copy of the world nearest the centre of the view.
      var cx = view.x + view.w / 2,
        ps = allPoints();
      for (var j = 0; j < ps.length; j++) {
        var p = ps[j],
          n = Math.round((cx - p.__x0) / W);
        if (n !== p.__k) {
          p.__k = n;
          setPointX(p, +(p.__x0 + n * W).toFixed(2));
        }
      }
      if (inset) {
        var show = e < W * 0.5;
        inset.parentNode.classList.toggle('lmap-inset-off', !show);
        if (show) {
          var iw = Math.min(view.w, view.h * 2) * 0.22,
            ih = iw / 2;
          inset.setAttribute('x', view.x + view.w - iw - view.w * 0.015);
          inset.setAttribute('y', view.y + view.h - ih - view.w * 0.015);
          inset.setAttribute('width', iw);
          inset.setAttribute('height', ih);
          var nx = view.x - W * Math.floor((view.x - world.x) / W);
          insetRects.forEach(function (r, i) {
            r.setAttribute('x', nx - i * W);
            r.setAttribute('y', view.y);
            r.setAttribute('width', view.w);
            r.setAttribute('height', view.h);
          });
        }
      }
      var hv = homeView();
      var moved =
        Math.abs(view.w - hv.w) > 0.01 ||
        Math.abs(view.x - hv.x) > 0.01 ||
        Math.abs(view.y - hv.y) > 0.01;
      svg.classList.toggle('lmap-moved', moved);
      svg.classList.toggle('lmap-in', e < home.w - 0.01);
      updateTiles(e);
      follow();
      svg.dispatchEvent(
        new CustomEvent('lmap:view', {
          detail: { k: k, x: view.x, y: view.y, w: view.w, h: view.h },
        }),
      );
    }

    function schedule() {
      clamp();
      if (!raf) raf = requestAnimationFrame(draw);
    }

    function updateTiles(e) {
      if (e >= TILE_BELOW) {
        tiles.style.display = 'none';
        return;
      }
      tiles.style.display = '';
      loadManifest(base, function (m) {
        var have = m.tiles[name] || [];
        var gx = m.grid[0],
          gy = m.grid[1],
          b = m.bounds,
          tw = b[2] / gx,
          th = b[3] / gy;
        // Columns run on past the edge of the world; column c is tile c mod gx, one world over.
        var c0 = Math.floor((view.x - b[0]) / tw),
          c1 = Math.floor((view.x + view.w - b[0]) / tw);
        var r0 = Math.max(0, Math.floor((view.y - b[1]) / th)),
          r1 = Math.min(gy - 1, Math.floor((view.y + view.h - b[1]) / th));
        for (var c = c0; c <= c1; c++)
          for (var r = r0; r <= r1; r++) {
            var col = ((c % gx) + gx) % gx,
              shift = Math.floor(c / gx) * b[2];
            var id = col + '-' + r,
              key = id + '@' + Math.round(shift);
            if (shown[key] || have.indexOf(id) < 0) continue;
            shown[key] = true;
            var href = base + 'tiles/' + name + '/' + id + '.svg';
            // One group per layer, so no tile's sea covers the edge of its neighbour's land.
            tileLayers.forEach(function (p, i) {
              var u = el('use', { href: href + '#' + p.id, 'class': p.cls });
              if (shift) u.setAttribute('x', shift);
              tiles.childNodes[i].appendChild(u);
            });
          }
      });
    }

    function stop() {
      if (glide) {
        cancelAnimationFrame(glide);
        glide = 0;
      }
    }

    // Move smoothly to the view {x, y, w}: the centre slides along the shorter way round
    // the world while the width changes at an even rate of zoom.
    // done (optional) runs once the view is there.
    function glideTo(to, ms, done) {
      stop();
      to.w = lim(to.w);
      if (reducedMotion()) {
        view = { x: to.x, y: to.y, w: to.w, h: to.w / aspect };
        clamp();
        draw();
        if (done) done();
        return;
      }
      var fw = view.w,
        tw = to.w;
      var fx = view.x + view.w / 2,
        tx = to.x + to.w / 2;
      fx -= W * Math.round((fx - tx) / W);
      var fy = view.y + view.h / 2,
        ty = to.y + to.w / aspect / 2;
      var t0 = performance.now();
      function frame(now) {
        var t = Math.min(1, (now - t0) / ms),
          e = ease(t);
        var w = Math.exp(Math.log(fw) + (Math.log(tw) - Math.log(fw)) * e);
        var cx = fx + (tx - fx) * e,
          cy = fy + (ty - fy) * e;
        view = { x: cx - w / 2, y: cy - w / aspect / 2, w: w, h: w / aspect };
        clamp();
        draw();
        glide = t < 1 ? requestAnimationFrame(frame) : 0;
        if (!glide && done) done();
      }
      glide = requestAnimationFrame(frame);
    }

    // The view after zooming by factor f (>1 zooms in) keeping the SVG point (px, py) where it is.
    function zoomed(f, px, py) {
      if (px === undefined) {
        px = view.x + view.w / 2;
        py = view.y + view.h / 2;
      }
      var w = lim(view.w / f);
      var s = w / view.w;
      return { x: px - (px - view.x) * s, y: py - (py - view.y) * s, w: w };
    }
    function zoom(f, px, py) {
      stop();
      var v = zoomed(f, px, py);
      view.x = v.x;
      view.y = v.y;
      view.w = v.w;
      schedule();
    }
    function zoomSmooth(f) {
      glideTo(zoomed(f), STEP_MS);
    }

    function toSvg(clientX, clientY) {
      var r = svg.getBoundingClientRect();
      // preserveAspectRatio meet: the view fills the box when the box has the same aspect.
      var scale = Math.max(view.w / r.width, view.h / r.height);
      var ox = (r.width - view.w / scale) / 2,
        oy = (r.height - view.h / scale) / 2;
      return [
        view.x + (clientX - r.left - ox) * scale,
        view.y + (clientY - r.top - oy) * scale,
        scale,
      ];
    }

    function reset() {
      glideTo(homeView(), GLIDE_MS);
    }

    // Pointers: one pans (a finger too, from the start: touch-action is none on the map,
    // so the page scrolls from outside the map), two pinch.
    var pts = {},
      start = null;
    function snapshot() {
      var ids = Object.keys(pts);
      if (!ids.length) {
        start = null;
        return;
      }
      var a = pts[ids[0]],
        b = pts[ids[1]] || a;
      start = {
        n: ids.length,
        view: { x: view.x, y: view.y, w: view.w },
        mid: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2],
        dist: Math.hypot(a[0] - b[0], a[1] - b[1]) || 1,
      };
      start.at = toSvg(start.mid[0], start.mid[1]);
    }
    svg.addEventListener('pointerdown', function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      stop();
      pts[e.pointerId] = [e.clientX, e.clientY];
      try {
        svg.setPointerCapture(e.pointerId);
      } catch {
        /* the pointer is already gone */
      }
      svg.classList.add('lmap-drag');
      snapshot();
    });
    svg.addEventListener('pointermove', function (e) {
      if (!pts[e.pointerId] || !start) return;
      pts[e.pointerId] = [e.clientX, e.clientY];
      var ids = Object.keys(pts);
      if (start.n !== ids.length) snapshot();
      var a = pts[ids[0]],
        b = pts[ids[1]] || a;
      var mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      var f = ids.length > 1 ? Math.hypot(a[0] - b[0], a[1] - b[1]) / start.dist : 1;
      var w = lim(start.view.w / f),
        s = w / start.view.w;
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
    svg.addEventListener(
      'wheel',
      function (e) {
        // Plain wheel scrolls the page; Ctrl/Cmd + wheel (and trackpad pinch, which browsers
        // report as Ctrl + wheel) zooms the map.
        // In the map view there is no page to scroll, so every wheel zooms.
        if (!full && !e.ctrlKey && !e.metaKey) return;
        e.preventDefault();
        var p = toSvg(e.clientX, e.clientY);
        zoom(Math.exp(-e.deltaY * (e.deltaMode === 1 ? 0.05 : 0.0025)), p[0], p[1]);
      },
      { passive: false },
    );
    // Safari trackpad pinch.
    var g0 = null;
    svg.addEventListener('gesturestart', function (e) {
      e.preventDefault();
      stop();
      g0 = { w: view.w, at: toSvg(e.clientX, e.clientY) };
    });
    svg.addEventListener('gesturechange', function (e) {
      if (!g0) return;
      e.preventDefault();
      var w = lim(g0.w / e.scale);
      zoom(view.w / w, g0.at[0], g0.at[1]);
    });
    svg.addEventListener('gestureend', function () {
      g0 = null;
    });
    svg.addEventListener('dblclick', function (e) {
      var p = toSvg(e.clientX, e.clientY);
      glideTo(zoomed(e.shiftKey ? 1 / STEP : STEP, p[0], p[1]), STEP_MS);
    });
    svg.setAttribute('tabindex', '0');
    svg.addEventListener('keydown', function (e) {
      var d = view.w * 0.15,
        used = true;
      if (e.key === '+' || e.key === '=') zoomSmooth(STEP);
      else if (e.key === '-' || e.key === '_') zoomSmooth(1 / STEP);
      else if (e.key === '0') reset();
      else if (e.key === 'Escape' && full) closeView();
      else if (e.key === 'ArrowLeft') {
        stop();
        view.x -= d;
        schedule();
      } else if (e.key === 'ArrowRight') {
        stop();
        view.x += d;
        schedule();
      } else if (e.key === 'ArrowUp') {
        stop();
        view.y -= d;
        schedule();
      } else if (e.key === 'ArrowDown') {
        stop();
        view.y += d;
        schedule();
      } else used = false;
      if (used) e.preventDefault();
    });

    // Buttons, placed over the top right corner of the map.
    var bar = document.createElement('div');
    bar.className = 'lmap-tools';
    // Every button shows an icon and carries its label for screen readers and as a tooltip.
    function toolButton(path, text, onClick) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.appendChild(icon(path));
      btn.setAttribute('aria-label', text);
      btn.title = text;
      btn.addEventListener('click', onClick);
      return btn;
    }
    // Two buttons in one box with a line between them, [ - | + ] and [ < | > ] (the owner's
    // requests, 2026-11-23); each half stays its own button, for the keyboard and screen
    // readers (record.css draws the box).
    function pair(className, first, second) {
      var box = document.createElement('span');
      box.className = className;
      box.appendChild(first);
      box.appendChild(second);
      bar.appendChild(box);
    }
    // Reset comes first, at the start of the bar: the left end, or the right end on
    // right-to-left pages (the owner's request, 2026-11-23).
    var resetBtn = toolButton(ICON_RESET, 'Reset view', reset);
    resetBtn.className = 'lmap-reset';
    bar.appendChild(resetBtn);
    // - and + only where a mouse or trackpad exists; on phones and tablets people pinch.
    var fine = !window.matchMedia || window.matchMedia('(any-pointer: fine)').matches;
    if (fine)
      pair(
        'lmap-pair',
        toolButton(ICON_ZOOM_OUT, 'Zoom out', function () {
          zoomSmooth(1 / STEP);
        }),
        toolButton(ICON_ZOOM_IN, 'Zoom in', function () {
          zoomSmooth(STEP);
        }),
      );
    pair(
      'lmap-pair lmap-step',
      toolButton(ICON_PREV, 'Previous point', function () {
        step(-1);
      }),
      toolButton(ICON_NEXT, 'Next point', function () {
        step(1);
      }),
    );
    var pngBtn = document.createElement('button');
    pngBtn.type = 'button';
    pngBtn.className = 'lmap-png';
    pngBtn.appendChild(icon(ICON_DOWNLOAD));
    pngBtn.setAttribute('aria-label', 'Download the map as PNG');
    pngBtn.title = 'Download the map as PNG';
    pngBtn.addEventListener('click', function () {
      exportPNG();
    });
    bar.appendChild(pngBtn);
    var fullBtn = document.createElement('button');
    fullBtn.type = 'button';
    fullBtn.className = 'lmap-full-btn';
    bar.appendChild(fullBtn);
    function label(open) {
      var t = open ? 'Close map view' : 'Map view';
      fullBtn.textContent = '';
      fullBtn.appendChild(icon(open ? ICON_CLOSE : ICON_OPEN));
      fullBtn.setAttribute('aria-label', t);
      fullBtn.title = t;
      fullBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    label(false);
    var parent = svg.parentNode;
    var wrap = document.createElement('div');
    wrap.className = 'lmap-wrap';
    parent.insertBefore(wrap, svg);
    wrap.appendChild(svg);
    wrap.appendChild(bar);
    // The key under the map (written by build_paths.py on record pages, filled by
    // dist/explore.js on the top page) moves into the box with it, so the map view shows it
    // too (record.css places it over the map there).
    var key = wrap.parentNode.querySelector(':scope > .lmap-key');
    if (key) wrap.appendChild(key);
    // Each key entry that names its points becomes a button that steps through them; run
    // again by refresh() for entries a page adds later.
    function keyButtons() {
      if (!key) return;
      Array.prototype.forEach.call(key.querySelectorAll('li[data-points]'), function (li) {
        if (li.querySelector(':scope > .lmap-key-btn')) return;
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'lmap-key-btn';
        while (li.firstChild) b.appendChild(li.firstChild);
        li.appendChild(b);
        b.addEventListener('click', function () {
          // On a narrow screen the map may be partly off screen: bring it into view first.
          var r = svg.getBoundingClientRect();
          if (!full && (r.top < 0 || r.bottom > window.innerHeight))
            svg.scrollIntoView({ block: 'center' });
          showGroup(svg.querySelectorAll(li.getAttribute('data-points')));
        });
      });
    }
    keyButtons();
    // The part of the page that fills the window in the map view: the map, or a larger
    // box marked lmap-host that holds the map and its own overlays (the top page's map view).
    var host = wrap.closest('.lmap-host') || wrap;

    // Map view. resize() keeps the centre and the scale on screen while the box changes.
    var pushed = false,
      boxW = 0;
    // The width and centre the last resize asked for, before fit() held them inside the world,
    // and the view that came out. While the view is still that one, the next resize starts from
    // what was asked, so zooming the browser far out (or in) and back brings back the same view.
    var asked = null;
    function resize(before) {
      var r = svg.getBoundingClientRect();
      if (!r.width || !r.height || !before) return;
      var from =
        asked && asked.x === view.x && asked.y === view.y && asked.w === view.w ? asked : null;
      var cx = from ? from.cx : view.x + view.w / 2,
        cy = from ? from.cy : view.y + view.h / 2,
        w = ((from ? from.want : view.w) * r.width) / before;
      aspect = full ? r.width / r.height : homeAspect;
      px = full ? r.width / pageW : 1;
      view.w = lim(w);
      view.h = view.w / aspect;
      view.x = cx - view.w / 2;
      view.y = cy - view.h / 2;
      boxW = r.width;
      clamp();
      asked = { cx: cx, cy: cy, want: w, x: view.x, y: view.y, w: view.w };
      schedule();
    }
    // The map view's buttons, key and lines keep their size on the screen when the browser
    // zooms (dist/record.css): --lmap-screen-scale is the window's longer side over
    // --lmap-screen-base, or 1 where the stylesheet sets no base (touch screens).
    function screenScale() {
      var base = parseFloat(getComputedStyle(host).getPropertyValue('--lmap-screen-base'));
      host.style.setProperty(
        '--lmap-screen-scale',
        base > 0 ? String(Math.max(window.innerWidth, window.innerHeight) / base) : '1',
      );
    }
    function openView(push) {
      if (full) return;
      if (opened && opened !== api) opened.close(false);
      stop();
      var before = svg.getBoundingClientRect().width;
      pageW = before;
      full = true;
      opened = api;
      host.classList.add('lmap-full');
      document.documentElement.classList.add('lmap-full-open');
      screenScale();
      label(true);
      resize(before);
      draw();
      if (push && location.hash !== HASH) {
        try {
          history.pushState({ lmap: 1 }, '', location.pathname + location.search + HASH);
          pushed = true;
        } catch {
          /* no history entry: Back leaves the page */
        }
      }
      try {
        svg.focus({ preventScroll: true });
      } catch {
        svg.focus();
      }
      window.addEventListener('resize', onResize);
    }
    function close(fromHistory) {
      if (!full) return;
      stop();
      hidePop();
      var before = svg.getBoundingClientRect().width;
      full = false;
      if (opened === api) opened = null;
      host.classList.remove('lmap-full');
      document.documentElement.classList.remove('lmap-full-open');
      host.style.removeProperty('--lmap-screen-scale');
      label(false);
      window.removeEventListener('resize', onResize);
      resize(before);
      draw();
      if (!fromHistory && location.hash === HASH) {
        // Leave the entry the map view added, or drop the mark from an address that came with it.
        if (pushed) history.back();
        else
          try {
            history.replaceState(history.state, '', location.pathname + location.search);
          } catch {
            /* keep the address as it is */
          }
      }
      pushed = false;
      fullBtn.focus();
    }
    function closeView() {
      close(false);
    }
    function onResize() {
      screenScale();
      resize(boxW);
    }
    fullBtn.addEventListener('click', function () {
      if (full) closeView();
      else openView(true);
    });

    // Taps on points: a tap (or click) that did not end a drag picks the nearest circle with
    // data-g within TAP_PX on screen (points are only a few pixels wide) and shows the box
    // of its records next to the tap; a tap elsewhere, Escape, closing the map view or new
    // points (refresh()) hide it. The same on the record maps and the top page's map view.
    // While it is open, the box moves with its point whenever the view changes (follow()),
    // and is out of sight while the point is outside the map.
    var root = base.replace(/map\/$/, '');
    var pop = null,
      popAt = null,
      downAt = null,
      tapAt = null;
    // Each tap gets a number; a box whose names arrive after a newer tap or after hidePop()
    // is dropped.
    var popTap = 0;
    function hidePop() {
      popTap++;
      popAt = null;
      if (pop) pop.hidden = true;
    }
    // The centre of a point on screen.
    function onScreen(c) {
      var r = c.getBoundingClientRect();
      return [r.left + r.width / 2, r.top + r.height / 2];
    }
    function nearest(clientX, clientY) {
      var p = toSvg(clientX, clientY),
        best = null,
        bd = Infinity;
      var cs = svg.querySelectorAll('circle[data-g], .lmap-ctx rect[data-g]');
      for (var i = 0; i < cs.length; i++) {
        var c = cs[i],
          xy = pointXY(c),
          dx = xy[0] - p[0],
          dy = xy[1] - p[1];
        var d = Math.sqrt(dx * dx + dy * dy) / p[2];
        var reach = Math.max(TAP_PX, pointR(c) / p[2] + 4);
        if (d <= reach && d < bd) {
          bd = d;
          best = c;
        }
      }
      return best;
    }
    // The box opens only once the records' names have loaded (records() fetches the atlas
    // data on the first tap), so it never shows the bare ids of data-g in the meantime.
    function showPop(c, clientX, clientY) {
      var ids = c.getAttribute('data-g').split(' ').filter(Boolean);
      hidePop();
      var tap = popTap;
      records(ids, root).then(
        function (rs) {
          if (tap !== popTap) return;
          if (!pop) {
            pop = document.createElement('div');
            pop.className = 'lmap-pop';
            pop.setAttribute('role', 'dialog');
            pop.setAttribute('aria-label', 'Records at this point');
            host.appendChild(pop);
          }
          pop.textContent = '';
          var list = document.createElement('ul');
          list.className = 'notranslate';
          rs.forEach(function (r) {
            var li = document.createElement('li');
            var a = document.createElement(r.url ? 'a' : 'span');
            a.textContent = r.name;
            if (r.url) a.href = r.url;
            li.appendChild(a);
            list.appendChild(li);
          });
          pop.appendChild(list);
          var x = document.createElement('button');
          x.type = 'button';
          x.className = 'lmap-pop-close';
          x.setAttribute('aria-label', 'Close');
          x.appendChild(icon(ICON_CLOSE));
          x.addEventListener('click', function () {
            hidePop();
            svg.focus();
          });
          pop.appendChild(x);
          pop.hidden = false;
          // The box keeps the distance from its point that the tap had.
          var xy = onScreen(c);
          popAt = { point: c, dx: clientX - xy[0], dy: clientY - xy[1] };
          follow();
        },
        function () {},
      );
    }

    function place(clientX, clientY) {
      var b = host.getBoundingClientRect();
      var x = Math.min(clientX - b.left + 10, b.width - pop.offsetWidth - 8);
      var y = Math.min(clientY - b.top + 10, b.height - pop.offsetHeight - 8);
      pop.style.left = Math.max(8, x) + 'px';
      pop.style.top = Math.max(8, y) + 'px';
    }
    // Runs after every change of the view (draw()): the open box goes next to its point
    // again, which draw() may have moved to another copy of the world.
    function follow() {
      if (!popAt) return;
      var xy = onScreen(popAt.point),
        r = svg.getBoundingClientRect(),
        inside = xy[0] >= r.left && xy[0] <= r.right && xy[1] >= r.top && xy[1] <= r.bottom;
      pop.style.visibility = inside ? '' : 'hidden';
      if (inside) place(xy[0] + popAt.dx, xy[1] + popAt.dy);
    }
    // Where the finger or pointer went down and came up decides, not the click: phone
    // browsers move a tap's click towards the nearest element they think it meant.
    svg.addEventListener('pointerdown', function (e) {
      downAt = [e.clientX, e.clientY];
      tapAt = null;
    });
    svg.addEventListener('pointerup', function (e) {
      // A press that moved more than DRAG_PX was a drag, not a tap.
      var moved = downAt && Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > DRAG_PX;
      tapAt = downAt && !moved ? downAt : null;
      downAt = null;
    });
    svg.addEventListener('click', function () {
      var at = tapAt;
      tapAt = null;
      if (!at) return;
      var c = nearest(at[0], at[1]);
      if (c) showPop(c, at[0], at[1]);
      else hidePop();
    });
    svg.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !full) hidePop();
    });

    // Stepping through points: group is the points the < and > buttons go through, west to
    // east (all points until a key or legend entry chooses some), at the index of the last one.
    var group = null,
      at = -1;
    function byPlace(list) {
      allPoints();
      return Array.prototype.filter
        .call(list, function (c) {
          return c.hasAttribute('data-g');
        })
        .sort(function (a, b) {
          var ax = a.__x0 === undefined ? pointXY(a)[0] : a.__x0,
            bx = b.__x0 === undefined ? pointXY(b)[0] : b.__x0;
          return ax - bx || pointXY(a)[1] - pointXY(b)[1];
        });
    }
    function focusPoint(c) {
      hidePop();
      allPoints();
      var w = lim(Math.min(view.w, W / FOCUS_SHARE)),
        x0 = c.__x0 === undefined ? pointXY(c)[0] : c.__x0,
        cx = view.x + view.w / 2,
        x = x0 + W * Math.round((cx - x0) / W),
        y = pointXY(c)[1];
      glideTo({ x: x - w / 2, y: y - w / aspect / 2, w: w }, GLIDE_MS, function () {
        var xy = onScreen(c);
        showPop(c, xy[0], xy[1]);
      });
    }
    function step(d) {
      if (!group || !group.length || !group[0].isConnected) {
        group = byPlace(svg.querySelectorAll(POINTS));
        at = -1;
      }
      if (!group.length) return;
      at = at < 0 ? (d > 0 ? 0 : group.length - 1) : (at + d + group.length) % group.length;
      focusPoint(group[at]);
    }
    function showGroup(list) {
      group = byPlace(list);
      at = -1;
      step(1);
    }

    // PNG: the background layers (each <use> of a map file, in the order drawn) and the
    // points, painted on a canvas with the colours and line widths the page's CSS gives them.
    // A line with non-scaling-stroke (in the CSS, or written on a map file's path) keeps its
    // width on screen, as on the map; any other line is as wide in the units of the map as the
    // SVG draws it. Every point's outline is non-scaling (dist/record.css).
    var files = {};
    function mapFile(href) {
      if (!files[href])
        files[href] = fetch(new URL(href, document.baseURI))
          .then(function (r) {
            if (!r.ok) throw new Error(href);
            return r.text();
          })
          .then(function (t) {
            return new DOMParser().parseFromString(t, 'image/svg+xml');
          });
      return files[href];
    }
    // A number from computed style, or 1 when it has none.
    function share(v) {
      var n = parseFloat(v);
      return isNaN(n) ? 1 : n;
    }
    // own is the drawn element (a map file's path or a point); a fill, stroke or vector-effect
    // written on it wins over the CSS, as in the SVG.
    function paint(ctx, shape, own, cs, k, opacity) {
      var fill = own.getAttribute('fill') === 'none' ? 'none' : cs.fill,
        stroke = own.getAttribute('stroke') === 'none' ? 'none' : cs.stroke,
        sw = parseFloat(cs.strokeWidth) || 0;
      // k turns screen pixels into units of the map; a scaling line is in those units already.
      if ((own.getAttribute('vector-effect') || cs.vectorEffect) !== 'non-scaling-stroke') k = 1;
      ctx.globalAlpha = opacity * share(cs.fillOpacity);
      if (fill && fill !== 'none') {
        ctx.fillStyle = fill;
        ctx.fill(shape);
      }
      ctx.globalAlpha = opacity;
      if (stroke && stroke !== 'none' && sw > 0) {
        ctx.strokeStyle = stroke;
        ctx.lineWidth = sw * k;
        var dash = cs.strokeDasharray;
        ctx.setLineDash(
          dash && dash !== 'none'
            ? dash.split(/[ ,]+/).map(function (v) {
                return parseFloat(v) * k;
              })
            : [],
        );
        ctx.stroke(shape);
      }
    }
    function exportPNG() {
      var box = svg.getBoundingClientRect();
      if (!box.width || !box.height) return;
      var canvas = document.createElement('canvas');
      canvas.width = Math.round(box.width * PNG_SCALE);
      canvas.height = Math.round(box.height * PNG_SCALE);
      var ctx = canvas.getContext('2d');
      // preserveAspectRatio meet: the view, centred, as large as fits.
      var s = Math.min(canvas.width / view.w, canvas.height / view.h),
        ox = (canvas.width - view.w * s) / 2 - view.x * s,
        oy = (canvas.height - view.h * s) / 2 - view.y * s;
      // One CSS pixel of line width in the units of the map.
      var k = PNG_SCALE / s;
      var uses = Array.prototype.filter.call(svg.querySelectorAll('.lmap-bg use'), function (u) {
        return getComputedStyle(u).display !== 'none' && !u.closest('[style*="display: none"]');
      });
      Promise.all(
        uses.map(function (u) {
          return mapFile(u.getAttribute('href').split('#')[0]);
        }),
      )
        .then(function (docs) {
          ctx.fillStyle = getComputedStyle(svg).backgroundColor;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          uses.forEach(function (u, i) {
            var own = docs[i].getElementById(u.getAttribute('href').split('#')[1]);
            if (!own || !own.getAttribute('d')) return;
            ctx.setTransform(s, 0, 0, s, ox + (parseFloat(u.getAttribute('x')) || 0) * s, oy);
            paint(ctx, new Path2D(own.getAttribute('d')), own, getComputedStyle(u), k, 1);
          });
          Array.prototype.forEach.call(svg.querySelectorAll(POINTS), function (c) {
            if (c.closest('.lmap-inset')) return;
            var cs = getComputedStyle(c);
            if (cs.display === 'none') return;
            var xy = pointXY(c),
              r = pointR(c),
              shape = new Path2D();
            if (isSquare(c)) shape.rect(xy[0] - r, xy[1] - r, 2 * r, 2 * r);
            else shape.arc(xy[0], xy[1], r, 0, 2 * Math.PI);
            ctx.setTransform(s, 0, 0, s, ox, oy);
            paint(ctx, shape, c, cs, k, share(cs.opacity));
          });
          canvas.toBlob(function (blob) {
            if (!blob) return;
            var a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = PNG_NAME;
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(function () {
              URL.revokeObjectURL(a.href);
            });
          }, 'image/png');
        })
        .catch(function () {});
    }

    var api = {
      svg: svg,
      zoom: zoom,
      reset: reset,
      open: function () {
        openView(true);
      },
      close: close,
      isOpen: function () {
        return full;
      },
      refresh: function () {
        // The points changed: a box for a point that may be gone is closed, and stepping
        // starts again from all points.
        hidePop();
        points = null;
        scaled = null;
        group = null;
        keyButtons();
        at = -1;
        schedule();
      },
      showGroup: showGroup,
      view: function () {
        return { x: view.x, y: view.y, w: view.w, h: view.h };
      },
    };
    svg.__lmap = api;
    // The size of the points depends on the width of the map on screen (pointPx()).
    window.addEventListener('resize', schedule);
    schedule();
    // An address with #map-view opens the first map in the map view.
    if (location.hash === HASH && !opened) openView(false);
    return api;
  }

  // Back and Forward move between the page and its map view.
  window.addEventListener('popstate', function () {
    if (location.hash === HASH) {
      if (!opened) {
        var s = document.querySelector('svg.lmap');
        if (s && s.__lmap) s.__lmap.open();
      }
    } else if (opened) opened.close(true);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && opened && !e.defaultPrevented) opened.close(false);
  });

  window.LangLogMap = { mount: mount };
  function all() {
    Array.prototype.forEach.call(document.querySelectorAll('svg.lmap[data-map]'), mount);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all);
  else all();
})();
