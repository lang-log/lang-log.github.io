# Text, fonts and data

## Interface languages

- Every interface language in `LANGS` (`dist/components/language-menu/language-menu.js`), not only English and Japanese: no English text left where a translation should be, including text a script writes, `aria-label`, `title` and `placeholder` (seen: labels stayed in English with Korean chosen).
- The longest translations (German, Russian, Vietnamese and others) fit their buttons and menus at 390 px.
- Switching the language on an open page changes every visible text, and the profile link under `yoshi` (`titles.md`).
- Numbers and dates in each language's own style, Persian digits in Persian (`interface-text.md`).
- No source names in interface text (`interface-text.md`), and no text the owner did not give (`only-what-was-asked.md` in `research-aide`).

## Fonts

- Japanese, Chinese and Korean pages use their own glyphs and no letter-spacing (`fonts.md`).
- Record names in rare scripts: on a device without a font for the script, the characters show as empty boxes (seen: Duployan names on an Android phone, not in CI). Check which scripts a page can show, and how the page looks when a font is missing.
- Thai, Hindi and other scripts in the interface with the fonts a phone has.

## Data

- A record with no data for a part of the page (no map point, no names, no features): the part is left out or shows the agreed empty state, never a broken frame.
- The longest names, the longest classification paths, the most items in a list or a menu, and one item only.
- Names in right-to-left scripts inside a left-to-right page, and the other way round.
- Many points on one spot of the map, points near the 180° line and near the poles.

## Without JavaScript, offline and as an app

- With JavaScript off, the page reads and scripted controls stay hidden (`ui-design.md`, "Behaviour").
- Offline, a page opened before opens again (`pwa.md`); a page never opened shows the browser's own error.
- Installed as an app (standalone display): the header and the full-screen map fit.
- A link with an old or wrong query (unknown condition, unknown id) does not break the page.
