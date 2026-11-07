"""Write the top page of Lang Log, dist/index.html.

The top page shows the logo, a search box and a short introduction. The
language families, sign languages and writing systems are reached from the
search and from the atlas pages' own menu; the top page has no section for
each of them (owner, 2026-11-06).

The page works without JavaScript. The search box is a plain GET form that
opens the language-families atlas with ?q=.

Random lives on this page only (owner, 2026-11-06): a row of three buttons
under the search box, one per atlas. dist/home.js shows the row and, on a
click, opens the record page (record.html?domain=...&id=...) of a record
drawn from dist/random.json, which this script writes (not committed):

- language: Glottolog languages and dialects, without bookkeeping records;
- sign: sign languages and dialects of the signs-and-scripts data;
- scripts: writing systems, without special and collection codes.
"""

from html import escape
from pathlib import Path
import json

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
SOURCE_CODE_URL = "https://github.com/lang-log/lang-log.github.io"


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
        "language": sorted(n["id"] for n in nodes.values()
                           if n.get("level") in ("language", "dialect") and n.get("category") != "Bookkeeping"),
        "sign": sorted(n["id"] for n in visual.values()
                       if n.get("domain") == "sign" and n.get("kind") in ("language", "dialect")),
        "scripts": sorted(n["id"] for n in visual.values()
                          if n.get("domain") == "scripts" and n.get("kind") != "special / collection code"),
    }


def random_row():
    buttons = "".join(
        f'<button type="button" data-domain="{domain}" title="{escape(title)}" '
        f'aria-label="{escape(title)}">{escape(label)}</button>'
        for domain, label, title in RANDOM_BUTTONS)
    return (f'<div class="home-random" role="group" aria-labelledby="home-random-label" hidden>'
            f'<span id="home-random-label">Random</span>{buttons}</div>')


def main():
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
        '<form class="home-search" action="language-families.html" method="get" role="search">'
        '<label class="visually-hidden" for="home-q">Search languages and families</label>'
        '<div class="search-pill">'
        '<input id="home-q" name="q" type="search" placeholder="Name, ISO code, Glottocode…" autocomplete="off">'
        '<button type="submit" aria-label="Search" title="Search">'
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>'
        '</button></div></form>'
        f'{random_row()}'
        '<p class="sub">An atlas of language families, sign languages and writing systems. '
        'Every placement says which source it follows, competing classifications are shown together, '
        'and the data can be downloaded.</p></section>\n'

        '<section class="home-more"><h2>Also</h2><ul>'
        '<li><a href="families/">All families and isolates</a>: one plain page per Glottolog record, '
        'with its classification and a map.</li>'
        '<li><a href="wals-map.html">WALS feature map</a>: pick a feature and see which languages have each value, '
        'coloured on a world map.</li>'
        '<li>Corpora and data for low-resource languages: planned.</li>'
        '</ul></section></main>\n'
        '<footer><span>Sources: Glottolog, WALS, published study trees and script catalogs, each under its own license</span>'
        f'<span><a href="{SOURCE_CODE_URL}">Source code</a> (AGPL-3.0)</span></footer>\n'
        '<script src="home.js"></script>\n'
        '</body></html>\n'
    )
    (DIST / "index.html").write_text(html, encoding="utf-8")
    (DIST / "random.json").write_text(json.dumps(random_pools(), separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
