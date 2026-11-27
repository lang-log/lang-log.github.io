// Checks that the map view keeps its key, its buttons and its lines the same size on the
// screen whatever the browser zoom, and that zooming the browser and the map in and back
// out brings everything back (dist/map-zoom.js, dist/record.css; the owner's requests,
// 2026-11-23). Run after tools/build_site.sh, from the repository root, with Playwright and
// its browsers installed (.github/workflows/browsers.yml):
//   node tools/check_map_view.js [chromium firefox webkit]
//
// The browser's zoom is played by the window's size and its device pixel ratio: at zoom z
// on a screen of SCREEN pixels the page is SCREEN / z CSS pixels wide with z device pixels
// per CSS pixel. Sizes on the screen are measured in device pixels.
/* global window, document, getComputedStyle, requestAnimationFrame -- measure() runs in the page, not in Node.js */
const { chromium, firefox, webkit } = require('playwright'),
  { serve } = require('./serve_dist');

const SCREEN = { width: 1920, height: 960 }; // a desktop screen, in device pixels
const HOME_ZOOM = 1.5; // the zoom every other zoom is compared with (the owner's 150%)
// Browser zooms to open the map view at, from the smallest to the largest browsers offer.
const ZOOMS = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3, 4.7, 5, 7.1];
// Zooms the browser goes through, in this order, on one open map view; it ends at HOME_ZOOM.
const ROUND_TRIP = [4.7, 7.1, 1.5, 0.25, 1.5, 0.5, 3, 1.5];
// How far a size may drift from its size at HOME_ZOOM: text is laid out again at each zoom,
// so its width moves by a few per cent; a key or a line that grows with the zoom moves by
// far more (three times at 470%).
const TOLERANCE = 0.1;
// WebKit draws a border in whole device pixels, so a border may be off by up to this many
// device pixels at any zoom (a border that grows with the zoom is off by far more at 300%).
const SNAP_PX = 0.6;
// Safari zooms a page from 50% (Safari > Settings > Websites > Page Zoom). Below that, WebKit
// in Playwright stops resizing the page once it has been made 11520 device pixels wide, so
// its series of zooms starts at this one.
const SAFARI_MIN_ZOOM = 0.5;
// How long a page may take to open the map view or draw its points (ms). In CI, Firefox at
// 25% (a page 7680 CSS pixels wide) sometimes takes seconds to draw them.
const READY_MS = 15000;
const PHONE = { width: 390, height: 844 }; // CSS pixels
const FINGER_PX = 44; // buttons on a touch screen (record.css)
const PAGES = [
  // A record's map and the top page's map, which share dist/map-zoom.js and dist/record.css.
  { path: '/afro-asiatic/berber/#map-view', key: true },
  { path: '/?view=map#map-view', key: false },
];
const VARIANTS = [
  { locale: 'en-US', colorScheme: 'light' },
  { locale: 'ar', colorScheme: 'dark' }, // right to left
];

// Everything measured on the open map view, in device pixels where it is a size on screen.
function measure() {
  const d = window.devicePixelRatio,
    host = document.querySelector('.lmap-full');
  if (!host) return null;
  const svg = host.querySelector('svg.lmap'),
    key = host.querySelector('.lmap-key:not([hidden])'),
    button = host.querySelector('.lmap-tools .lmap-png'),
    line = svg.querySelector('.lmap-border');
  const box = (e) => {
    const r = e.getBoundingClientRect();
    // How much transform shrinks or grows the element on screen.
    const scale = e.offsetWidth ? r.width / e.offsetWidth : 1;
    return {
      w: r.width * d,
      h: r.height * d,
      border: parseFloat(getComputedStyle(e).borderTopWidth) * scale * d,
    };
  };
  return {
    view: svg.getAttribute('viewBox'),
    key: key ? box(key) : null,
    button: box(button),
    line: parseFloat(getComputedStyle(line).strokeWidth) * d,
  };
}

// A point of the map view that a click reaches (not under the key or the buttons), as
// [x, y] in CSS pixels, or null.
function pointOnScreen() {
  const ps = document.querySelectorAll(
    '.lmap-full circle[data-g], .lmap-full .lmap-ctx rect[data-g]',
  );
  for (const p of ps) {
    const r = p.getBoundingClientRect(),
      x = r.left + r.width / 2,
      y = r.top + r.height / 2;
    if (x > 0 && y > 0 && x < window.innerWidth && y < window.innerHeight)
      if (document.elementFromPoint(x, y) === p) return [x, y];
  }
  return null;
}
// The picked point (the one whose box is open) against the other points of its kind: how
// many times wider it is on screen, and how many times thicker its outline.
function picked() {
  const p = document.querySelector('.lmap-full .lmap-picked');
  if (!p) return null;
  const other = Array.prototype.find.call(
    p.parentNode.children,
    (c) => c !== p && c.tagName === p.tagName,
  );
  if (!other) return null;
  const w = (e) => e.getBoundingClientRect().width,
    sw = (e) => parseFloat(getComputedStyle(e).strokeWidth);
  return { size: w(p) / w(other), ring: sw(p) / sw(other) };
}
// Resolves once the page has drawn two more frames, so a draw that dist/map-zoom.js scheduled
// (requestAnimationFrame) has run. A busy browser draws later, so this waits as long as it
// takes, not a fixed time.
function frames(tab) {
  return tab.evaluate(
    () => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(() => done()))),
  );
}
async function pick(tab) {
  // A busy browser may not have drawn the points yet; wait for one a click can reach.
  const found = await tab
    .waitForFunction(pointOnScreen, null, { timeout: READY_MS })
    .catch(() => null);
  const at = found && (await found.jsonValue());
  if (!at) return null;
  await tab.mouse.click(at[0], at[1]);
  // The point is marked at once and drawn larger on the next frame; wait for both.
  await tab
    .waitForFunction(() => document.querySelector('.lmap-full .lmap-picked'), null, {
      timeout: 5000,
    })
    .catch(() => null);
  await frames(tab);
  return tab.evaluate(picked);
}

const failures = [];
function near(what, got, want, slack = 0) {
  if (!(Math.abs(got - want) <= Math.max(want * TOLERANCE, slack)))
    failures.push(
      `${what}: ${got.toFixed(2)} device px, ${want.toFixed(2)} at ${HOME_ZOOM * 100}%`,
    );
}
function compare(where, m, ref) {
  if (!m) {
    failures.push(`${where}: the map view did not open`);
    return;
  }
  if (ref.key) {
    near(`${where}: key width`, m.key.w, ref.key.w);
    near(`${where}: key height`, m.key.h, ref.key.h);
    near(`${where}: key border`, m.key.border, ref.key.border, SNAP_PX);
  }
  near(`${where}: button height`, m.button.h, ref.button.h);
  near(`${where}: button border`, m.button.border, ref.button.border, SNAP_PX);
  near(`${where}: border line`, m.line, ref.line);
}

async function open(browser, page, variant, zoom) {
  const ctx = await browser.newContext({
    viewport: { width: Math.round(SCREEN.width / zoom), height: Math.round(SCREEN.height / zoom) },
    deviceScaleFactor: zoom,
    locale: variant.locale,
    colorScheme: variant.colorScheme,
  });
  const tab = await ctx.newPage();
  tab.on('pageerror', (e) => failures.push(`${page.path}: ${e.message}`));
  await tab.goto(base + page.path, { waitUntil: 'networkidle' });
  await tab.waitForFunction(() => document.querySelector('.lmap-full'), null, {
    timeout: READY_MS,
  });
  await tab.waitForTimeout(300);
  await frames(tab);
  return { ctx, tab };
}

let base = '';
(async () => {
  const server = await serve();
  base = `http://127.0.0.1:${server.address().port}`;
  const engines = { chromium, firefox, webkit };
  const names = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(engines);
  for (const name of names) {
    const browser = await engines[name].launch();
    for (const page of PAGES)
      for (const variant of VARIANTS) {
        const at = `${name} ${page.path} ${variant.locale} ${variant.colorScheme}`;
        let { ctx, tab } = await open(browser, page, variant, HOME_ZOOM);
        const ref = await tab.evaluate(measure);
        const refPick = await pick(tab);
        await ctx.close();
        if (!refPick) failures.push(`${at}: no point could be picked at ${HOME_ZOOM * 100}%`);
        if (!ref || (page.key && !ref.key)) {
          failures.push(`${at}: no map view or key at ${HOME_ZOOM * 100}%`);
          continue;
        }
        // Opened at each zoom.
        for (const zoom of ZOOMS) {
          ({ ctx, tab } = await open(browser, page, variant, zoom));
          compare(`${at} opened at ${zoom * 100}%`, await tab.evaluate(measure), ref);
          // The picked point keeps its share of the others' size and outline.
          const got = await pick(tab);
          if (refPick && !got) failures.push(`${at} at ${zoom * 100}%: no point could be picked`);
          else if (refPick)
            for (const what of ['size', 'ring'])
              if (Math.abs(got[what] - refPick[what]) > refPick[what] * TOLERANCE)
                failures.push(
                  `${at} at ${zoom * 100}%: picked point ${what} ${got[what].toFixed(2)} times the others, ${refPick[what].toFixed(2)} at ${HOME_ZOOM * 100}%`,
                );
          await ctx.close();
        }
        // One map view through a series of browser zooms, then the map's own zoom in and
        // out, and back to the start. The device pixel ratio of a page cannot change in
        // every engine, so the window's size plays the zoom and sizes are compared in CSS
        // pixels times HOME_ZOOM / zoom, the device pixels they would take.
        ({ ctx, tab } = await open(browser, page, variant, HOME_ZOOM));
        for (const zoom of ROUND_TRIP.filter((z) => name !== 'webkit' || z >= SAFARI_MIN_ZOOM)) {
          await tab.setViewportSize({
            width: Math.round(SCREEN.width / zoom),
            height: Math.round(SCREEN.height / zoom),
          });
          await tab.waitForTimeout(300);
          const m = await tab.evaluate(measure);
          const k = zoom / HOME_ZOOM;
          if (m.key) ['w', 'h', 'border'].forEach((p) => (m.key[p] *= k));
          ['h', 'border'].forEach((p) => (m.button[p] *= k));
          m.line *= k;
          compare(`${at} zoomed to ${zoom * 100}% after the others`, m, ref);
        }
        const back = await tab.evaluate(measure);
        if (back.view !== ref.view)
          failures.push(`${at}: view ${back.view} after zooming back, ${ref.view} at the start`);
        await tab.focus('.lmap-full svg.lmap');
        for (const k of ['+', '+', '+', '-', '-', '-', '-', '+']) {
          await tab.keyboard.press(k);
          await tab.waitForTimeout(350);
          compare(`${at} after the map's own zoom (${k})`, await tab.evaluate(measure), ref);
        }
        await ctx.close();
        // A phone: whole CSS pixels, buttons big enough for a finger.
        if (name !== 'firefox') {
          const phone = await browser.newContext({
            viewport: PHONE,
            deviceScaleFactor: 3,
            isMobile: true,
            hasTouch: true,
            locale: variant.locale,
            colorScheme: variant.colorScheme,
          });
          const p = await phone.newPage();
          await p.goto(base + page.path, { waitUntil: 'networkidle' });
          await p.waitForFunction(() => document.querySelector('.lmap-full'), null, {
            timeout: READY_MS,
          });
          const m = await p.evaluate(measure);
          const h = m.button.h / 3;
          if (Math.abs(h - FINGER_PX) > 0.5)
            failures.push(`${at} phone: buttons ${h.toFixed(1)} px high, not ${FINGER_PX}`);
          await phone.close();
        }
      }
    await browser.close();
    console.log(`${name}: checked`);
  }
  server.close();
  if (failures.length) {
    console.error(failures.join('\n'));
    process.exit(1);
  }
  console.log('map view: key, buttons, lines and the picked point keep their size at every zoom');
})();
