# How to set up each case

Use Playwright as the CI checks do (`tools/check_map_view.js`, `browser_check.py` in `research-aide`); serve `dist/` with `tools/serve_dist.js`. Take screenshots you only look at yourself at `deviceScaleFactor: 1`.

- Browser zoom `z` on a screen `W` device pixels wide: a window `W / z` CSS pixels wide with `deviceScaleFactor: z` (as in `tools/check_map_view.js`).
- Phone: `viewport` 390 × 844, `hasTouch: true`, `isMobile: true` (Chromium and WebKit; Firefox has no mobile mode, so use a narrow window there). Use `page.tap()`, not `click()`, for touch.
- A stuck pressed state: tap the control, then read its computed background and border and compare them with a control never pressed (`getComputedStyle`).
- Theme: `colorScheme: 'dark'`; then press the theme toggle on the open page.
- Interface language: choose it in the language menu, or open the page with the browser `locale` set.
- Reduced motion and forced colours: `reducedMotion: 'reduce'`, `forcedColors: 'active'`.
- Keyboard: `page.keyboard.press('Tab')` and read `document.activeElement`.
- Slow network: delay responses with `page.route()`; press controls before `load`.
- Slow device: in Chromium, `Emulation.setCPUThrottlingRate` through a CDP session.
- JavaScript off: `javaScriptEnabled: false`.
- Offline: `context.setOffline(true)` after a first visit.
- Missing fonts cannot be reproduced in CI, where the browsers have their own fonts. Find the characters a page shows outside the scripts the font stack covers, and say in the pull request that a real device was not checked.
- Real devices (an Android phone, an iPhone, Safari on a Mac): only the owner can try these; list what to look at in the report.
