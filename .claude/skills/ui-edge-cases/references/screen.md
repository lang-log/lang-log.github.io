# Screen: zoom, width, theme, direction

## Browser zoom and text size

- From 25% to the largest zoom a browser offers (the map check goes to 710%), every control stays inside its frame: the map's key inside the map, menus and popups inside the window, nothing cut off at an edge. The map's buttons are checked by `tools/check_map_view.js` (seen: at 667% they stood out of the map).
- After zooming in and back out, everything returns to where it was.
- The map view keeps its buttons, key and lines the same size on the screen (`ui-design.md`, "Behaviour").
- With a larger default font size in the browser settings, text wraps instead of overlapping or being cut.

## Width and orientation

- 320 px (the narrowest common phone), 390 px, 700 px and 701 px (each side of the phone rules), a tablet, 1280 px and a very wide window.
- A phone turned sideways (wide and short): sticky parts and the map view still leave room for the content.
- Nothing scrolls sideways; long names and URLs wrap (`web-browsers.md` in `research-aide`).
- The full-screen map and any `100vh` part on iOS Safari, with the toolbar shown and hidden.

## Theme

- Light and dark, and switching between them on an open page (map, menus, popups and drawn SVG follow).
- Colours come only from the tokens in `dist/style.css`; no shadows anywhere (`ui-design.md`, "Look").
- The browser's forced colours (Windows high contrast): controls and their borders stay visible.

## Direction

- A right-to-left language (`rtl` in `LANGS`, `dist/components/language-menu/language-menu.js`): order of buttons, arrows that point the right way, padding on the right side, the map's tools and key in the mirrored place.
- Switching between a left-to-right and a right-to-left language on an open page.

## Drawn and printed

- Map symbols are the SVG icons, never text characters (`ui-design.md`), so they look the same on every device.
- Downloaded images (SVG, PNG of the map) in both themes and in a right-to-left language.
- Printing a record page: nothing cut off, no dark background.
