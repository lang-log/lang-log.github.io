# The translations

1. English and Japanese are approved by the owner. Every other file starts with the comment `# Machine translated.`; Claude translates those languages, and nobody else reviews them.
2. Translate the meaning, not word by word, in the formal wording each language's interface uses. Keep every placeholder, in the place the language's word order needs.
3. Punctuation, brackets, quotation marks and list separators follow that language's current official documents (`languages.md`). Digits are never typed: `local()` in `dist/lang.js` writes numbers and dates (0-9, except ۰-۹ in Persian).
4. A name with no proper translation, and notation such as `SVO`, keeps the English text (WALS names: `interface-text.md`).
