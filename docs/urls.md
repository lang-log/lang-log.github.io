# URLs

Every address of Lang Log, and every query parameter a page reads (issue #92). The site is static files on GitHub Pages, so a path is a file or a folder with an `index.html`. A new kind of page or a new parameter is added here in the same pull request (`.claude/rules/ui-design.md`).

## Pages

| Path                                 | Page                                                                                             | Built by                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------------------ | ----------------------------------------- |
| `/`                                  | Top page: logo, search box, Random row, the list and map of every top-level record               | `tools/build_home.py`                     |
| `/q?q=<terms>`                       | Search results (`dist/q.html`; GitHub Pages serves `q.html` at `/q`)                             | hand-written, `dist/search.js`            |
| `/<family>/<subgroup>/.../<record>/` | Record page of a Glottolog record, at its place in the Glottolog tree (see "Record paths" below) | `tools/build_paths.py`                    |
| `/<source>/.../<record>/`            | Record page of a record that exists only in another source (`wals/`, `gray-et-al-2009/`, ...)    | `tools/build_paths.py`                    |
| `/stats/`, `/sources/`, `/updates/`  | Stats, Sources & scope, Updates                                                                  | `tools/build_home.py`                     |
| `/releases.html`                     | Releases (from the GitHub Releases of this repository)                                           | `tools/build_releases.py`                 |
| `/signs-and-scripts.html`            | Sign languages and writing systems                                                               | hand-written, `dist/signs-and-scripts.js` |
| `/record.html?domain=<d>&id=<id>`    | Record of a sign language or writing system                                                      | hand-written, `dist/record.js`            |
| `/404.html`                          | Not found (served by GitHub Pages at any missing path)                                           | hand-written                              |

## Record paths

- Each segment is an ASCII slug of the record's name. Siblings with the same slug both get `-<glottocode>`.
- Family and source slugs share the top level; the build stops if two are equal.
- A study tree's root is the source's own page (`/gray-et-al-2009/`); `/wals/` lists the WALS families.
- Lang Log's own classification (historical stages) does not change a path: a record stays at its Glottolog place.
- `dist/lineage-paths.js` (Glottolog records) and `dist/source-paths.json` (source-only records) give the scripts the same paths.

## Data files

| Path                                                  | Contents                                                                                       |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `/<record path>/record.json`                          | The record as its page shows it                                                                |
| `/<record path>/languoid.json`                        | Lang Log's own data for the record (shape `schema/languoid.schema.json`, served at `/schema/`) |
| `/features/index.json`, `/features/<feature id>.json` | Lang Log features and the value of every record that has one                                   |
| `/data/`                                              | The data the page scripts load (`dist/atlas-data.js`, `tools/split_data.py`)                   |
| `/data/features/`                                     | Languages, features and values for the top page's conditions (`tools/build_wals_map.py`)       |
| `/language-families.xml`, `/language-families.opml`   | The whole tree, for download                                                                   |
| `/signs-and-scripts.json`, `.xml`, `.opml`            | The sign-language and writing-system data, for download                                        |
| `/releases.json`                                      | The releases shown on `/releases.html`                                                         |
| `/source-paths.json`, `/random.json`                  | Paths of source-only records; the pools of the Random row                                      |
| `/map/land.svg`, `/map/tiles/`, `/map/tiles.json`     | The land and borders behind every map (`tools/build_land.py`)                                  |
| `/sitemap*.xml`, `/robots.txt`, `/opensearch.xml`     | For search engines and browsers                                                                |

## Query parameters and fragments

Every screen state that can be shared is kept in the address, so a copied URL reopens the same view. Back and Forward step through selections, branches, filters and view changes; typing, panning and zooming update the current entry instead of adding new ones.

| Parameter     | Page                              | Meaning                                                                                                                               |
| ------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `q`           | `/q`                              | Search text. An old top-page link with `?q=` is sent to `/q?q=` (`dist/home.js`)                                                      |
| `view`        | Top page                          | `map` for the map; the list when left out. The former `tree` opens the list (issue #93)                                               |
| `c`           | Top page                          | One condition, `<feature>` or `<feature>:<values>`, one `c` per condition in order; a leading `\|` joins it to the previous one by OR |
| `k`           | Top page                          | The feature the map is coloured by                                                                                                    |
| `view`        | Record pages                      | `tree` to draw the tree of the branch instead of the outline                                                                          |
| `x`, `y`, `z` | Record pages                      | Tree position (centre in tree coordinates) and zoom; present only after panning or zooming                                            |
| `task`        | Record pages                      | Hugging Face model task (for example `translation`)                                                                                   |
| `#map-view`   | Top page, record pages            | Opens the first map in the full-window map view (`dist/map-zoom.js`)                                                                  |
| `domain`      | Signs and scripts, record.html    | `sign` or `scripts` (`record.html` also takes `language`)                                                                             |
| `id`          | Signs and scripts, record.html    | The selected record                                                                                                                   |
| `branch`      | Signs and scripts                 | The expanded branch                                                                                                                   |
| `q`           | Signs and scripts                 | Search text                                                                                                                           |
| `view`        | Signs and scripts                 | `tree` for the tree                                                                                                                   |
| `task`        | Signs and scripts, record.html    | Hugging Face model task                                                                                                               |
| `about`       | Signs and scripts                 | `1` opens the Sources & scope dialog                                                                                                  |
| `ref`         | Links to the owner's profile site | Where the visit came from (`langlog`; `profile-links.md` in `research-aide`), read by that site                                       |

On a record page the tree is drawn when the visitor presses "Show the tree of this branch", or at once when the URL has `view` or `x`. The top page's conditions keep the other parameters as they are.

Not kept in the address: rows opened by hand in a list or outline, the mobile search menu, scroll position and random draws (the drawn record is kept as `id`).
