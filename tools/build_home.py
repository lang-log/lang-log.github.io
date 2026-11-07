"""Write the top page of Lang Log, dist/index.html.

The top page shows the logo, a search box and a short introduction. The
language families, sign languages and writing systems are reached from the
search and from the menu of the three atlases; the top page has no card for
each of them (owner, 2026-11-06).

The top page is also the top of the language-families tree (owner,
2026-11-06): every Glottolog record and every source-only record has its own
page below it (tools/build_paths.py), and this page lists the top-level
families and isolates, draws the whole tree (dist/tree.js), and holds the
"Sources & scope" text (source-data/sources-and-scope.html) and the
downloads. There is no separate atlas page.

The list and the texts work without JavaScript. The search box is a GET form
to this page (?q=); dist/tree.js lists the matches under it.

Random lives on this page only (owner, 2026-11-06): a row of buttons under
the search box. "Random" itself is a button that picks any record (one of
the three atlases at random, then a record in it), so tapping the word does
something instead of selecting it as text; the three buttons after it pick
from one atlas each. dist/home.js shows the row and, on a click, opens the page of a record
drawn from dist/random.json, which this script writes (not committed):

- language: page paths of Glottolog languages and dialects, without
  bookkeeping records;
- sign: sign languages and dialects of the signs-and-scripts data;
- scripts: writing systems, without special and collection codes.
"""

from html import escape
from pathlib import Path
import datetime
import json

import build_paths as bp
from build_paths import PROFILE_URL

# TODO: sections planned for the top page, not built yet (owner, 2026-11-06):
# - Data sources band: names (and logos only where each source's brand terms
#   allow) of Glottolog, Hugging Face and the other inputs, headed "Data
#   sources" so it does not read as a list of partners.
# - Updates: a news list (date, one line, link), newest first, 3 to 5 items,
#   kept in a data file in this repository and added in the same pull request
#   as the change it announces.
# - Sponsors: a section for sponsors of Lang Log.

DIST = Path(__file__).resolve().parent.parent / "dist"


# Buttons of the Random row: (pool in random.json, label, title).
RANDOM_BUTTONS = [
    ("language", "Language", "Choose a random language or dialect"),
    ("sign", "Sign language", "Choose a random sign language or dialect"),
    ("scripts", "Writing system", "Choose a random writing system"),
]


def random_pools():
    nodes = json.loads((DIST / "data.json").read_text(encoding="utf-8"))["nodes"]
    visual = json.loads((DIST / "signs-and-scripts.json").read_text(encoding="utf-8"))["nodes"]
    return {
        "language": sorted(bp.path_of(n["id"]) + ("" if "/#" in bp.path_of(n["id"]) else "/") for n in nodes.values()
                           if n.get("level") in ("language", "dialect") and n.get("category") != "Bookkeeping"),
        "sign": sorted(n["id"] for n in visual.values()
                       if n.get("domain") == "sign" and n.get("kind") in ("language", "dialect")),
        "scripts": sorted(n["id"] for n in visual.values()
                          if n.get("domain") == "scripts" and n.get("kind") != "special / collection code"),
    }


def random_row():
    any_button = ('<button type="button" class="random-any" data-domain="any" '
                  'title="Choose a random language, sign language or writing system" '
                  'aria-label="Choose a random language, sign language or writing system">Random</button>')
    buttons = any_button + "".join(
        f'<button type="button" data-domain="{domain}" title="{escape(title)}" '
        f'aria-label="{escape(title)}">{escape(label)}</button>'
        for domain, label, title in RANDOM_BUTTONS)
    return f'<div class="home-random" role="group" aria-label="Random" hidden>{buttons}</div>'


def families_html():
    """The top-level families and isolates of Glottolog, each linked to its page."""
    roots = sorted(bp.data["roots"], key=lambda r: bp.nodes[r]["name"].lower())
    rows = "".join(f'<li><a href="{escape(bp.path_of(r))}/">{escape(bp.nodes[r]["name"])}</a> '
                   f'<span class="muted">{escape("isolate" if bp.nodes[r].get("isolate") else bp.nodes[r]["level"])}</span></li>'
                   for r in roots)
    unplaced = bp.unified["anchors"].get("__unplaced__", [])
    rows_unplaced = "".join(f'<li><a href="{escape(bp.path_of(a["root"]))}/">{escape(bp.sources[a["source"]]["title"])}</a> '
                            f'<span class="muted">{"catalog grouping" if a["type"] == "catalog" else "sampled study tree"}</span></li>'
                            for a in unplaced)
    return (f'<section class="home-section" id="families"><h2>All families and isolates · {len(roots)}</h2>'
            '<p class="muted">Top-level entries of Glottolog 5.3. Each record has its own page at a URL that follows its classification.</p>'
            f'<ul class="record-links">{rows}</ul>'
            '<h3>Cross-family / outgroup source trees</h3><p class="muted">Study trees and WALS families that span more than one '
            'Glottolog family. They are listed here for navigation only.</p>'
            f'<ul class="record-links">{rows_unplaced}</ul></section>')


def tree_section():
    downloads = ('<a class="exportlink" href="language-families.xml" download title="Complete Glottolog and WALS trees, all imported names and source tags">XML</a>'
                 '<a class="exportlink" href="language-families.opml" download title="Complete outline for compatible outliner tools">OPML</a>')
    return ('<section class="home-section tree-section" id="tree-section"><h2>Whole tree</h2>'
            + bp.atlas_html("", downloads=downloads) + "</section>")


def sources_section():
    """The "Sources & scope" text with the coverage figures and the study trees, each linked to its tree."""
    u = bp.unified
    st = u["stats"]
    text = (bp.ROOT / "source-data" / "sources-and-scope.html").read_text(encoding="utf-8")
    text = text.split("-->", 1)[1].strip()
    coverage = (f'<p>{st["glottologRecords"]:,} Glottolog records retained; {st["canonicalRecords"]:,} canonical records including '
                f'source-specific clades/samples. All {st["summaryTrees"]} discovered Phlorest dataset summary trees imported, plus WALS.</p>'
                f'<p>{st["assertions"]:,} source-tagged root/parent assertions. {st["topologicalConflicts"]:,} incompatible clade pairs '
                f'across study trees involve {st["recordsWithConflicts"]:,} canonical records.</p>'
                '<p>This is coverage of the imported corpus, not every publication worldwide.</p>')
    register = "".join(
        f'<div class="registry-source"><strong><a href="{escape(bp.SOURCE_SLUG[s["id"]])}/">{escape(s["title"])}</a></strong><br>{escape(s["citation"])}<br>'
        f'<a href="{escape(s["url"])}" target="_blank" rel="noopener">Paper ↗</a> · '
        f'<a href="{escape(s["dataset"])}" target="_blank" rel="noopener">Source tree &amp; data ↗</a>'
        f'<small>{escape(s["family"])} · {escape(s["license"])} · summary tree imported</small>'
        + (f'<p>{escape(s["interpretationNote"])}</p>' if s.get("interpretationNote") else "") + "</div>"
        for s in u["sources"].values() if s.get("kind") == "study")
    register = (f'<p><a href="{bp.SOURCE_SLUG["wals"]}/">WALS families in Lang Log</a></p>' + register)
    text = text.replace("<!-- coverage -->", coverage).replace("<!-- source-register -->", register)
    return f'<section class="home-section sources-scope" id="sources"><h2>Sources &amp; scope</h2>{text}</section>'


def main():
    st = bp.unified["stats"]
    roots = [bp.nodes[r] for r in bp.data["roots"]]
    isolates = sum(1 for n in roots if n.get("isolate"))
    categories = sum(1 for n in roots if n.get("category") not in ("Spoken genealogy", None) and not n.get("isolate"))
    genealogical = len(roots) - isolates - categories
    retrieved = datetime.date.fromisoformat(bp.data["retrieved"]).strftime("%-d %b %Y")
    description = ("Lang Log: an atlas of language families, sign languages and writing systems, "
                   "with source-linked classifications, alternative hypotheses and exportable data.")
    html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{escape(description)}">'
        '<title>Lang Log by yoshi</title>'
        '<link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="apple-touch-icon.png">'
        '<link rel="stylesheet" href="style.css">'
        '<script src="theme.js"></script><script src="i18n.js"></script><script src="lang.js"></script>'
        '<link rel="search" type="application/opensearchdescription+xml" title="Lang Log" href="opensearch.xml">'
        '</head><body class="home-page">\n'
        '<header><div class="brand"><a class="home" href="./" aria-current="page"><svg class="logo" role="img" aria-label="LANG LOG"><use href="logo.svg#logo"/></svg></a> '
        f'<span class="by">by <a href="{escape(PROFILE_URL)}" title="MATSUURA Yoshihiro">yoshi</a></span></div>'
        '</header>\n'
        '<main class="home-main">'
        '<section class="home-intro">'
        '<h1 class="home-logo"><svg class="logo" role="img" aria-label="LANG LOG"><use href="logo.svg#logo"/></svg></h1>'
        f'<p class="home-by">by <a href="{escape(PROFILE_URL)}" title="MATSUURA Yoshihiro">yoshi</a></p>'
        '<form class="home-search" action="./" method="get" role="search">'
        '<label class="visually-hidden" for="home-q">Search languages and families</label>'
        '<div class="search-pill">'
        '<input id="home-q" name="q" type="search" placeholder="Name, ISO code, Glottocode…" autocomplete="off">'
        '<button type="submit" aria-label="Search" title="Search">'
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>'
        '</button></div></form>'
        '<div id="results" class="home-results" aria-live="polite" hidden></div>'
        f'{random_row()}'
        '<p class="sub">An atlas of language families, sign languages and writing systems. '
        'Every placement says which source it follows, competing classifications are shown together, '
        'and the data can be downloaded.</p></section>\n'

        f'{bp.domain_nav("./")}'
        f'{families_html()}{tree_section()}{sources_section()}'
        '<section class="home-more"><h2>Also</h2><ul>'
        '<li><a href="feature-map.html">Language feature map</a>: every language on a world map, '
        'narrowed by conditions on WALS features and coloured by one of them.</li>'
        '<li>Corpora and data for low-resource languages: planned.</li>'
        '</ul></section></main>\n'
        f'<footer><span>Glottolog 5.3 + WALS + {st["summaryTrees"]} Phlorest summary trees · Retrieved {retrieved}</span>'
        f'<span>{genealogical} genealogical family roots · {isolates} isolates · {categories} non-genealogical categories</span>'
        '<span>Sources: Glottolog, WALS, published study trees and script catalogs, each under its own license</span>'
        '<span>© 2026 MATSUURA Yoshihiro. All rights reserved.</span></footer>\n'
        '<script src="home.js"></script><script src="atlas-data.js"></script><script src="lineage-paths.js"></script><script src="tree.js"></script>\n'
        '</body></html>\n'
    )
    (DIST / "index.html").write_text(html, encoding="utf-8")
    (DIST / "random.json").write_text(json.dumps(random_pools(), separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
