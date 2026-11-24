---
name: i18n
description: Steps for adding, changing or removing Lang Log interface text in every interface language (i18n/<code>.yaml), including the draft for the owner, machine translation, checks and the right-to-left look. Use before touching any i18n/*.yaml file or any words a visitor sees.
---

# Interface text in every language

The rules live in `.claude/rules/interface-text.md` and in `languages.md`, `only-what-was-asked.md` and `generated-values.md` of `research-aide`; this skill only puts the steps in order and points to them. If a step here and a rule file disagree, the rule file wins: fix this skill in the same pull request. Data (record names, source titles, citations, codes) is not interface text and is never translated.

## Steps

Read each file below, in full, at its step. Every step is required.

1. The wording: `references/wording.md`. Without the owner's own words or an approved draft, stop here.
2. The keys in every `i18n/<code>.yaml`: `references/keys.md`.
3. The translations: `references/translations.md`.
4. The checks and the look in English, Japanese and Arabic: `references/checks.md`.
5. The pull request: `references/pull-request.md`.
