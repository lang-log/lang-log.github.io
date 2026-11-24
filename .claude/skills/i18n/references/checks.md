# Checks

1. `python3 tools/build_i18n.py`: fails when a language lacks a key, has an extra or empty one, or uses a placeholder its English text lacks.
2. `npm run check` on an unbuilt tree, then `bash tools/build_site.sh` (`code-quality.md`).
3. Look at the page in English, Japanese and Arabic, at phone width (390 px) and desktop, light and dark (`ui-design.md`):
   - Japanese text uses Japanese glyphs and has no letter-spacing (`fonts.md`).
   - Arabic and Persian read right to left, with the layout mirrored (logical CSS properties only).
   - Long words (German, Russian, Vietnamese) wrap instead of widening the page.
4. The `browsers` workflow covers Chromium, Firefox and WebKit; look at its screenshots.
