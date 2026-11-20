---
paths:
  - "dist/**"
  - "tools/build_*.py"
---

# UI design

How a new or changed piece of interface (a page, view, control, menu, popup, map or list) is designed, so every page looks and behaves like one site (owner's request, issue #90). Colours, interface text and the header are in `interface-text.md`, fonts in `fonts.md`, the logo in `logo.md`, browsers and touch in `web-browsers.md` (`research-aide`); this file does not repeat them.

## Reuse before adding

- Look for an existing component that does the same job and use it, with its class, before writing a new one. Search the section comments of `dist/style.css`, which name the components and the files that build them, and the page styles `dist/explore.css` and `dist/record.css`.
- The same job always gets the same component: one switch between views (`.seg` buttons with `aria-pressed`, as `VIEWS` in `tools/build_home.py`), one Download menu (`details.menu.downloads` in `tools/build_paths.py`, each entry named by its format: `SVG (current view)`, `XML`, `OPML`), one map (`.lmap`, mounted by `dist/map-zoom.js`), one search box and results list (`dist/search.js`).
- When a component is changed, change it at its source (the generator in `tools/` or the shared script and style in `dist/`) so every page that uses it changes together; never restyle it for one page.
- `docs/components.md` names every component with its markup and the files that build and style it; a new or renamed component is added there in the same pull request.
- A new component gets a section comment in the stylesheet that names it and the file that builds it. Put it in `dist/style.css` when more than one page can use it, otherwise in the page's own stylesheet.

## Layout

- Design the phone layout (390 px wide) together with the desktop one; the phone rules sit in the `@media (max-width: 700px)` blocks next to the desktop rules they change. Nothing may scroll sideways.
- Motion goes inside `@media (prefers-reduced-motion: no-preference)`, and hover effects inside `@media (hover: hover)`.

## Behaviour

- Every page is readable without JavaScript. A control that needs a script is in the markup with `hidden` and the script shows it (the Random row, the view switch); content is never only drawn by a script when the generator can write it.
- A state a visitor may want to share (view, conditions, selection, position) is kept in the query string, and `docs/urls.md` lists every parameter. A new parameter is added there in the same pull request.
- Toggle buttons carry `aria-pressed`; a button with only a symbol (`×`, `<`) carries an `aria-label`; groups of buttons are `role="group"` with an `aria-label`. These labels are interface text like any other (`interface-text.md`).
- Do not add a label, heading, hint or placeholder the owner did not ask for (`only-what-was-asked.md` in `research-aide`). A new component that needs text waits for the owner's wording.

## Before the pull request

- Look at the change in English, Japanese and Arabic, light and dark, at phone and desktop width, and say in the pull request that you did. The `browsers` workflow screenshots cover Chromium, Firefox and WebKit.
