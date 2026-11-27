# Fonts

The owner's rule (2026-11-07): every page, modal, popup, menu, tooltip and drawing uses the one font stack, in every interface language.

- The stack is `--font` on `:root` in `dist/style.css`: Arial for Latin text, then the fonts of the interface language for Japanese, Simplified and Traditional Chinese and Korean (`:lang(...)` rules next to it). `dist/lang.js` sets `<html lang>`, so the stack follows the language menu. Keep this per-language part when changing fonts.
- Never name a font anywhere else. CSS uses `var(--font)` or `inherit`; scripts that draw text (canvas, SVG export) read the page's font, as `siteFont()` in `dist/tree.js` does.
- Letter-spacing is for Latin text only; Japanese, Chinese and Korean text is set without it (the rule after `--font`). The header brand keeps its spacing in every language.
- The only exception is `.v-glyphs` in `dist/signs-and-scripts.css` (script samples, `serif`, then `var(--font-fallback)`).
- No empty boxes ("tofu") on a device without a font for a script (the owner's report, 2026-11-27, of a Duployan sample on Android): every stack ends with `var(--font-fallback)`, the site's own fallback fonts. `tools/fallback_fonts.py` (run by `tools/build_site.sh`) cuts the Noto fonts listed in `tools/fallback-fonts.json` down to the characters the built site uses and writes `dist/fonts/` and `dist/fonts.css`, which `dist/style.css` imports; each file has its `unicode-range`, so a browser downloads one only when a page has a character no font before it can draw. A new stack keeps `var(--font-fallback)` last. To take newer Noto fonts, run `python3 tools/fallback_fonts.py --update <commit of notofonts/notofonts.github.io>`; never edit the list by hand. The build prints the characters no listed font has (Han, Hangul and kana, which every system has, and scripts Noto does not cover yet).
- `tools/build_site.sh` fails when a style or script names a font outside `--font`.

## When adding a page, modal, popup or other new piece of interface

- Do not set `font`, `font-family` or `letter-spacing` on it unless the rules above allow it; a `<dialog>`, a popup built by a script and a new page all inherit `--font` from `body`.
- Before opening the pull request, look at it in Japanese and in English (and in one right-to-left language) at phone width, and check that the Japanese text uses Japanese glyphs, has no letter-spacing and matches the rest of the page. Say in the pull request that you checked.
- A new language with its own script (for example Thai or Hindi) that needs a font of its own gets a `:lang(...)` rule next to the others, not a font set on one element.
