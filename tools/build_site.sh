#!/usr/bin/env bash
# Build dist/ as it is published, and check it. Run from the repository root.
# Used by .github/workflows/site.yml (pull requests) and pages.yml (the live site).
set -euo pipefail

# Restores dist/data.json and dist/language-families.xml from
# source-data/packed/ and checks their SHA-256.
python3 tools/prepare_static.py
# Writes the top page dist/index.html (the list of top-level families,
# the whole tree, Sources & scope) and dist/random.json, the records its
# Random buttons draw from.
python3 tools/build_home.py
# Writes one page and one record.json per Glottolog record under
# dist/<family>/.../<language>/, and per source-only record under
# dist/<source>/.../ with dist/source-paths.json (not committed; built
# here).
python3 tools/build_paths.py
# Writes the small files the pages load (dist/data/, not committed):
# the atlas tree, the search text and the names split into 64 files.
python3 tools/split_data.py
# The browser rebuilds the same objects as data.json and integrated.json.
node tools/check_atlas_data.js

echo "Check that every page and data file is present"
for f in index.html signs-and-scripts.html record.html 404.html \
         favicon.svg apple-touch-icon.png logo.svg theme.js i18n.js lang.js \
         data.json integrated.json language-families.xml \
         lineage-paths.js stages.json tree.js record-page.js source-paths.json \
         afro-asiatic/berber/index.html wals/index.html gray-et-al-2009/index.html \
         map/land.svg map/land-pacific.svg data/atlas.json \
         data/search.json data/names/0.json atlas-data.js \
         home.js random.json; do
  test -s "dist/$f" || { echo "missing dist/$f"; exit 1; }
done

# The asterisk and "LANG LOG" are always the one SVG, dist/logo.svg
# (.claude/rules/logo.md): every page draws it, and no page writes the
# word mark as text.
echo "Check that every page draws the SVG logo"
missing=$(find dist -name '*.html' -print0 | xargs -0 grep -L 'logo.svg#logo' || true)
[ -z "$missing" ] || { echo "pages without the SVG logo:"; echo "$missing" | head; exit 1; }
text=$(find dist -name '*.html' -print0 | xargs -0 grep -il '>[[:space:]]*\(✱\|\*\|★\)\?[[:space:]]*lang log[[:space:]]*<' || true)
[ -z "$text" ] || { echo "pages with a text logo:"; echo "$text" | head; exit 1; }

# Adds ?v=<content hash> to every local CSS, JS and SVG link in the
# pages, so a browser never pairs new HTML with an old cached file
# (Pages caches files for ten minutes). Runs after every page is written.
python3 tools/version_assets.py
echo "Check that the asset links are versioned"
grep -q 'href="style.css?v=' dist/index.html
