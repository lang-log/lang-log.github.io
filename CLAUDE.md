# CLAUDE.md

@../research-aide/.claude/common.md

Lang Log (<https://lang-log.github.io/>): an atlas of language families, sign languages and writing systems, built from source data into static pages in `dist/` by the scripts in `tools/`, checked and deployed by GitHub Actions.

This file holds only the principles. The owner's shared rules come from the `research-aide` repository (imported above; clone it next to this repository). Rules only for this repository live in `.claude/rules/`.

If the shared rules are not in your context (the import above can be skipped, for example before external imports are approved or when `../research-aide` is missing), read `../research-aide/.claude/common.md` and every file it lists before doing anything else. If `../research-aide` does not exist, clone `nguekwang/research-aide` next to this repository first, or tell the owner.

## Principles

- **Only what was asked.** Do what the owner asked and nothing else (`only-what-was-asked.md` in `research-aide`). Never add page or interface text, descriptions, "coming soon" placeholders or features the owner did not ask for; when asked to explain or investigate, answer and stop, with no pull request.
- **Show the sources.** Every classification says which source it follows; alternative hypotheses are shown side by side, not merged away.
- **Static pages for now.** The site is plain files on GitHub Pages, with no server or database (the owner's decision, 2026-11-07; it may change later).
- **A progressive web app.** Lang Log is to become a progressive web app (PWA) (the owner's decision, 2026-11-08).
- **Simple and loosely coupled.** Always keep the structure as simple and as loosely coupled as possible (`simple-structure.md` in `research-aide`). Behaviour needed on several pages, such as the maps, is written once and shared, not rewritten per page.
- **Fix things once, at the source.** Page generators in `tools/`, shared style and scripts in `dist/`; never patch one generated page.
- **One look.** Every page is built from the same components; reuse one before adding a new one (`ui-design.md`).

## Where the rules are

- `.claude/rules/titles.md`: the ` by yoshi` title and the profile link, as used here.
- `.claude/rules/security.md`: the Content-Security-Policy and referrer policy on every page, and the headers GitHub Pages cannot send.
- `.claude/rules/license.md`: all rights reserved for the owner's work; third-party data keeps its own license.
- `.claude/rules/fonts.md`: one font stack for every page, modal and popup, per interface language; check the font whenever adding one.
- `.claude/rules/logo.md`: the Lang Log logo is always the one SVG.
- `.claude/rules/readable-code.md`: where each shared value is defined, and the check that finds copies.
- `.claude/rules/code-quality.md`: Prettier, ESLint and Ruff on every pull request and before every deployment.
- `.claude/rules/releases.md`: version tags, GitHub Releases and the Releases page.
- `.claude/rules/pwa.md`: the web app manifest, the service worker and what works offline.
- `.claude/rules/data.md` (`source-data/**`, `schema/**`, `tools/**`): Lang Log's own data, sources, languoids, features and classification.
- `.claude/rules/interface-text.md` (`dist/**`, `tools/**`): interface text in every interface language, colours, header.
- `.claude/rules/previews.md` (`.github/**`, `tools/build_site.sh`): pull request previews here.
- `.claude/rules/ui-design.md` (`dist/**`, `tools/build_*.py`): reusing components, phone layout, pages without JavaScript, shareable state, accessible controls.
- `.claude/skills/add-to-lang-log/`: the steps for adding a component, interface text or data.
- `.claude/skills/i18n/`: the steps for adding, changing or removing interface text in every interface language.
- `docs/`: the documentation (no GitHub Wiki): `docs/site.md` (how the pages work), `docs/data.md` (how the data is built), `docs/urls.md` (every address and query parameter) and `docs/components.md` (every UI component by name).
- Browsers: `.github/workflows/browsers.yml` runs the shared browser check (`browser-check.md` in `research-aide`) on every pull request; add a page there when a new kind of page appears.
