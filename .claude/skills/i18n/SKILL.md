---
name: i18n
description: Steps for adding, changing or removing Lang Log interface text in every interface language (i18n/<code>.yaml), including the draft for the owner, machine translation, checks and the right-to-left look. Use before touching any i18n/*.yaml file or any words a visitor sees.
---

# Interface text in every language

The rules live in `.claude/rules/interface-text.md` and in `languages.md`, `only-what-was-asked.md` and `generated-values.md` of `research-aide`; this skill only puts the steps in order and points to them. If a step here and a rule file disagree, the rule file wins: fix this skill in the same pull request. Data (record names, source titles, citations, codes) is not interface text and is never translated.

## 1. The wording

1. Use the owner's own words. If the owner gave none, write a draft in English and Japanese, show it in the thread (on the card and in a code block), and wait for approval before it goes into a pull request.
2. Before showing a draft, check it against `interface-text.md`: no source names, no record kinds, no counts or limits typed into the text. "Languoids" stays in English in every language.
3. Write nothing the owner did not ask for: no descriptions, help text or placeholders such as "coming soon".

## 2. The keys

1. Put the English text in `i18n/en.yaml` under a section and a key that say what it is (`info_pages.stats`). The English text itself is what `dist/lang.js` looks up on the page, so it must match the page's English exactly.
2. A value the page fills in is a placeholder: `{count}`, `{date}`, `{name}`; `{name|tr}` translates the value too. Where the default pattern does not fit, add an entry under `match` in `i18n/en.yaml`.
3. Add the same key to every other `i18n/<code>.yaml` (the languages are `LANGS` in `dist/lang.js`), in the same pull request. Never add a fallback to English.
4. Changing an English text: change it in `i18n/en.yaml` and in the page or script that shows it, and update every translation whose meaning changed. Removing a text: remove the key from every file.

## 3. The translations

1. English and Japanese are approved by the owner. Every other file starts with the comment `# Machine translated.`; Claude translates those languages, and nobody else reviews them.
2. Translate the meaning, not word by word, in the formal wording each language's interface uses. Keep every placeholder, in the place the language's word order needs.
3. Punctuation, brackets, quotation marks and list separators follow that language's current official documents (`languages.md`). Digits are never typed: `local()` in `dist/lang.js` writes numbers and dates (0-9, except ۰-۹ in Persian).
4. A name with no proper translation, and notation such as `SVO`, keeps the English text (WALS names: `interface-text.md`).

## 4. Checks

1. `python3 tools/build_i18n.py`: fails when a language lacks a key, has an extra or empty one, or uses a placeholder its English text lacks.
2. `npm run check` on an unbuilt tree, then `bash tools/build_site.sh` (`code-quality.md`).
3. Look at the page in English, Japanese and Arabic, at phone width (390 px) and desktop, light and dark (`ui-design.md`):
   - Japanese text uses Japanese glyphs and has no letter-spacing (`fonts.md`).
   - Arabic and Persian read right to left, with the layout mirrored (logical CSS properties only).
   - Long words (German, Russian, Vietnamese) wrap instead of widening the page.
4. The `browsers` workflow covers Chromium, Firefox and WebKit; look at its screenshots.

## 5. The pull request

1. Quote the approved English and Japanese wording, and say that the other languages are machine translated.
2. Say which languages, widths and themes you looked at, and point to the preview comment.
