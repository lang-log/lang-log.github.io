---
name: add-to-lang-log
description: Steps for adding to Lang Log a UI component (page, view, control, menu, map layer), interface text (any words a visitor sees), or data (a source, field, feature, value or classification). Use before writing any of these.
---

# Adding a component, interface text or data to Lang Log

The rules live in `CLAUDE.md`, `.claude/rules/` and the shared rules of `research-aide`; this skill only puts the steps in order and points to them. If a step here and a rule file disagree, the rule file wins: fix this skill in the same pull request.

## Before any of the three

1. Check that the owner asked for exactly this (`only-what-was-asked.md`). New words, labels or placeholders the owner did not give wait for their approval.
2. Read the rule files the change touches, including the path-scoped ones that load only when a matching file is opened: `interface-text.md`, `ui-design.md` (for `dist/**`, `tools/**`), `data.md` (for `source-data/**`, `schema/**`, `tools/**`).
3. Branch from the latest `main`.

## A. A UI component

1. Look for an existing component that does the job (`docs/components.md`; `ui-design.md`, "Reuse before adding"). If one exists, use it and stop here.
2. Write the markup in the page generator (`tools/build_home.py`, `tools/build_paths.py`, ...) or the shared script in `dist/`, never in one generated page. Hand-written pages (`dist/*.html`) keep the security policy: run `python3 tools/security_policy.py --write` if their `<head>` changed.
3. Style it with the colour tokens and `--font` only (`interface-text.md`, `fonts.md`), in `dist/style.css` or the page's stylesheet, under a section comment that names it.
4. Without JavaScript the page still reads; a scripted control starts `hidden` (`ui-design.md`, "Behaviour").
5. If it keeps a state worth sharing, put it in the query string and add the parameter to `docs/urls.md`.
6. Every word it shows, and every `aria-label`, goes through step B.
7. If the value it needs already exists elsewhere (a size, a duration, a colour), read it from its source (`readable-code.md`); a new shared value gets an entry in `tools/single-source.json`.
8. A new kind of page gets a line in `.github/workflows/browsers.yml` and in `docs/urls.md`.
9. Add the component to `docs/components.md`.

## B. Interface text

1. Use the owner's wording; if there is none, show a draft and wait. A draft never names a data source (WALS, Glottolog, PHOIBLE ...) outside credits and citations (`interface-text.md`).
2. Add the English text to `i18n/en.yaml` and the same key to every other `i18n/<code>.yaml` (`LANGS` in `dist/lang.js`), in the same pull request. Counts and dates are placeholders (`{count}`, `{date}`), never typed numbers.
3. Run `python3 tools/build_i18n.py`; it fails when a language lacks the key or a placeholder.
4. Check Japanese and Arabic at phone width: no letter-spacing on Japanese, right-to-left layout correct.

## C. Data

1. A new source: keep its files in `source-data/` as published and list it in `source-data/sources.json` (version, retrieval date, license, address, files). Check its license first (`license.md`).
2. Convert it in its own function in `tools/build_languoids.py`, writing only that source's values, into the shape of `schema/languoid.schema.json`. Never give a family, language or dialect a shape of its own.
3. A new field or feature changes the schema, the converter and the section "Lang Log data" in `docs/data.md` together.
4. The owner's own values go under source `lang-log` with a reference (`source-data/lang-log/`).
5. Never type a count, list or other derived value; let the build compute it (`generated-values.md`).

## Before pushing

1. `npm run check` on an unbuilt tree (`git checkout -- dist`), then `bash tools/build_site.sh` (`code-quality.md`).
2. Check the diff for anything private (`publishing.md`).
3. Open the pull request; for a visible change, say which languages, widths and themes you looked at, and point to the preview comment.
