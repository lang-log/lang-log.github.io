# Languer

An interactive atlas of language families, sign languages and writing systems, with source-linked classifications, alternative hypotheses and exportable data.

Live site: https://atlas-of-language-families.agileduck5.chatgpt.site

## Run locally

Serve the static site with `python -m http.server 8000 --directory dist`, then open http://localhost:8000. No build step is required for the checked-in site.

Source datasets keep their own licenses and attribution. See `dist/visual-atlas-licenses.txt`, the source registers in the site and the documentation below.

## Cloudflare Pages

Connect this repository, select `main`, use framework preset `None`, set the build command to `python3 prepare_static.py`, and set the output directory to `dist`. No environment variables or secrets are required by the site.

---

# Integrated Language Atlas

## Rebuild

Run `python build_data.py`, `python enrich.py`, `python unify.py`, then `python finish_unified.py`. Serve `dist/` as static files.

## Integration model

All 27,177 Glottolog 5.3 records are retained. WALS and the 30 Phlorest data repositories discovered on 2026-10-12 contribute source-conditioned assertions. The software and .github repositories are not data sources. All 30 summary trees are imported; posterior tree samples are not. The D-PLACE catalog was used for discovery only; phylogeny data came directly from each original Phlorest repository.

Exact Glottocodes share one canonical record. Unmatched study samples and internal clades retain source-specific identities. Repeated samples preserve original labels on their edges. No anonymous study clade is claimed to be an accepted named family. Same-language labels remain as documented in provenance.

The default details/summary outline embeds alternative study branches into Glottolog navigation. Those attachments are display context, not genetic ancestry assertions. Each source branch expands only that source's edges. Source switching is not required. The diagram uses dashed navigation attachments and source-tagged occurrences of shared identities.

Automatic conflicts are crossing, non-nested rooted clades after restricting two summary trees to shared exact, non-repeated, non-ancestor tip IDs. Sampling differences, missing taxa and polytomies alone are not conflicts. These are computational comparisons of imported summary topologies, not a review of statistical uncertainty or scientific validity. The Transeurasian paper-level debate is separately curated with proposal, critique and response.

## Exports

XML schema v3 uses canonical nodes, named sources, source-conditioned placement assertions, conflict witnesses and paper debates. OPML repeats shared references to provide a hierarchical outline; node-id and source preserve their identity. SVG is a view export, not the authoritative graph model.

## Verification and scope

All assertion endpoints, original node IDs, XML node/edge counts and 2,247 conflict witnesses were checked. The interaction harness exercises conditional placements, both paper links, native-name search, inherited debates, branch expansion, horizontal layout and export. Browser visual QA is unavailable in this authoring environment.

This is not every publication worldwide. See Sources & scope and provenance.json for exact coverage, per-source licenses, hashes and remaining gaps. No unreviewed node is labeled consensus solely because no alternative has been imported.

## Hugging Face model discovery

`dist/hf-models.js` queries the public Hub API when a language detail is opened, with no account, token, inference call, or model download. `dist/hf-iso-map.js` contains the existing 184 exact ISO 639-1/639-3 equivalences from `source-data/iso-map.json`. Only the selected record's own language/dialect ISO code is used; a family or dialect does not inherit support from its relatives.

The client fetches up to 20 records per equivalent code and selected task, requires an exact `cardData.language` match, deduplicates model IDs, and displays up to 8 models sorted by downloads. Each entry links to its model card and shows task, matched codes, multilingual metadata, license when present, and download count. Results are publisher metadata, not independent quality evaluations or guarantees of coverage. A 30-minute in-memory cache and in-flight deduplication avoid repeated requests; failed calls are retryable, and Hub search links remain available. A stale response cannot overwrite a newer task or language selection. There is no inferred support for Chinese macrolanguage vs Mandarin, or other macrolanguage/member pairs.

The Sources panel documents this integration. XML and OPML remain classification exports and do not embed the live model results. API reference: https://huggingface.co/docs/hub/api ; model card language reference: https://huggingface.co/docs/huggingface_hub/package_reference/cards .

## Signs and scripts extension (17 October 2026)

`visual-atlas.html?domain=sign` and `visual-atlas.html?domain=scripts` extend the same public atlas. Domain navigation is added to the existing page without replacing its language data or controls.

Rebuild with `python build_visual.py`; validate with `python validate_visual.py` and `node --check dist/visual-atlas.js`.

Coverage: all 344 Glottolog 5.3 Sign Language-category records (including categories, families and dialects), all 76 Power et al. CLDF manual-alphabet samples, three Abner et al. consensus trees spanning 19 distinct language samples, all 226 rows of the downloaded ISO 15924 table, and all 325 SIL Scripts Index rows. Exact script codes are merged; SIL-local IDs remain distinct. There are 334 script/notation records, 63 reviewed historical/influence assertions and 1,001 explicit CLDR language/script usage entries. These counts measure different units. They do not establish exhaustive coverage of world literature or all proposed genealogies.

The Abner European trees are independent replicates, not independent publications. Historical manual-alphabet samples retain separate identities and only link to Glottocodes when explicitly mapped in the dataset. A manual-alphabet grouping is not treated as a whole-language genealogy. Broad script ancestry retains the qualifier “intermediate stages omitted”. Ledyard’s proposed Phags-pa influence is linked to the thesis and explicitly accompanied by Lee’s criticism. Brahmi origin accounts appear together with separate citations.

JSON and XML preserve all fields, assertions, source metadata, notes, usage and input checksums. XML uses typed `field`/`item` elements and is tested by exact JSON round-trip. OPML repeats references under alternate parents and preserves assertion citations, but does not carry the full metadata or usage table. Glottolog alias provider/language tags remain intact. Unicode letter samples are not labeled as native names.

Validation passed for catalog coverage, mappings, acyclic relationships, complete OPML reachability and XML round-trip. A temporary LinkeDOM harness also exercised both domains: rendering, pagination, alias search, mobile-menu state, record details, lazy expansion, horizontal/list switching, collapse and source register. This is DOM logic validation, not real-browser rendering or device testing; the managed environment had no supported browser QA capability.

Source files and their original licenses remain attributed. See `source-data/visual-atlas/input-provenance.json` and `dist/visual-atlas-licenses.txt`. The base language atlas is unchanged apart from domain navigation.

## Variant details and simplified copy (18 October 2026 JST)

Removed decorative hero copy and fixed “Start exploring” suggestions. Persistent dice controls select canonical language/dialect records (not families or study samples); the scripts section samples writing-system records and excludes special/collection codes. The currently selected record is excluded from the next draw.

`variant-detail.html?domain=language&id=<record-id>` provides standalone details for base language records and imported source-specific nodes. `domain=sign` and `domain=scripts` use the signs/scripts graph. Tree-node names and sidebar links open the record page. Pages include aliases, native-label evidence, source-conditioned parents and children, competing research accounts, script usage where applicable, and language-tagged Hugging Face results. Shareable URLs, copy-link control, return-to-tree links and random selection are included. Unknown IDs render a not-found state. No new decorative explanatory copy was added.

Syntax and DOM checks cover both list views, random selection, detail routes for language/dialect/source-node/sign/script records, copying URLs, navigation and unknown-ID handling. Real-browser visual QA remains unverified in this managed environment.
