"""Write the top page of Lang Log, dist/index.html.

The top page introduces the tool and links to its three atlases: language
families (dist/language-families.html), sign languages and writing systems
(dist/visual-atlas.html?domain=...). The record counts are shown here only,
not on the atlas pages themselves. They are read from the committed data
files, so the page stays in step with the data:

- dist/integrated.json `stats`: Glottolog records, study trees, records in
  conflicting clades;
- dist/visual-atlas.json `counts`: sign-language and writing-system records.

The page needs no JavaScript. The search box is a plain GET form that opens
the language-families atlas with ?q=.
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

DIST = Path(__file__).resolve().parent / "dist"
SOURCE_CODE_URL = "https://github.com/lang-log/lang-log.github.io"


def stat(value, label):
    return f'<div><b>{value:,}</b><span>{escape(label)}</span></div>'


def card(href, title, text, stats):
    return (f'<li class="home-card"><h2><a href="{escape(href)}">{escape(title)}</a></h2>'
            f'<p>{escape(text)}</p><div class="stats">{"".join(stats)}</div></li>')


def main():
    lang = json.loads((DIST / "integrated.json").read_text(encoding="utf-8"))["stats"]
    visual = json.loads((DIST / "visual-atlas.json").read_text(encoding="utf-8"))["counts"]
    cards = "".join([
        card("language-families.html", "Language families",
             "Glottolog's classification of every language family, language and dialect, "
             "with WALS and published study trees side by side and the clades they disagree on.",
             [stat(lang["glottologRecords"], "Glottolog records"),
              stat(lang["summaryTrees"], "Imported study trees"),
              stat(lang["recordsWithConflicts"], "Records in conflicting clades")]),
        card("visual-atlas.html?domain=sign", "Sign languages",
             "Sign languages and their proposed relationships, from catalogs, "
             "manual alphabets and lexical studies.",
             [stat(visual["glottologSignRecords"], "Glottolog sign records"),
              stat(visual["manualAlphabetSamples"], "Manual-alphabet samples"),
              stat(visual["distinctLexicalSamples"], "Languages in lexical study")]),
        card("visual-atlas.html?domain=scripts", "Writing systems",
             "Scripts and notations, how they descend from and influence each other, "
             "and which languages use them.",
             [stat(visual["scriptRecords"], "Script / notation records"),
              stat(visual["scriptRelationships"], "Reviewed relationships"),
              stat(visual["usageAssertions"], "CLDR usage assertions")]),
    ])
    description = ("Lang Log: an atlas of language families, sign languages and writing systems, "
                   "with source-linked classifications, alternative hypotheses and exportable data.")
    html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{escape(description)}">'
        '<title>Lang Log by yoshi</title>'
        '<link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="apple-touch-icon.png">'
        '<link rel="stylesheet" href="style.css">'
        '<link rel="search" type="application/opensearchdescription+xml" title="Lang Log" href="opensearch.xml">'
        '</head><body class="home-page">\n'
        '<header><div class="brand"><a class="home" href="./" aria-current="page"><span class="mark">✳</span> LANG LOG</a> '
        f'<span class="by">by <a href="{escape(PROFILE_URL)}" title="MATSUURA Yoshihiro">yoshi</a></span></div>'
        '<a href="families/">All families</a></header>\n'
        '<main class="home-main">'
        '<section class="home-intro"><h1>Lang Log</h1>'
        '<p class="sub">An atlas of language families, sign languages and writing systems. '
        'Every placement says which source it follows, competing classifications are shown together, '
        'and the data can be downloaded.</p>'
        '<form class="home-search" action="language-families.html" method="get" role="search">'
        '<label for="home-q">Search languages and families</label>'
        '<div class="search"><span aria-hidden="true">⌕</span>'
        '<input id="home-q" name="q" placeholder="Name, ISO code, Glottocode…" autocomplete="off"></div>'
        '<button type="submit">Search</button></form></section>\n'
        f'<ul class="home-cards">{cards}</ul>\n'
        '<section class="home-more"><h2>Also</h2><ul>'
        '<li><a href="families/">All families and isolates</a>: one plain page per Glottolog record, '
        'with its classification and a map.</li>'
        '<li>Corpora and data for low-resource languages: planned.</li>'
        '</ul></section></main>\n'
        '<footer><span>Sources: Glottolog, WALS, published study trees and script catalogs, each under its own license</span>'
        f'<span><a href="{SOURCE_CODE_URL}">Source code</a> (AGPL-3.0)</span></footer>\n'
        '</body></html>\n'
    )
    (DIST / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
