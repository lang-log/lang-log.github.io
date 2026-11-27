# License

The owner's decision (2026-11-07): Lang Log is not open source. The repository stays public, but nothing in it may be reused.

- `LICENSE` is an "All rights reserved" notice for the owner's own work: code, templates, styles, scripts, logo and design, site text, and data compiled for Lang Log. No license is granted, commercial or non-commercial. It replaces AGPL-3.0-only; versions published before then stay AGPL for those who received them.
- Third-party data (Glottolog, WALS, SIL, Power et al. and any later source) keeps its own license and is never covered by the notice. Keep each source's attribution and license in `dist/signs-and-scripts-licenses.txt`, the site's source registers and `source-data/`. A new source needs its license checked first; a share-alike or copyleft source (CC BY-SA, GPL) must stay a separate, clearly marked component.
- Do not add an open-source license, a `SPDX-License-Identifier` header or open-source wording to code, pages or descriptions without the owner's decision.
- Share-alike and non-commercial sources (the owner's decision, 2026-11-23: take them all in): LinguaMeta (CC BY-SA 4.0) and D-PLACE (CC BY-NC 4.0) are read by their own functions in `tools/record_facts.py`, every value from them carries its source (`linguameta`, `dplace`) in `languoid.json`, and the record page footer names them with their licenses. Those values stay under their own license; the notice never covers them.
- Lang Log will charge only for its learning features (the owner, 2026-11-23). Never use non-commercial data (D-PLACE, or any later CC BY-NC source) in a paid feature; check each source's license before a paid feature reads it.
- The fallback fonts (`fonts.md`) are Noto fonts under the SIL Open Font License 1.1: the site serves them cut down, with the license as `dist/fonts/LICENSE` and the copyright and license entries kept in each file. The notice never covers them.
- The ISO 639-3 code tables are not kept in `source-data/`: their terms of use (iso639-3.sil.org) do not allow a product to redistribute the code set.
