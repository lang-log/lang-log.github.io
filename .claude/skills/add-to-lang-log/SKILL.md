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

## Which steps to read

Read the file for the kind of change, in full, before writing anything. A change of more than one kind reads each file.

- A UI component (page, view, control, menu, map layer): `references/component.md`. Every word it shows also follows `references/interface-text.md`.
- Interface text (any words a visitor sees): `references/interface-text.md`.
- Data (a source, field, feature, value or classification): `references/data.md`.

## Before pushing

1. `npm run check` on an unbuilt tree (`git checkout -- dist`), then `bash tools/build_site.sh` (`code-quality.md`).
2. Check the diff for anything private (`publishing.md`).
3. Open the pull request; for a visible change, say which languages, widths and themes you looked at, and point to the preview comment.
