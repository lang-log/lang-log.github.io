# What CI already checks

Read this first, so you check by hand only what is left. Each line names the check; its file says exactly what it does.

## Already checked on every pull request

- `browsers.yml` (shared `browser-check.yml` in `research-aide`): every page listed there, in Chromium, Firefox and WebKit, at 1280 px and at 390 px with touch, light and dark, with an English and a Japanese browser. Fails on sideways scrolling, JavaScript and console errors (Content-Security-Policy violations included) and missing files. It looks only at the top of each page after it loads; it does not press anything.
- `tools/check_map_view.js` (`site.yml`): the map view on a record page and on the top page, in the three engines, from 25% to 710% browser zoom and back, in English light and Arabic dark. Fails when the key, the buttons or the map's lines change size on the screen, when the picked point loses its share, when a button on a phone is under 44 px, or when a map button is not wholly inside the map (up to 2000%).
- `tools/build_site.sh`: fonts named outside `--font`, pages without the SVG logo or with a text logo, kind labels, record maps that read a record's kind, unversioned asset links, the security policy (`tools/security_policy.py --check`), the manifest and service worker (`tools/pwa.py --check`), the brand text (`tools/site_brand.py --check`), the component directories (`tools/check_components.py --check`) and copies of shared values (`tools/check_single_source.py`).
- `tools/build_i18n.py`: a language without a key, or with a placeholder its English text lacks.
- `quality.yml`: Prettier, ESLint, markdownlint, html-validate, Stylelint, ShellCheck and Ruff.

## Not checked by any script yet (check by hand)

- Whether controls other than the map's buttons (menus, popups, the conditions panel) stay inside their frame at high zoom.
- Anything after a press, a tap, a drag or a key: states that stay on, menus that do not close, focus that is lost.
- Text left in English in the other interface languages (a key can exist and still hold English, or a script can write English text).
- Characters the visitor's device has no font for (shown as empty boxes).
- Pages not listed in `browsers.yml`, languages other than English and Japanese, and right-to-left pages outside the map check.
- Slow networks and slow devices, and presses made before a script has finished.
