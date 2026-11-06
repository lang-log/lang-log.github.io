---
paths:
  - "dist/**"
  - "build_*.py"
---

# Interface text and colours

- Every page loads `theme.js`, `i18n.js` and `lang.js` in `<head>`, after `style.css`. A new page or page generator does the same.
- Write interface text in English. Add the Japanese for every new string to `dist/i18n.js` (`exact`, or `patterns` when the text holds a number or a name) in the same pull request. Data (record names, source titles, citations, codes) is not translated; mark an element `notranslate` if its text could be mistaken for interface text.
- Use only the colour variables at the top of `dist/style.css`. A new colour gets a `--c-<light hex>` variable with a light value and a dark value in both dark blocks.
- Keep the header as the brand on the left and one element on the right; the scripts put the theme toggle and the language menu after that element.
