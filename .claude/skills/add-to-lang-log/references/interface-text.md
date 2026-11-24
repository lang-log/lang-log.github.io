# Interface text

Steps for adding interface text to Lang Log, moved from `SKILL.md` without changes (2026-11-24). Do the steps in `SKILL.md` under "Before any of the three" first.

1. Use the owner's wording; if there is none, show a draft and wait. A draft never names a data source (WALS, Glottolog, PHOIBLE ...) outside credits and citations (`interface-text.md`).
2. Add the English text to `i18n/en.yaml` and the same key to every other `i18n/<code>.yaml` (`LANGS` in `dist/lang.js`), in the same pull request. Counts and dates are placeholders (`{count}`, `{date}`), never typed numbers.
3. Run `python3 tools/build_i18n.py`; it fails when a language lacks the key or a placeholder.
4. Check Japanese and Arabic at phone width: no letter-spacing on Japanese, right-to-left layout correct.
