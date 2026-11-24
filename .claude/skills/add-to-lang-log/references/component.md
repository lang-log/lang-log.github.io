# A UI component

Steps for adding a ui component to Lang Log, moved from `SKILL.md` without changes (2026-11-24). Do the steps in `SKILL.md` under "Before any of the three" first.

1. Look for an existing component that does the job (`docs/components.md`; `ui-design.md`, "Reuse before adding"). If one exists, use it and stop here.
2. Write the markup in the page generator (`tools/build_home.py`, `tools/build_paths.py`, ...) or the shared script in `dist/`, never in one generated page. Hand-written pages (`dist/*.html`) keep the security policy: run `python3 tools/security_policy.py --write` if their `<head>` changed.
3. Style it with the colour tokens and `--font` only (`interface-text.md`, `fonts.md`), in `dist/style.css` or the page's stylesheet, under a section comment that names it.
4. Without JavaScript the page still reads; a scripted control starts `hidden` (`ui-design.md`, "Behaviour").
5. If it keeps a state worth sharing, put it in the query string and add the parameter to `docs/urls.md`.
6. Every word it shows, and every `aria-label`, goes through `references/interface-text.md`.
7. If the value it needs already exists elsewhere (a size, a duration, a colour), read it from its source (`readable-code.md`); a new shared value gets an entry in `tools/single-source.json`.
8. A new kind of page gets a line in `.github/workflows/browsers.yml` and in `docs/urls.md`.
9. Add the component to `docs/components.md`.
