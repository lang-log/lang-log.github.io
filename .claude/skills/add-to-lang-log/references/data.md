# Data

Steps for adding data to Lang Log, moved from `SKILL.md` without changes (2026-11-24). Do the steps in `SKILL.md` under "Before any of the three" first.

1. A new source: keep its files in `source-data/` as published and list it in `source-data/sources.json` (version, retrieval date, license, address, files). Check its license first (`license.md`).
2. Convert it in its own function in `tools/build_languoids.py`, writing only that source's values, into the shape of `schema/languoid.schema.json`. Never give a family, language or dialect a shape of its own.
3. A new field or feature changes the schema, the converter and the section "Lang Log data" in `docs/data.md` together.
4. The owner's own values go under source `lang-log` with a reference (`source-data/lang-log/`).
5. Never type a count, list or other derived value; let the build compute it (`generated-values.md`).
