// Temporary diagnosis for the Firefox 25% pick failure; removed before review.
/* global window, document -- runs in the page */
const { firefox } = require('playwright'),
  { serve } = require('./serve_dist');
(async () => {
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  const b = await firefox.launch();
  for (let run = 0; run < 4; run++)
    for (const zoom of [1.5, 0.25, 0.5]) {
      const ctx = await b.newContext({
        viewport: { width: Math.round(1920 / zoom), height: Math.round(960 / zoom) },
        deviceScaleFactor: zoom,
        locale: 'en-US',
        colorScheme: 'light',
      });
      const tab = await ctx.newPage();
      tab.on('pageerror', (e) => console.log('pageerror', e.message));
      tab.on('console', (m) => console.log('console', m.type(), m.text()));
      await tab.addInitScript(() => {
        window.__log = [];
        const t0 = performance.now();
        const ev = (n) => window.__log.push(n + ' ' + Math.round(performance.now() - t0));
        window.__ev = ev;
        const iv = setInterval(() => {
          const s = document.querySelector('.lmap-full svg.lmap');
          if (s && s.__lmap) {
            const r = s.__lmap.refresh;
            s.__lmap.refresh = function () {
              ev('refresh');
              return r.apply(this, arguments);
            };
            ['pointerdown', 'pointerup', 'click'].forEach((t) =>
              s.addEventListener(
                t,
                (e) => ev(t + '@' + e.clientX + ',' + e.clientY + ' ' + e.target.tagName),
                true,
              ),
            );
            clearInterval(iv);
          }
        }, 1);
        document.addEventListener('langchange', () => ev('langchange'));
      });
      const t = Date.now();
      await tab.goto(base + '/?view=map#map-view', { waitUntil: 'networkidle' });
      await tab.waitForFunction(() => document.querySelector('.lmap-full'), null, {
        timeout: 15000,
      });
      await tab.waitForTimeout(300);
      const at = await tab.evaluate(() => {
        const ps = document.querySelectorAll(
          '.lmap-full circle[data-g], .lmap-full .lmap-ctx rect[data-g]',
        );
        let n = 0;
        for (const p of ps) {
          const r = p.getBoundingClientRect(),
            x = r.left + r.width / 2,
            y = r.top + r.height / 2;
          if (x > 0 && y > 0 && x < window.innerWidth && y < window.innerHeight) {
            n++;
            const hit = document.elementFromPoint(x, y);
            if (hit === p)
              return {
                x,
                y,
                n,
                total: ps.length,
                w: r.width,
                iw: window.innerWidth,
                dpr: window.devicePixelRatio,
              };
          }
        }
        return {
          none: true,
          n,
          total: ps.length,
          iw: window.innerWidth,
          dpr: window.devicePixelRatio,
        };
      });
      const loaded = Date.now() - t;
      let ok = false;
      if (!at.none) {
        await tab.evaluate(() => window.__ev('click-sent'));
        await tab.mouse.click(at.x, at.y);
        ok = await tab
          .waitForFunction(() => document.querySelector('.lmap-full .lmap-picked'), null, {
            timeout: 5000,
          })
          .then(
            () => true,
            () => false,
          );
        if (!ok)
          ok = await tab
            .waitForFunction(() => document.querySelector('.lmap-full .lmap-picked'), null, {
              timeout: 30000,
            })
            .then(
              () => 'late',
              () => false,
            );
      }
      const log = await tab.evaluate(() => ({
        log: window.__log,
        pop: !!document.querySelector('.lmap-pop:not([hidden])'),
      }));
      console.log(JSON.stringify({ run, zoom, loaded, at, ok, ...log }));
      await ctx.close();
    }
  await b.close();
  server.close();
})();
