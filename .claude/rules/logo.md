# Logo

The owner's rule (2026-11-06): the Lang Log logo, the asterisk and the word mark "LANG LOG", is always the one SVG, everywhere in this repository.

- Draw it only with `<svg class="logo" role="img" aria-label="LANG LOG"><use href="logo.svg#logo"/></svg>` (with `../` as needed). This covers every page and page generator (`build_home.py`, `build_paths.py`, the atlas pages, `404.html`), the header and the large logo on the top page, both themes and both interface languages.
- Never write the logo as text, an emoji or a character (`✱ LANG LOG`, `★ LANG LOG`), and never draw the asterisk and the word mark separately.
- Colours come from CSS (`--teal` for the asterisk, `currentColor` for the word mark), so dark theme needs no second file. The interface language does not change the logo; the word mark stays "LANG LOG".
- To change the logo, edit `build_logo.py` and run it; it rewrites `dist/logo.svg` and the `.logo` aspect ratio in `dist/style.css`. Do not edit `dist/logo.svg` by hand.
- The `pages` workflow fails if a page in `dist/` lacks `logo.svg#logo` or writes "LANG LOG" as text.
- The favicon (`dist/favicon.svg`, `dist/apple-touch-icon.png`) is the asterisk alone and is not covered here.
