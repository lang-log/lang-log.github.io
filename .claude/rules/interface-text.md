---
paths:
  - "dist/**"
  - "tools/**"
---

# Interface text and colours

- Every page loads `theme.js`, `i18n.js` and `lang.js` in `<head>`, after `style.css`. A new page or page generator does the same.
- Link local CSS, JS and SVG files by plain relative paths (`style.css`, `../logo.svg#logo`). `tools/version_assets.py` adds `?v=<content hash>` to them in CI so browsers never mix a new page with an old cached file; do not add a query by hand.
- Lang Log offers the same 21 languages as the profile site, in the same order (`LANGS` in `dist/lang.js`). Write interface text in English. Add every new string to all 20 dictionaries in the same pull request: Japanese in `dist/i18n.js`, the others in `dist/i18n/<code>.js` (`exact`, or `patterns` when the text holds a number or a name). `tools/check_i18n.js` fails CI when a language lacks a string.
- Numbers and dates captured by a pattern are written by `Intl` in each language's own style (`local()` in `dist/lang.js`); digits are 0-9 everywhere except Persian (۰-۹). Arabic and Persian pages get `dir="rtl"`, so use logical CSS properties (`inset-inline-end`, `margin-inline-start`, `text-align: start`) rather than left and right. Data (record names, source titles, citations, codes) is not translated; mark an element `notranslate` if its text could be mistaken for interface text.
- Use only the colour variables at the top of `dist/style.css`. A new colour gets a `--c-<light hex>` variable with a light value and a dark value in both dark blocks.
- Keep the header as the brand on the left and one element on the right; the scripts put the theme toggle and the language menu after that element.
