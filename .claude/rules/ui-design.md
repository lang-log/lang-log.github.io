---
paths:
  - "dist/**"
  - "tools/build_*.py"
  - "tools/components/**"
---

# UI design

How a new or changed piece of interface (a page, view, control, menu, popup, map or list) is designed, so every page looks and behaves like one site (owner's request, issue #90). Colours, interface text and the header are in `interface-text.md`, fonts in `fonts.md`, the logo in `logo.md`, browsers and touch in `web-browsers.md` (`research-aide`); this file does not repeat them.

## Reuse before adding

- Look for an existing component that does the same job and use it, with its class, before writing a new one: `docs/components.md` lists them, and each has its directory in `dist/components/`.
- The same job always gets the same component: one switch between views (`.seg` buttons with `aria-pressed`), one set of conditions over a list and a map (`conditions_html()` in `tools/components/conditions_panel.py`, run by `dist/components/explorer/explorer.js` on the top page and the record pages), with the map and the list shown together, the map first, at every width (the owner's decision: no switch between them), one Download menu (`download_menu()` in `tools/components/download_menu.py`, each entry named by its format: `SVG (current view)`, `XML`, `OPML`), one map (`.lmap`, mounted by `dist/components/map/map.js`), one search box and results list (`dist/components/search-results/search-results.js`).
- Every map behaves the same on every page (owner): the points' size (`pointPx()` in `dist/components/map/map.js`), outline and hover, the key under the map (`.lmap-key`), the locator (`locator()` in `tools/components/map.py`) and the frame (`dist/components/map/map.css`). Only how the points are written differs: record maps by `tools/build_paths.py`, the top page's map by `dist/components/explorer/explorer.js` (which also draws a record map's matching languages while a condition or a colour is set). Maps carry no caption; the sources are credited in the footer and on the Sources page.
- Every component lives in its own directory and pages only call it (the owner's request): its look in `dist/components/<name>/<name>.css`, its behaviour in `dist/components/<name>/<name>.js`, and the function that writes its markup in `tools/components/<snake_name>.py`. Page generators and hand-written pages never copy its markup, style or script; `docs/components.md` ("Where a component lives") has the details and `tools/check_components.py` the check.
- When a component is changed, change it in its directory so every page that uses it changes together; never restyle it for one page.
- `docs/components.md` names every component with its markup and the files that build and style it; a new or renamed component is added there in the same pull request.
- A new component gets its own directory: `dist/components/<name>/` with a comment at the top of its stylesheet that names it and the file that writes its markup, an entry in `STYLES` in `tools/components/__init__.py` (the place in the list is its place in the cascade), and its markup function in `tools/components/` when the build writes it. `dist/style.css` holds only the colour tokens, the fonts, the defaults of plain elements and the layout of the pages.

## Layout

- Design the phone layout (390 px wide) together with the desktop one; the phone rules sit in the `@media (max-width: 700px)` blocks next to the desktop rules they change. Nothing may scroll sideways.
- Motion goes inside `@media (prefers-reduced-motion: no-preference)`, and hover effects inside `@media (hover: hover)`.

## Look

- No shadows (the owner's rule): no `box-shadow`, `text-shadow` or `filter: drop-shadow()` on any page, component, popup or map, in either theme.
- No line under the header (the owner's rule). The footer puts each part (figures, sources, copyright, contact) on its own line, still centred, and the record pages' source credit lists one source per line (`FOOTER` in `tools/build_paths.py`), never one paragraph.
- No Download button with the word on it (the owner's rule): every Download button and menu shows the map's download symbol (`ICON_DOWNLOAD` in `dist/components/map/map.js`, written into pages by `download_icon()` in `tools/components/download_menu.py`), with `Download` only as its `aria-label` and `title`.

## Behaviour

- The map view keeps its buttons, its key and the map's lines the same size on the screen at every browser zoom and after zooming back (the owner's requests): they follow `--lmap-screen-grow` and `--lmap-screen-shrink` (`dist/components/map/map.css`, set by `screenScale()` in `dist/components/map/map.js`), never plain CSS pixels. `tools/check_map_view.js` (run by `site.yml`) checks it in Chromium, Firefox and WebKit, from 25% to 710%, with the picked point (`PICK_SHARE`) keeping its share of the other points; a new overlay on the map view gets the same scale and a line in that check.
- The map's buttons (`.lmap-tools`) stay inside the map at every browser zoom and width, on the page and in the map view (the owner's request): they wrap onto more rows, and a map shorter than the rows grows with them (`.lmap-wrap` in `dist/components/map/map.css`). `tools/check_map_view.js` checks it up to 2000%; never fix it for one zoom.
- Every page is readable without JavaScript. A control that needs a script is in the markup with `hidden` and the script shows it (the Random row, the top page's map); content is never only drawn by a script when the generator can write it.
- A state a visitor may want to share (view, conditions, selection, position) is kept in the query string, and `docs/urls.md` lists every parameter. A new parameter is added there in the same pull request.
- Toggle buttons carry `aria-pressed`; a button with only a symbol (`×`, `<`) carries an `aria-label`; groups of buttons are `role="group"` with an `aria-label`. These labels are interface text like any other (`interface-text.md`).
- Do not add a label, heading, hint or placeholder the owner did not ask for (`only-what-was-asked.md` in `research-aide`). A new component that needs text waits for the owner's wording.

## Before the pull request

- Look at the change in English, Japanese and Arabic, light and dark, at phone and desktop width, and say in the pull request that you did. The `browsers` workflow screenshots cover Chromium, Firefox and WebKit.
