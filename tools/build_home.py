"""Write the top page of Lang Log, dist/index.html.

The top page shows the logo, a search box and a short introduction. The
language families, sign languages and writing systems are reached from the
search and from Random; the top page has no card for
each of them (owner, 2026-11-06).

The top page is also the top of the language-families tree (owner,
2026-11-06): every Glottolog record and every source-only record has its own
page below it (tools/build_paths.py), and this page lists the top-level
families and isolates, draws the whole tree (dist/tree.js) and holds the
downloads. There is no separate atlas page.

Stats, sources and updates are pages of their own, not sections of the top
page (owner, 2026-11-07): dist/stats/, dist/sources/ (the "Sources & scope"
text, source-data/sources-and-scope.html) and dist/updates/ (the entries of
source-data/lang-log/updates.json). The top page links to them in a row of
links next to the Random button. Every count on the Stats page is counted from the
data here, at build time; no number is typed by hand.

The list and the texts work without JavaScript. The search box is a GET form to
the search results page, dist/q.html at <site>/q?q=<terms> (dist/search.js,
owner 2026-11-08); dist/home.js sends old ?q= links to the top page there.

Random lives on this page only (owner, 2026-11-06): a row of buttons under
the search box. "Random" itself is a button that picks any record (one of
the three pools at random, then a record in it), so tapping the word does
something instead of selecting it as text. The buttons per domain and the
row of links to the three atlases are gone (owner, 2026-11-07: Lang Log is
one tree, not three domains). dist/home.js shows the row and, on a click, opens the page of a record
drawn from dist/random.json, which this script writes (not committed):

- language: page paths of Glottolog languages and dialects, without
  bookkeeping records;
- sign: sign languages and dialects of the signs-and-scripts data;
- scripts: writing systems, without special and collection codes.
"""

from html import escape
import csv
import re
import datetime
import json

from locations import DIST
import build_paths as bp
import info_page
from security_policy import HEAD as SECURITY_HEAD
from site_brand import COPYRIGHT, HOME_TITLE, by_yoshi

# TODO: sections planned for the top page, not built yet (owner, 2026-11-06):
# - Data sources band: names (and logos only where each source's brand terms
#   allow) of Glottolog, Hugging Face and the other inputs, headed "Data
#   sources" so it does not read as a list of partners.
# - Sponsors: a section for sponsors of Lang Log.


def random_pools():
    nodes = json.loads((DIST / "data.json").read_text(encoding="utf-8"))["nodes"]
    visual = json.loads((DIST / "signs-and-scripts.json").read_text(encoding="utf-8"))["nodes"]
    return {
        "language": sorted(
            bp.path_of(n["id"]) + ("" if "/#" in bp.path_of(n["id"]) else "/")
            for n in nodes.values()
            if n.get("level") in ("language", "dialect") and n.get("category") != "Bookkeeping"
        ),
        "sign": sorted(
            n["id"]
            for n in visual.values()
            if n.get("domain") == "sign" and n.get("kind") in ("language", "dialect")
        ),
        "scripts": sorted(
            n["id"]
            for n in visual.values()
            if n.get("domain") == "scripts" and n.get("kind") != "special / collection code"
        ),
    }


def random_row():
    """One Random button. The three buttons per domain (language, sign
    language, writing system) were removed with the three-way split (owner,
    2026-11-07); see the git history to reuse them."""
    button = (
        '<button type="button" class="random-any" data-domain="any" '
        'title="Choose a random language, sign language or writing system" '
        'aria-label="Choose a random language, sign language or writing system">Random</button>'
    )
    return f'<div class="home-random" role="group" aria-label="Random" hidden>{button}</div>'


# Links next to the Random button on the top page: (page, label).
GUIDE_LINKS = [
    ("stats/", "Stats"),
    ("sources/", "Sources"),
    ("updates/", "Updates"),
    ("releases.html", "Releases"),
]


def guide_row():
    links = "".join(f'<a href="{escape(h)}">{escape(t)}</a>' for h, t in GUIDE_LINKS)
    return f'<nav class="home-guide" aria-label="About Lang Log">{links}</nav>'


# The continents of the top-page list, in the owner's order (2026-11-08), and
# the Glottolog macroareas each one takes. The grouping is for display only:
# a continent is a heading on the top page, never a node of the tree.
CONTINENTS = {
    "Africa": ("Africa",),
    "Eurasia": ("Eurasia",),
    "Oceania": ("Papunesia", "Australia"),
    "North America": ("North America",),
    "South America": ("South America",),
}
CONTINENT_OF_MACROAREA = {a: c for c, areas in CONTINENTS.items() for a in areas}


def first_macroarea(node):
    """A record's first Glottolog macroarea ("" if it has none); records in
    several macroareas list them separated by ";"."""
    return (node.get("area") or "").split(";")[0]


# The heading for top-level records with no macroarea, neither their own nor
# any of their languages' (for example a root whose records have no location).
NO_CONTINENT = "No location in the data"


def continent_of_roots():
    """Each top-level record's continent: the one where most of its languages
    (level "language", by their first macroarea) are; a tie goes to the
    continent that comes first in CONTINENTS. A root with no such language
    takes the continent of its own first macroarea, and one without that
    either goes under NO_CONTINENT."""
    tally = {r: dict.fromkeys(CONTINENTS, 0) for r in bp.data["roots"]}
    for n in bp.nodes.values():
        continent = CONTINENT_OF_MACROAREA.get(first_macroarea(n))
        if n.get("level") == "language" and continent and n.get("root") in tally:
            tally[n["root"]][continent] += 1
    return {
        r: max(t, key=t.get)
        if any(t.values())
        else CONTINENT_OF_MACROAREA.get(first_macroarea(bp.nodes[r]), NO_CONTINENT)
        for r, t in tally.items()
    }


def families_html():
    """The top-level records of Glottolog, each linked to its page, under the
    continent where most of their languages are (continent_of_roots())."""
    roots = sorted(bp.data["roots"], key=lambda r: bp.nodes[r]["name"].lower())
    continent_of = continent_of_roots()
    # No kind label (family, isolate) after the name: every record is a languoid.
    groups = "".join(
        f"<h3>{escape(continent)}</h3>"
        '<ul class="record-links">'
        + "".join(
            f'<li><a href="{escape(bp.path_of(r))}/">{escape(bp.nodes[r]["name"])}</a></li>'
            for r in roots
            if continent_of[r] == continent
        )
        + "</ul>"
        for continent in (*CONTINENTS, NO_CONTINENT)
        if continent in continent_of.values()
    )
    unplaced = bp.unified["anchors"].get("__unplaced__", [])
    rows_unplaced = "".join(
        f'<li><a href="{escape(bp.path_of(a["root"]))}/">{escape(bp.sources[a["source"]]["title"])}</a> '
        f'<span class="muted">{"catalog grouping" if a["type"] == "catalog" else "sampled study tree"}</span></li>'
        for a in unplaced
    )
    return (
        f'<section class="home-section" id="families"><h2>All families and isolates · {len(roots)}</h2>'
        '<p class="muted">Top-level entries of Glottolog 5.3. Each record has its own page at a URL that follows its classification.</p>'
        '<p class="muted">Each is listed under the continent where most of its languages are spoken.</p>'
        f"{groups}"
        '<h3>Cross-family / outgroup source trees</h3><p class="muted">Study trees and WALS families that span more than one '
        "Glottolog family. They are listed here for navigation only.</p>"
        f'<ul class="record-links">{rows_unplaced}</ul></section>'
    )


def tree_section():
    downloads = (
        '<a class="exportlink" href="language-families.xml" download title="Complete Glottolog and WALS trees, all imported names and source tags">XML</a>'
        '<a class="exportlink" href="language-families.opml" download title="Complete outline for compatible outliner tools">OPML</a>'
    )
    return (
        '<section class="home-section tree-section" id="tree-section"><h2>Whole tree</h2>'
        + bp.atlas_html("", downloads=downloads)
        + "</section>"
    )


def sources_section():
    """The "Sources & scope" text with the coverage figures and the study trees, each linked to its tree."""
    u = bp.unified
    st = u["stats"]
    text = (bp.ROOT / "source-data" / "sources-and-scope.html").read_text(encoding="utf-8")
    text = text.split("-->", 1)[1].strip()
    # The page is one level below the root.
    text = re.sub(r'href="(?!https?:|#|\.\./)', 'href="../', text)
    coverage = (
        f"<p>{st['glottologRecords']:,} Glottolog records retained; {st['canonicalRecords']:,} canonical records including "
        f"source-specific clades/samples. All {st['summaryTrees']} discovered Phlorest dataset summary trees imported, plus WALS.</p>"
        f"<p>{st['assertions']:,} source-tagged root/parent assertions. {st['topologicalConflicts']:,} incompatible clade pairs "
        f"across study trees involve {st['recordsWithConflicts']:,} canonical records.</p>"
        "<p>This is coverage of the imported corpus, not every publication worldwide.</p>"
    )
    register = "".join(
        f'<div class="registry-source"><strong><a href="../{escape(bp.SOURCE_SLUG[s["id"]])}/">{escape(s["title"])}</a></strong><br>{escape(s["citation"])}<br>'
        f'<a href="{escape(s["url"])}" target="_blank" rel="noopener noreferrer">Paper ↗</a> · '
        f'<a href="{escape(s["dataset"])}" target="_blank" rel="noopener noreferrer">Source tree &amp; data ↗</a>'
        f"<small>{escape(s['family'])} · {escape(s['license'])} · summary tree imported</small>"
        + (f"<p>{escape(s['interpretationNote'])}</p>" if s.get("interpretationNote") else "")
        + "</div>"
        for s in u["sources"].values()
        if s.get("kind") == "study"
    )
    register = (
        f'<p><a href="../{bp.SOURCE_SLUG["wals"]}/">WALS families in Lang Log</a></p>' + register
    )
    text = text.replace("<!-- coverage -->", coverage).replace("<!-- source-register -->", register)
    # Counts in the text are computed here, never written in the source file.
    with open(bp.ROOT / "source-data" / "names.csv", encoding="utf-8", newline="") as f:
        name_rows = sum(1 for _ in csv.DictReader(f))
    for key, value in (
        ("summaryTrees", st["summaryTrees"]),
        ("nameRows", name_rows),
        ("sameLanguageLabels", st["sameLanguageLabels"]),
    ):
        text = text.replace(f"<!-- {key} -->", f"{value:,}")
    if "<!-- " in text:
        raise SystemExit(
            "sources-and-scope.html: unknown placeholder " + text[text.index("<!-- ") :][:40]
        )
    return f'<section class="home-section sources-scope" id="sources">{text}</section>'


def counts():
    """Every figure of the Stats page, counted from the data: [(heading, [(label, number)])].

    Everything is a languoid: the figures split one set of records by
    modality (spoken, signed, written) instead of by kind. Until the Lang Log
    data (schema/languoid.schema.json) carries a modality field, sign
    languages are the Glottolog records in the Sign Language category and
    writing systems are the ISO 15924 codes of the signs-and-scripts data.
    """
    st = bp.unified["stats"]
    nodes = bp.nodes.values()
    visual = json.loads((DIST / "signs-and-scripts.json").read_text(encoding="utf-8"))[
        "nodes"
    ].values()
    roots = [bp.nodes[r] for r in bp.data["roots"]]
    isolates = sum(1 for n in roots if n.get("isolate"))
    categories = sum(
        1
        for n in roots
        if n.get("category") not in ("Spoken genealogy", None) and not n.get("isolate")
    )
    not_spoken = ("Sign Language", "Bookkeeping", "Artificial Language")

    def count(category, level, spoken=False):
        return sum(
            1
            for n in nodes
            if n.get("level") == level
            and ((n.get("category") not in not_spoken) if spoken else n.get("category") == category)
        )

    return [
        (
            "All records",
            [
                ("Languoids", st["canonicalRecords"]),
                ("Glottolog records", st["glottologRecords"]),
                ("Records from study trees only", st["additionalRecords"]),
            ],
        ),
        (
            "By modality",
            [
                ("Spoken languages", count(None, "language", spoken=True)),
                ("Spoken dialects", count(None, "dialect", spoken=True)),
                ("Sign languages", count("Sign Language", "language")),
                ("Sign-language dialects", count("Sign Language", "dialect")),
                (
                    "Writing systems",
                    sum(
                        1
                        for n in visual
                        if n.get("domain") == "scripts" and n.get("kind") == "script code"
                    ),
                ),
                (
                    "Manual alphabets",
                    sum(
                        1
                        for n in visual
                        if n.get("domain") == "sign" and n.get("kind") == "manual-alphabet sample"
                    ),
                ),
            ],
        ),
        (
            "Other kinds of languages",
            [
                ("Constructed languages", count("Artificial Language", "language")),
                ("Pidgins", count("Pidgin", "language")),
                ("Mixed languages", count("Mixed Language", "language")),
            ],
        ),
        (
            "Families",
            [
                ("Top-level families", len(roots) - isolates - categories),
                ("Isolates", isolates),
                ("Families and subgroups", count(None, "family", spoken=True)),
            ],
        ),
        (
            "Sources",
            [
                ("Study trees", st["summaryTrees"]),
                ("Source-tagged placements", st["assertions"]),
                ("Conflicting clade pairs between studies", st["topologicalConflicts"]),
            ],
        ),
    ]


# Glottolog macroareas in the order the Stats page draws them.
MACROAREAS = ["Africa", "Papunesia", "Eurasia", "North America", "South America", "Australia"]


def by_macroarea():
    """Spoken languages (as counted on the Stats page) per Glottolog macroarea; a
    language in several macroareas counts for the first one."""
    not_spoken = ("Sign Language", "Bookkeeping", "Artificial Language")
    tally = {a: 0 for a in MACROAREAS}
    for n in bp.nodes.values():
        area = first_macroarea(n)
        if n.get("level") == "language" and n.get("category") not in not_spoken and area in tally:
            tally[area] += 1
    return list(tally.items())


def bars(rows):
    """A bar chart as a list: label, bar, value. The bars are SVG so their
    lengths need no inline style; every value is written next to its bar."""
    top = max(n for _, n in rows) or 1
    return (
        '<ul class="bars">'
        + "".join(
            f'<li><span class="bar-label">{escape(label)}</span>'
            f'<svg class="bar" viewBox="0 0 100 1" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
            f'<rect width="{max(100 * n / top, 0.6):.2f}" height="1"/></svg>'
            f'<span class="bar-value count" data-value="{n}">{n:,}</span></li>'
            for label, n in rows
        )
        + "</ul>"
    )


def stats_body():
    figures = {label: n for _, rows in counts() for label, n in rows}
    hero = "".join(
        f'<div><dd class="count" data-value="{figures[k]}">{figures[k]:,}</dd><dt>{escape(k)}</dt></div>'
        for k in ("Languoids", "Sign languages", "Writing systems", "Study trees")
    )
    modality = [
        (k, figures[k])
        for k in ("Spoken languages", "Sign languages", "Writing systems", "Constructed languages")
    ]
    groups = "".join(
        f'<h3>{escape(h)}</h3><dl class="stat-list">'
        + "".join(f"<div><dt>{escape(label)}</dt><dd>{n:,}</dd></div>" for label, n in rows)
        + "</dl>"
        for h, rows in counts()
    )
    return (
        '<p class="muted">Counted from the data each time the site is built. '
        "Different kinds of records are counted separately; do not add them up.</p>"
        f'<dl class="stat-hero">{hero}</dl>'
        f'<section class="stats-group"><h2>By modality</h2>{bars(modality)}</section>'
        f'<section class="stats-group"><h2>Spoken languages by macroarea</h2>{bars(by_macroarea())}</section>'
        f'<details class="stats-group all-figures"><summary>All figures</summary>{groups}</details>'
    )


def updates_body():
    entries = json.loads(
        (bp.ROOT / "source-data" / "lang-log" / "updates.json").read_text(encoding="utf-8")
    )["updates"]
    rows = []
    for e in entries:
        day = datetime.date.fromisoformat(e["date"])
        text = escape(e["text"])
        if e.get("link"):
            text = f'<a href="../{escape(e["link"])}">{text}</a>'
        rows.append(
            f'<li><time datetime="{day.isoformat()}">{day.strftime("%-d %b %Y")}</time> <span>{text}</span></li>'
        )
    return f'<ul class="updates">{"".join(rows)}</ul>'


def sub_page(slug, title, body, scripts=()):
    """A page one level below the root, such as dist/stats/index.html. `scripts` are
    extra files from dist/ loaded in <head> after lang.js."""
    (DIST / slug).mkdir(exist_ok=True)
    (DIST / slug / "index.html").write_text(
        info_page.page(title, body, "../", scripts), encoding="utf-8"
    )


def main():
    st = bp.unified["stats"]
    retrieved = datetime.date.fromisoformat(bp.data["retrieved"]).strftime("%-d %b %Y")
    description = (
        "Lang Log: an atlas of language families, sign languages and writing systems, "
        "with source-linked classifications, alternative hypotheses and exportable data."
    )
    html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        + SECURITY_HEAD
        + '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{escape(description)}">'
        f"<title>{HOME_TITLE}</title>"
        '<link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="apple-touch-icon.png">'
        '<link rel="stylesheet" href="style.css">'
        '<script src="theme.js"></script><script src="i18n.js"></script><script src="lang.js"></script>'
        '<link rel="search" type="application/opensearchdescription+xml" title="Lang Log" href="opensearch.xml">'
        '</head><body class="home-page">\n'
        '<header><div class="brand"><a class="home" href="./" aria-current="page"><svg class="logo" role="img" aria-label="LANG LOG"><use href="logo.svg#logo"/></svg></a> '
        + by_yoshi()
        + "</div>"
        "</header>\n"
        '<main class="home-main">'
        '<section class="home-intro">'
        '<h1 class="home-logo"><svg class="logo" role="img" aria-label="LANG LOG"><use href="logo.svg#logo"/></svg></h1>'
        + by_yoshi("p", "home-by")
        + '<form class="home-search" action="q" method="get" role="search">'
        '<label class="visually-hidden" for="home-q">Search languages and families</label>'
        '<div class="search-pill">'
        '<input id="home-q" name="q" type="search" placeholder="Name, ISO code, Glottocode…" autocomplete="off">'
        '<button type="submit" aria-label="Search" title="Search">'
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>'
        "</button></div></form>"
        f'<div class="home-actions">{random_row()}{guide_row()}</div>'
        '<p class="sub">An atlas of language families, sign languages and writing systems. '
        "Every placement says which source it follows, competing classifications are shown together, "
        "and the data can be downloaded.</p></section>\n"
        f"{families_html()}{tree_section()}"
        '<section class="home-more"><h2>Also</h2><ul>'
        '<li><a href="feature-map.html">Language feature map</a>: every language on a world map, '
        "narrowed by conditions on WALS features and coloured by one of them.</li>"
        "<li>Corpora and data for low-resource languages: planned.</li>"
        "</ul></section></main>\n"
        f"<footer><span>Glottolog 5.3 + WALS + {st['summaryTrees']} Phlorest summary trees · Retrieved {retrieved}</span>"
        "<span>Sources: Glottolog, WALS, published study trees and script catalogs, each under its own license</span>"
        f"<span>{COPYRIGHT}</span></footer>\n"
        '<script src="home.js"></script><script src="atlas-data.js"></script><script src="lineage-paths.js"></script><script src="tree.js"></script>\n'
        "</body></html>\n"
    )
    (DIST / "index.html").write_text(html, encoding="utf-8")
    sub_page("stats", "Stats", stats_body(), scripts=("stats.js",))
    sub_page("sources", "Sources & scope", sources_section())
    sub_page("updates", "Updates", updates_body())
    (DIST / "random.json").write_text(
        json.dumps(random_pools(), separators=(",", ":")), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
