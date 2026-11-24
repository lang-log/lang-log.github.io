# The keys

1. Put the English text in `i18n/en.yaml` under a section and a key that say what it is (`info_pages.stats`). The English text itself is what `dist/lang.js` looks up on the page, so it must match the page's English exactly.
2. A value the page fills in is a placeholder: `{count}`, `{date}`, `{name}`; `{name|tr}` translates the value too. Where the default pattern does not fit, add an entry under `match` in `i18n/en.yaml`.
3. Add the same key to every other `i18n/<code>.yaml` (the languages are `LANGS` in `dist/lang.js`), in the same pull request. Never add a fallback to English.
4. Changing an English text: change it in `i18n/en.yaml` and in the page or script that shows it, and update every translation whose meaning changed. Removing a text: remove the key from every file.
