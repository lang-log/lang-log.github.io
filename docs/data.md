# The data

How Lang Log's data is built from its sources, and what the pages load. The rules Claude follows for the data are in `.claude/rules/data.md`.

## Lang Log data

Lang Log keeps its own data in one shape for every record, whatever source it comes from. Glottolog, WALS and the other datasets are references: their files stay in `source-data/` as they were published (listed with version, license and download address in `source-data/sources.json`), and the build converts them. Only the converted data is deployed; it is not committed.

- `tools/build_languoids.py` (run by `tools/build_site.sh` after `tools/build_paths.py`) writes `languoid.json` next to every record page, for every Glottolog record and every WALS language Glottolog lacks: for example `https://lang-log.com/japonic/japanesic/japan-taiwan-japanese/japanese/languoid.json`. The shape is `schema/languoid.schema.json` (also served at `schema/`); the build checks every file against it and stops on the first that does not match.
- Every record is a languoid. Lang Log does not sort them into families, languages, dialects or clades; a languoid's place is its parent in each source (`classification.<source>.parent`), and what a source calls it is that source's claim (`classification.<source>.level`, such as Glottolog's `family`, `language` or `dialect`).
- The only labels Lang Log gives a languoid itself are `modality` (`spoken`, `signed`, `written`) and `constructed` (an artificial or formal language). Every languoid of every modality belongs to one tree. Every page shows both as its "Medium" (such as "Medium: spoken · constructed"). `tools/modality.py` sets them, for now from the Glottolog group a record is listed under ("Sign Language": signed; "Artificial Language": constructed; writing systems in the signs-and-scripts data: written), read before the groups are left out of the tree.
- Every value says where it came from. Names, classification and location carry their source; a feature value keeps all its evidence (source, version, the source's own feature id and value, reference, comment) and `value` is chosen from it by source priority (the owner's own values, then WALS). When sources disagree, `disagreement` is set and every value is kept.
- Features are Lang Log's own (`source-data/lang-log/features.json`, shape `schema/features.schema.json`). The catalogue started as the WALS features; each feature has its own value ids and `mappings` from each source's feature and values. A language without WALS data has the same features; a feature without data is left out of its file. `dist/features/index.json` lists the features with counts, and `dist/features/<feature id>.json` holds the value of every record that has one.
- Some groups a source lists are not languoids: they are catalog groupings by modality, status or source languages, not families with a common ancestor. All of Glottolog's top-level groups of this kind (Sign Language, Pidgin, Mixed Language, Speech Register, Artificial Language, Unattested, Unclassifiable, Bookkeeping) and the groups inside them (such as "L1 Sign Language", "French-based pidgin", "Arawakan (Unattested)"), and WALS's "other" family with its "Sign Languages" and "Creoles and Pidgins" genera, are listed in `source-data/lang-log/not-languoids.json` and left out of the tree by `tools/not_languoids.py`. Their members move up to the nearest real ancestor or become top-level languoids, and keep the group's name as the source's claim (`classification.<source>.grouping`). Real groups of related varieties inside them (Esperantic, Scandinavian Romani, Upcountry Swahili) stay. `tools/check_not_languoids.py` fails the build when a listed group is back.
- Lang Log's own classification is `source-data/lang-log/classification.json`: the parent of a languoid where Lang Log places it differently from Glottolog, curated by hand. For now it places each historical stage as the parent of the later language (Old English → Middle English → English); Glottolog has no such relation. It becomes `classification.lang-log.parent` in `languoid.json`, next to Glottolog's, and never replaces it.
- Facts beyond the tree come from more sources, each read by its own function in `tools/record_facts.py`, which the record pages and `languoid.json` share: Glottolog's values (`source-data/values.csv`, `codes.csv`: `endangerment`, Glottolog's agglomerated endangerment status, and `description`, the most extensive description with its reference), the IANA Language Subtag Registry (`source-data/iana/`: `registry`, the language tag of the record's ISO 639-3 code, its scope, macrolanguage, the tag that replaced it, the retired tags it replaced and the script its tags leave out) and Unicode CLDR (`source-data/cldr/`: `scripts`, `speakers_by_country` with each country's official status, and `plural_categories`), LinguaMeta (`source-data/linguameta/linguameta.tsv`, CC BY-SA 4.0: `linguameta`, the estimated number of speakers, scripts, an endangerment status, the ISO 639-2/B code and the Wikidata item; its scripts that CLDR and the registry lack are added to `scripts`), PHOIBLE (`source-data/phoible/phoible.csv`: `phonemes`, each inventory's consonants, vowels and tones) and D-PLACE (`source-data/dplace/societies.csv`, CC BY-NC 4.0: `societies`). Share-alike and non-commercial values keep their source on every value (`.claude/rules/license.md`). CLDR names a language by its shortest code (`jpn` is `ja`); its macrolanguage codes are not followed, since their figures cover the whole macrolanguage. Records without a code in a source get the same fields, empty or null.
- The ISO 639-3 code tables themselves are not kept: their terms of use (iso639-3.sil.org) do not allow a product to redistribute the code set. The codes Lang Log shows come from Glottolog, WALS and the IANA registry.
- To take in a new release of a source, replace its files in `source-data/`, update `source-data/sources.json` and build. If WALS has a feature or value the catalogue lacks, the build stops; run `python3 tools/feature_catalogue.py`, which appends the missing ones and never changes existing entries. Then add the new names under `wals_features` or `wals_values` in every `i18n/<code>.yaml`; `tools/build_i18n.py` stops until they are there.

## What each page generator reads

- `tools/build_paths.py` (record pages) reads `dist/data.json` and `dist/integrated.json`, Glottolog's `source-data/languages.csv` (map points, countries, years of documentation), `source-data/iso-map.json`, WALS's `source-data/wals/` (feature values), the facts of `tools/record_facts.py` and Lang Log's own `source-data/lang-log/classification.json`.
- `tools/build_wals_map.py` (the top page's map and its conditions, `dist/data/features/`) reads WALS's `source-data/wals/` and `source-data/wals.csv`, Glottolog's `source-data/languages.csv`, `dist/data.json` and `dist/integrated.json`. Its other conditions come from `tools/condition_features.py`, which also reads `source-data/lang-log/classification.json` and the sign language groups in `source-data/signs-and-scripts/power-languages.csv`. `tools/build_home.py` uses it for the top page, and also reads `source-data/sources-and-scope.html`.
- Lang Log's own data (`languoid.json`, `dist/features/`) is written for download; no page generator reads it yet.

## Rebuild

`tools/build_site.sh` runs `tools/build_data.py`, `tools/enrich.py`, `tools/unify.py` and `tools/finish_unified.py` on every build. They read only `source-data/` and write `dist/data.json`, `dist/integrated.json`, `dist/provenance.json`, `dist/language-families.xml` and `dist/language-families.opml`; none of these is committed.

## Integration model

Every Glottolog record is kept, except the catalog groupings listed in `source-data/lang-log/not-languoids.json` (see Lang Log data). WALS and the Phlorest data repositories discovered on 2026-10-12 contribute source-conditioned assertions. The software and .github repositories are not data sources. All summary trees are imported; posterior tree samples are not. The D-PLACE catalog was used for discovery only; phylogeny data came directly from each original Phlorest repository.

Exact Glottocodes share one canonical record. Unmatched study samples and internal clades retain source-specific identities. Repeated samples preserve original labels on their edges. No anonymous study clade is claimed to be an accepted named family. Same-language labels remain as documented in provenance.

The outline embeds alternative study branches into Glottolog navigation. Those attachments are display context, not genetic ancestry assertions. Each source branch expands only that source's edges. The tree diagram uses dashed navigation attachments and source-tagged occurrences of shared identities.

Automatic conflicts are crossing, non-nested rooted clades after restricting two summary trees to shared exact, non-repeated, non-ancestor tip IDs. Sampling differences, missing taxa and polytomies alone are not conflicts. These are computational comparisons of imported summary topologies, not a review of statistical uncertainty or scientific validity. The Transeurasian paper-level debate is separately curated with proposal, critique and response.

This is not every publication worldwide. See the Sources page and `provenance.json` for exact coverage, per-source licenses, hashes and remaining gaps. No unreviewed node is labeled consensus solely because no alternative has been imported.

## Exports

XML schema v3 uses canonical nodes, named sources, source-conditioned placement assertions, conflict witnesses and paper debates. OPML repeats shared references to provide a hierarchical outline; node-id and source preserve their identity. SVG is a view export, not the authoritative graph model.

## Sign languages and writing systems

`tools/build_site.sh` builds this data with `tools/build_visual.py` and checks it with `tools/validate_visual.py` on every build; `dist/signs-and-scripts.json`, `.xml` and `.opml` are not committed.

Coverage: every Glottolog sign-language record (including families and dialects; the catalog groups that are not languoids are left out, see Lang Log data), the Power et al. CLDF manual-alphabet samples, the Abner et al. consensus trees, the downloaded ISO 15924 table and the SIL Scripts Index. Exact script codes are merged; SIL-local IDs remain distinct. The counts of each are in `counts` in `dist/signs-and-scripts.json`; they measure different units and do not establish exhaustive coverage of world literature or all proposed genealogies.

The Abner European trees are independent replicates, not independent publications. Historical manual-alphabet samples retain separate identities and only link to Glottocodes when explicitly mapped in the dataset. A manual-alphabet grouping is not treated as a whole-language genealogy. Broad script ancestry retains the qualifier “intermediate stages omitted”. Ledyard’s proposed Phags-pa influence is linked to the thesis and explicitly accompanied by Lee’s criticism. Brahmi origin accounts appear together with separate citations.

JSON and XML preserve all fields, assertions, source metadata, notes, usage and input checksums. XML uses typed `field`/`item` elements and is tested by exact JSON round-trip. OPML repeats references under alternate parents and preserves assertion citations, but does not carry the full metadata or usage table. Glottolog alias provider/language tags remain intact. Unicode letter samples are not labeled as native names.

`tools/validate_visual.py` checks catalog coverage, mappings, acyclic relationships, complete OPML reachability and XML round-trip. Source files and their original licenses remain attributed: `source-data/signs-and-scripts/input-provenance.json` and `dist/signs-and-scripts-licenses.txt`.

## Page data

The record pages, the top page and `record.html` do not load `data.json` and `integrated.json`; those stay as downloads. `tools/split_data.py` writes smaller files to `dist/data/` (built by the Pages workflow, not committed), and `dist/atlas-data.js` rebuilds the same objects from them in the browser:

- `data/atlas.json`: the tree, native names, sources, study trees and conflicts. Glottolog records are stored as columns, and values the browser can recompute (ids inside records, children, root, size, Glottolog assertions, placements) are left out.
- `data/names/<n>.json`: recorded names and spellings, split into `SHARDS` files (set in `dist/atlas-data.js`) by a hash of the record id. A page loads one when it shows a record's names.
- `data/search.json`: the text of all recorded names. It loads after the tree is shown, so searching by an alternative name (for example 日本語) works a moment later than searching by name, Glottocode or ISO code.

The WALS genus lists in `data.json` are not used by the pages and are not in these files. `tools/split_data.py` rebuilds the objects the same way and stops if anything differs from `data.json` and `integrated.json`.
