# The site

How the pages of Lang Log work. Addresses and query parameters are in [`urls.md`](urls.md), UI components in [`components.md`](components.md), and the data behind the pages in [`data.md`](data.md).

## Top page

The top page (`./`, `dist/index.html`) shows the logo, the `by yoshi` line and a search box. It is written by `tools/build_home.py`. Under the search box, a Random button opens the page of a random record of any kind; the top page is the only page with Random. `dist/home.js` draws from `dist/random.json`, which `tools/build_home.py` writes (not committed). Without JavaScript the button stays hidden. Next to it, a row of links leads to the Stats, Sources and Releases pages.

The top page is also the top of the language-families tree. Below the search box it shows all top-level families and isolates in two views, with one switch between them and one set of conditions they share (`dist/explore.js`, markup from `tools/build_home.py`):

- List: the top-level records under their continents, each with up to two native names, the number of sources that place it and a flag for conflicting study trees. It works without JavaScript. With JavaScript each row opens into its members, as the outline on a record page does (`dist/tree.js`), and the Download menu above the list gives the whole tree as SVG, XML and OPML. The list and the former Tree view are one (issue #93).
- Map: every Glottolog language with a point, coloured by one feature if chosen.

Conditions are on WALS features and on two Lang Log features, conflicting study clades and research trees (`tools/build_wals_map.py`); the values ticked in one condition are joined by OR, conditions by AND unless switched to OR. The Sources & scope text is on its own page (`source-data/sources-and-scope.html`). There is no separate atlas page; every record has its own page.

## Record pages

`tools/build_paths.py` writes one page and one `record.json` for each Glottolog record, at a URL that follows its classification, for example `indo-european/.../castilic/spanish/`. The breadcrumb starts at the top page, which lists all families and isolates. The pages need no JavaScript; `dist/lineage-paths.js` follows the same rules to link to them.

Each page shows its facts in tables (`facts_table()` and `data_table()` in `tools/build_paths.py`; the owner's request, 2026-11-23), in groups with a heading each (`group()`), in the owner's order: Names, Codes (ID, ISO 639-3, 639-1 and 639-2/B, language tag and what the registry says of it, WALS code), Medium and writing (Medium, scripts), Classification (its placement in every source, with paper links and the other direct members, the other sources' trees attached below it, incompatible study branches, curated debates, its members and the tree of its branch, `dist/tree.js`, on request), Place (area, countries, coordinates, map), Speakers (estimated speakers, societies, share of each country's population), Vitality (each source's endangerment status), Status in society (official status by country), Features (plural categories, phoneme inventories and feature values), Records and resources (years of documentation, the most extensive description, Hugging Face models: `dist/hf-models.js`, loaded when the section scrolls into view) and Links (with the Wikidata item). A group with nothing in it is left out. Country and script names, percentages and counts are written in the page's language by `dist/record-page.js` (`Intl`).

Records that exist only in another source's tree (WALS genera and families, study clades and unmatched samples) get the same kind of page under that source, for example `wals/altaic/turkic/azerbaijani/`. A study tree's root is the source's page (`gray-et-al-2009/`); `wals/` lists the WALS families. `dist/source-paths.json` maps these records to their paths for the scripts. The rules for the paths are in [`urls.md`](urls.md).

- Historical stages, such as Old English, have their own page at their place in Glottolog like every other record. Lang Log's own classification (`source-data/lang-log/classification.json`, see [`data.md`](data.md)) places a stage as the parent of the later language; the page shows it under the Glottolog path ("Lang Log’s own: Old English › Middle English" on the English page) and lists the record's children there ("Members according to Lang Log"). It does not change the URL.
- The record pages (one directory per top-level family or source under `dist/`) and `dist/source-paths.json` are built by the Pages workflow and are not committed.

## Maps

- Each record page has a static map (inline SVG, no JavaScript; `tools/languoid_map.py`, `map_html()` in `tools/build_paths.py`). Every record's map is built the same way: the deepest points on each of its branches, or its own point when it has none below, all in one colour and size; grey squares, as large as those points, are the sister languoids (the rest of its parent's points). A key under the map (also shown in the map view) names each kind of point. Points are Glottolog's representative coordinates (`source-data/languages.csv`), one per record, not the area where a language is spoken. `record.json` carries the same `coordinates`.
- The land and country borders behind the points are `dist/map/land.svg`, drawn by `tools/build_land.py` from Natural Earth 1:50m land and boundary lines v5.1.2 (public domain) in the Web Mercator projection (cut at 85 degrees north and south, as on other web maps) and committed. The map goes round the world: each page draws it once more on each side, and a group of points around the 180th meridian (for example Oceanic) stays together; each page refers to them with `<use>`, so browsers download them once. Borders are thin solid lines; disputed, indefinite and unrecognised boundaries are dashed.
- `dist/map-zoom.js` adds zoom and pan: drag (one finger is enough on a phone; the page scrolls from outside the map), east and west without end, pinch, Ctrl/Cmd + wheel, double click, the + / − buttons (shown only when the device has a mouse or trackpad), Reset (which glides back to the starting view) and the keyboard. Points and border lines keep their size on screen at every zoom. Once the view is narrow enough, it draws the 1:10m tiles in `dist/map/tiles/land/` (listed in `dist/map/tiles.json`, also written by `tools/build_land.py`) for the part in view. Other pages can reuse it with `window.LangLogMap.mount(svg)`; see the comment at the top of the file.
- The top page's map behaves the same; only its points are written by `dist/explore.js` instead of `tools/build_paths.py`.

## Logo

The header logo (asterisk and "LANG LOG") is one SVG symbol, `dist/logo.svg`, drawn on every page with `<use href="logo.svg#logo">`, so the logo link is one rectangle. `tools/build_logo.py` writes it from Montserrat Bold outlines and updates the `.logo` aspect ratio in `dist/style.css`; it needs `fontTools` and the Montserrat variable font file (not in the repository; the script says where to get it) and is run only when the logo changes. Every place that shows the logo uses this SVG, including the not-found page `dist/404.html`; the logo is never written as text (`.claude/rules/logo.md`; `tools/build_site.sh` checks it).

## Interface language and theme

The right end of the header on every page has a light/dark theme toggle and a language menu with the same languages as the owner's profile site, in the same order (`LANGS` in `dist/lang.js`).

- `dist/theme.js` adds the toggle and applies a saved theme before the page is drawn. Without a saved choice the page follows the system setting. Every colour is a variable at the top of `dist/style.css`, with one light and one dark value; the canvas tree in `dist/tree.js` reads the same variables.
- `dist/lang.js` adds the language menu. The pages are written in English; in another language the script translates the interface text with that language's dictionary (`dist/i18n.js` for Japanese, `dist/i18n/<code>.js` for the others, loaded only when chosen; both written by `tools/build_i18n.py` from `i18n/<code>.yaml`) and keeps translating what the atlas scripts add later. Record names, source titles, citations and codes are data and stay as the sources give them. Without a saved choice the language follows the browser. Arabic and Persian are right-to-left; numbers and dates follow each language's conventions (0-9 except Persian ۰-۹).
- Both choices are kept in `localStorage` (`theme`, `lang`) for every page. Switching keeps the URL and adds no history entry. Without JavaScript the pages are English, follow the system theme, and show neither control.
- The interface text is in `i18n/`: `en.yaml` holds the English text under a key, and each other language has `<code>.yaml` with the same keys. `python3 tools/build_i18n.py` lists what is missing.

## Search from the address bar

`https://lang-log.github.io/q?q=<text>` opens the search results page (`dist/q.html`) with `<text>` in the search box and its matches listed under it. To add the site as a browser search engine by hand, use that address with `%s` in place of `<text>`. Old links to the top page with `?q=<text>` are sent there.

`dist/opensearch.xml` describes the same search for browsers, and every page links to it with `<link rel="search">`. Firefox then offers "Add Lang Log" in the search menu; Chrome lists it under Settings > Search engine > Manage search engines and site search > Inactive shortcuts after the site has been visited.

## Hugging Face models

`dist/hf-models.js` queries the public Hub API when the models section of a record page scrolls into view, with no account, token, inference call, or model download. `dist/hf-iso-map.js` contains the exact ISO 639-1/639-3 equivalences from `source-data/iso-map.json`. Only the selected record's own language or dialect ISO code is used; a family or dialect does not inherit support from its relatives.

The client fetches a page of records per equivalent code and selected task, requires an exact `cardData.language` match, deduplicates model IDs, and shows the most downloaded models. Each entry links to its model card and shows task, matched codes, multilingual metadata, license when present, and download count. Results are publisher metadata, not independent quality evaluations or guarantees of coverage. An in-memory cache and in-flight deduplication avoid repeated requests; failed calls are retryable, and Hub search links remain available. A stale response cannot overwrite a newer task or language selection. There is no inferred support for Chinese macrolanguage vs Mandarin, or other macrolanguage/member pairs.

XML and OPML remain classification exports and do not embed the live model results. API reference: <https://huggingface.co/docs/hub/api>; model card language reference: <https://huggingface.co/docs/huggingface_hub/package_reference/cards>.

## Sign languages and writing systems

`signs-and-scripts.html?domain=sign` and `signs-and-scripts.html?domain=scripts` show the sign-language and writing-system data (`dist/signs-and-scripts.js`); they show no domain navigation, because Lang Log is one tree, not three domains. `record.html?domain=<sign|scripts|language>&id=<record-id>` (`dist/record.js`) shows one record of that data: aliases, native-label evidence, source-conditioned parents and children, competing research accounts, script usage where applicable, and language-tagged Hugging Face results, with a copy-link button and a link back to the tree or to the record's page. Unknown IDs show a not-found state.
