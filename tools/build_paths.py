"""Write one static page and one JSON file per Glottolog record, at a URL
that follows the classification: dist/<family>/<subgroup>/.../<language>/
(served as https://lang-log.com/<family>/.../<language>/).

Run after tools/finish_unified.py (it reads dist/data.json and dist/integrated.json);
tools/build_site.sh runs them in order.

- Each path segment is an ASCII slug of the record name. When two siblings
  share a slug, both get "-<glottocode>" appended, so a URL never depends on
  the order of the data.
- Every record has its own page at its place in Glottolog, historical
  stages (for example Old English) too. Lang Log's own classification
  (source-data/lang-log/classification.json, such as Old English as the
  parent of Middle English) is shown on the page next to Glottolog's and
  does not change the URL.
- Records that exist only in another source's tree (WALS genera and
  families, clades and unmatched samples of the study trees) get the same kind
  of page under that source: dist/<source>/<path in that tree>/, for example
  dist/wals/turkic/azerbaijani/. A study tree's root is the source's own page
  (dist/gray-et-al-2009/); dist/wals/ lists the WALS families. Glottolog
  records inside a source tree link to their Glottolog page.
  dist/source-paths.json maps each of these records to its path for the
  scripts.
- The top page (dist/index.html, tools/build_home.py) lists the top-level
  families and isolates; breadcrumbs start there ("Top").
- A top-level slug (family or source) must not equal another top-level slug
  or a name already used at the top of dist/ (RESERVED); the build stops if
  one does.
- The pages need no JavaScript (dist/map-zoom.js only adds zoom and pan to
  the map). dist/lineage-paths.js uses the same rules to
  link to Glottolog records. Each page also has two parts that need it: the
  tree of its branch (dist/tree.js, drawn when the visitor asks for it) and
  the Hugging Face models (dist/hf-models.js).
"""

from html import escape

from locations import DIST, ROOT
from pwa import head_tags as pwa_head
from security_policy import HEAD as SECURITY_HEAD
from site_brand import SITE_NAME_META, TITLE_SUFFIX, by_yoshi, contact_line, icon_links
import csv
import json
import re
import shutil
import sys
import unicodedata

from build_wals_map import condition_languages, glottolog
from explore_panel import explore_open
from languoid_map import map_svg
from modality import labels, medium_words
from record_facts import facts
from source_versions import CLDR, GLOTTOLOG, SOURCE_TITLES

OUT = DIST
# Top-level names in dist/ that a family or source slug must not take.
RESERVED = {"map", "data", "i18n", "stats", "sources", "features", "schema"}
# Directories of earlier builds that no longer exist; removed on each run.
OLD_DIRS = {
    "families",
    "sign-language",
    "bookkeeping",
    "pidgin",
    "unclassifiable",
    "unattested",
    "artificial-language",
    "speech-register",
    "mixed-language",
}

data = json.loads((DIST / "data.json").read_text(encoding="utf-8"))
unified = json.loads((DIST / "integrated.json").read_text(encoding="utf-8"))
# Lang Log's own classification: child -> parent, and parent -> children.
lang_log_parent = {
    c: v["parent"]
    for c, v in json.loads(
        (ROOT / "source-data" / "lang-log" / "classification.json").read_text(encoding="utf-8")
    )["parents"].items()
}
lang_log_children = {}
for _c, _p in lang_log_parent.items():
    lang_log_children.setdefault(_p, []).append(_c)
nodes = data["nodes"]
extra = unified["extraNodes"]
sources = unified["sources"]


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def segments_for(ids):
    """Slug for each id among its siblings, with collisions disambiguated."""
    base = {i: slug(nodes[i]["name"]) or i for i in ids}
    count = {}
    for s in base.values():
        count[s] = count.get(s, 0) + 1
    return {i: (s if count[s] == 1 else s + "-" + i) for i, s in base.items()}


segment = {}
segment.update(segments_for(data["roots"]))
for n in nodes.values():
    segment.update(segments_for(n["children"]))

path_cache = {}


def source_slug(sid):
    """URL name of a source: gray_et_al2009 -> gray-et-al-2009, wals -> wals."""
    return re.sub(r"([a-z])(\d{4})$", r"\1-\2", slug(sid.replace("_", " ")))


SOURCE_SLUG = {sid: source_slug(sid) for sid in sources if sid != "glottolog"}

# Members of each record in each source tree: (source, parent) -> assertions.
by_source = {}
for e in unified["assertions"]:
    if e.get("parent"):
        by_source.setdefault((e["source"], e["parent"]), []).append(e)

# A study tree's root record is the source page itself.
study_root = {i for i, n in extra.items() if not n.get("parent") and n["source"] != "wals"}


def extra_segments(ids):
    base = {i: slug(extra[i]["name"]) or slug(i.split(":")[-1]) for i in ids}
    count = {}
    for s in base.values():
        count[s] = count.get(s, 0) + 1
    return {i: (s if count[s] == 1 else s + "-" + slug(i.split(":")[-1])) for i, s in base.items()}


extra_segment = {}
extra_segment.update(
    extra_segments([i for i, n in extra.items() if n["source"] == "wals" and not n.get("parent")])
)
_extra_kids = {}
for i, n in extra.items():
    if n.get("parent"):
        _extra_kids.setdefault(n["parent"], []).append(i)
for kids in _extra_kids.values():
    extra_segment.update(extra_segments(kids))


def rec(i):
    """A record of any source: a Glottolog record or a source-only record."""
    return nodes.get(i) or extra.get(i) or {"id": i, "name": i, "level": "", "children": []}


# The Glottocodes of the languages the conditions of the explorer choose from.
condition_ids = {r["ID"] for r in condition_languages(glottolog())}

# Glottolog's representative point of each record, as (longitude, latitude), and the first
# and last years in which it was documented, as Glottolog gives them (either may be empty).
coords = {}
documented = {}
with open(ROOT / "source-data" / "languages.csv", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        if row["ID"] not in nodes:
            continue
        if row["Latitude"] and row["Longitude"]:
            coords[row["ID"]] = (float(row["Longitude"]), float(row["Latitude"]))
        years = (row["First_Year_Of_Documentation"], row["Last_Year_Of_Documentation"])
        if any(years):
            documented[row["ID"]] = years
# ISO 639-3 -> ISO 639-1, from the exact equivalences Lang Log keeps (also used by dist/hf-iso-map.js).
iso_639_1 = {
    three: two
    for two, three in json.loads(
        (ROOT / "source-data" / "iso-map.json").read_text(encoding="utf-8")
    ).items()
}
# Feature values of each WALS language, as ((order, feature name), value name), read from
# the WALS files (the same values tools/build_languoids.py converts).
wals_values = {}
with open(ROOT / "source-data" / "wals" / "parameters.csv", encoding="utf-8", newline="") as f:
    _features = {r["ID"]: (k, r["Name"]) for k, r in enumerate(csv.DictReader(f))}
with open(ROOT / "source-data" / "wals" / "codes.csv", encoding="utf-8", newline="") as f:
    _values = {r["ID"]: r["Name"] for r in csv.DictReader(f)}
with open(ROOT / "source-data" / "wals" / "values.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        wals_values.setdefault(r["Language_ID"], []).append(
            (_features[r["Parameter_ID"]], _values[r["Code_ID"]])
        )


def _points_under():
    """For every record: the deepest records on each of its branches that Glottolog gives a
    point, and how many records at the ends of its branches have no point on their way up.
    A record with no point below it stands for itself. The same rule for every record,
    whatever its level: every record is a languoid (.claude/rules/interface-text.md)."""
    found, unplaced = {}, {}

    def walk(i):
        if i in found:
            return
        pts, none = [], 0
        kids = [c for c in nodes[i]["children"] if c in nodes]
        for c in kids:
            walk(c)
            pts += found[c]
            none += unplaced[c]
        if not pts and i in coords:
            pts, none = [i], 0
        elif not kids:
            none = 1
        found[i], unplaced[i] = pts, none

    for i in nodes:
        walk(i)
    return found, unplaced


points_under, unplaced_under = _points_under()


def path_of(i):
    """URL path below the atlas root, without leading or trailing slash."""
    if i in path_cache:
        return path_cache[i]
    if i in extra:
        n = extra[i]
        if i in study_root:
            p = SOURCE_SLUG[n["source"]]
        elif n.get("parent"):
            p = path_of(n["parent"]) + "/" + extra_segment[i]
        else:  # a WALS family
            p = SOURCE_SLUG[n["source"]] + "/" + extra_segment[i]
    else:
        parent = nodes[i].get("parent")
        p = (path_of(parent) + "/" if parent else "") + segment[i]
    path_cache[i] = p
    return p


def lineage(i):
    out = []
    seen = set()
    while i and i in nodes and i not in seen:
        seen.add(i)
        out.insert(0, i)
        i = nodes[i].get("parent")
    return out


def href(from_dir_depth, target_id):
    """Relative link from a page at depth from_dir_depth below the atlas root to a record."""
    return "../" * from_dir_depth + path_of(target_id) + "/"


def href_source(depth, sid):
    """Relative link to a source's own page (Glottolog's page is the top page)."""
    return "../" * depth + (SOURCE_SLUG[sid] + "/" if sid in SOURCE_SLUG else "")


def source_link(sid):
    s = sources.get(sid)
    if not s:
        return escape(sid)
    return f'<a href="{escape(s["url"])}" target="_blank" rel="noopener noreferrer">{escape(s["title"])}</a>'


def names_rows(n):
    """The facts-table rows for a record's own names and the names other sources record."""
    own = sorted({r["text"] for r in n.get("nativeNames", [])})
    seen = {}
    for r in n.get("names", []):
        if r.get("placeholder"):
            continue
        seen.setdefault((r["text"], r.get("lang", "")), set()).add(r.get("provider", ""))
    rows = []
    if own:
        rows.append(
            (
                "Name in this language",
                f'<span dir="auto">{" / ".join(escape(x) for x in own)}</span>',
            )
        )
    if seen:  # an empty toggle would open onto nothing, so leave it out
        items = "".join(
            f'<li dir="auto">{escape(t)} <span class="muted">{escape(tag or "tag unspecified")} · {escape(" · ".join(sorted(p)))}</span></li>'
            for (t, tag), p in sorted(seen.items())
        )
        rows.append(
            (
                "Recorded names and spellings",
                f'<details><summary>{len(seen)}</summary><ul class="name-list">{items}</ul></details>',
            )
        )
    return rows


def ext_link(sid):
    """Link to a source's paper or catalog, as on the old atlas cards."""
    src = sources.get(sid)
    if not src:
        return ""
    label = "Catalog" if src.get("kind") == "catalog" else "Paper"
    return f'<a href="{escape(src["url"])}" target="_blank" rel="noopener noreferrer">{label} ↗</a>'


def source_name_link(depth, sid):
    """A source's title, linked to its tree in Lang Log (Glottolog: the top page)."""
    return f'<a href="{escape(href_source(depth, sid))}">{escape(sources.get(sid, {}).get("title", sid))}</a>'


def record_link(depth, i):
    # A study tree's root is shown as the study itself (its page is the source's page).
    name = sources[extra[i]["source"]]["title"] if i in study_root else rec(i)["name"]
    return f'<a href="{escape(href(depth, i))}">{escape(name)}</a>'


def cell(content, label):
    """One cell of a data table. The column's label is repeated inside the cell for
    the phone layout (dist/record.css shows each row as a block there)."""
    if not content:
        return '<td class="data-empty"></td>'
    return f'<td><span class="data-label" aria-hidden="true">{escape(label)}</span>{content}</td>'


def data_table(head, rows):
    """A table with a header row (the data table of record pages, dist/record.css).
    Each row is (cells, row class): one HTML string per column, an empty string for an
    empty cell, and "" when the row has no class of its own."""
    thead = "".join(f'<th scope="col">{escape(h)}</th>' for h in head)
    body = ""
    for cells, cls in rows:
        attr = f' class="{escape(cls)}"' if cls else ""
        body += (
            f"<tr{attr}>" + "".join(cell(x, h) for x, h in zip(cells, head, strict=True)) + "</tr>"
        )
    return f'<table class="data-table"><thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table>'


def facts_table(rows, header_html=False):
    """A table of one fact per row: the label as a row header, then the value (HTML).
    With header_html the labels are HTML too (links), otherwise plain text."""
    body = "".join(
        f'<tr><th scope="row">{k if header_html else escape(k)}</th><td>{v}</td></tr>'
        for k, v in rows
    )
    return f'<table class="data-table facts-table"><tbody>{body}</tbody></table>'


def classification_html(depth, i):
    """Every source's placement of a record, with its other direct members, and
    the other sources' trees attached below it, as tables."""
    n = rec(i)
    rows = []
    if i in nodes and not nodes[i].get("parent"):
        rows.append(([source_name_link(depth, "glottolog"), "", "", "", ext_link("glottolog")], ""))
    seen = set()
    unique = []
    for e in unified["placements"].get(i, []):
        key = (e["source"], e["parent"], e.get("sample", ""))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    if i in extra and not unique and n.get("parent"):
        unique.append({"source": n["source"], "parent": n["parent"]})
    for e in unique:
        peers = []
        for x in by_source.get((e["source"], e["parent"]), []):
            if x["child"] != i and x["child"] not in peers:
                peers.append(x["child"])
        more = f' <span class="muted">and {len(peers) - 5} more</span>' if len(peers) > 5 else ""
        peer_html = ", ".join(record_link(depth, x) for x in peers[:5]) + more if peers else ""
        rows.append(
            (
                [
                    source_name_link(depth, e["source"]),
                    record_link(depth, e["parent"]),
                    escape(e.get("sample", "")),
                    peer_html,
                    ext_link(e["source"]),
                ],
                "",
            )
        )
    out = '<section class="classification"><h3>Classification by source</h3>' + data_table(
        ["Source", "Placement", "Source sample / record", "Other direct members", "Link"], rows
    )
    attached = unified["anchors"].get(i, []) if i in nodes else []
    if attached:
        out += "<h4>Other sources' trees below this record</h4>" + facts_table(
            [
                (
                    f'<a href="{escape(href(depth, a["root"]))}">If following {escape(sources[a["source"]]["title"])}</a>',
                    "catalog grouping" if a["type"] == "catalog" else "sampled study tree",
                )
                for a in attached
            ],
            header_html=True,
        )
    return out + "</section>"


def debates_html(i):
    ids = set(lineage(i)) if i in nodes else {i}
    out = ""
    for d in unified.get("debates", []):
        if not ids & set(d["appliesTo"]):
            continue
        rows = [
            (
                [
                    escape(p["author"]),
                    escape(p["publication"]),
                    f'<a href="{escape(p["url"])}" target="_blank" rel="noopener noreferrer">Paper ↗</a>',
                ],
                "conflict-row" if p.get("stance") == "critique" else "",
            )
            for p in d["positions"]
        ]
        out += (
            f'<section class="debate"><h3>{escape(d["title"])}</h3>'
            + data_table(["Source", "Publication", "Link"], rows)
            + "</section>"
        )
    return out


def conflicts_html(depth, i):
    refs = unified["conflictIndex"].get(i, [])
    if not refs:
        return ""
    pairs = {}
    for k in refs:
        c = unified["conflicts"][k]
        pairs.setdefault((c["a"], c["b"]), [c, 0])[1] += 1

    def title(sid):
        return escape(sources[sid]["title"])

    rows = []
    for c, count in pairs.values():
        a, b, d = (escape(rec(x)["name"]) for x in c["witness"])
        rows.append(
            (
                [
                    f"{title(c['a'])} vs {title(c['b'])}",
                    f'<span class="conflict-witness">{title(c["a"])}: [{a} + {b}] before {d}.<br>{title(c["b"])}: [{b} + {d}] before {a}.</span>'
                    f'<span class="small-disclaimer">Same {c["sharedTips"]} sampled IDs compared · {count} incompatible clade pair(s) involving this record.</span>',
                    f"{ext_link(c['a'])} {ext_link(c['b'])}<br>"
                    f'<a href="{escape(href(depth, c["cladeA"]))}">Clade in {title(c["a"])}</a> · '
                    f'<a href="{escape(href(depth, c["cladeB"]))}">Clade in {title(c["b"])}</a>',
                ],
                "conflict-row",
            )
        )
    out = (
        f'<section class="conflicts"><h3>Incompatible study branches · {len(pairs)} source pairs</h3>'
        + data_table(["Source", "Difference", "Link"], rows)
    )
    return out + "</section>"


def tree_html(depth, i, sid):
    """The branch below a record, drawn by dist/tree.js when the visitor asks for it.
    Hidden without JavaScript; the Members list gives the same records."""
    return (
        '<section id="tree-section" hidden><h3>Tree</h3>'
        '<p><button type="button" id="show-tree" class="show-tree">Show the tree of this branch</button></p>'
        + atlas_html("../" * depth, root=i, src=sid)
        + "</section>"
    )


def download_icon():
    """The download symbol of the map's PNG button, drawn as icon() in dist/map-zoom.js
    draws it; the path is read from ICON_DOWNLOAD there, so it is written once."""
    m = re.search(r"ICON_DOWNLOAD = '([^']+)'", (DIST / "map-zoom.js").read_text())
    if not m:
        sys.exit("dist/map-zoom.js has no ICON_DOWNLOAD")
    return (
        '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">'
        f'<path d="{escape(m[1])}" fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def atlas_html(base, root=None, src=None, downloads=""):
    """The zoomable tree that dist/tree.js fills: the branch below a record (record
    pages, with its outline and a List / Tree switch), or every root (the top page's
    list, without them: only its Download menu shows there, and the canvas is drawn
    for the SVG export, dist/tree.js)."""
    whole = root is None
    attrs = f' data-base="{escape(base)}"' + (
        "" if whole else f' data-root="{escape(root)}" data-src="{escape(src)}"'
    )
    switch = (
        ""
        if whole
        else (
            '<div class="seg" role="group" aria-label="View"><button id="listview" type="button" aria-pressed="true">List</button>'
            '<button id="chartview" type="button" aria-pressed="false">Tree</button></div><button id="collapse" type="button">Collapse all</button>'
        )
    )
    outline = (
        ""
        if whole
        else '<div id="outline" role="group" aria-label="Expandable classification outline"></div>'
    )
    # The Download menu's button is always the map's download symbol, never the word
    # (the owner's rule, 2026-11-23). The top page shows only this menu, with no box.
    summary = f'<summary aria-label="Download" title="Download">{download_icon()}</summary>'
    return (
        f'<div id="atlas" class="workspace atlas-embed{" atlas-whole" if whole else ""}"{attrs} hidden>'
        f'<div class="toolbar">{switch}'
        f'<details class="menu downloads">{summary}<div class="menu-panel"><button id="export" type="button">SVG (current view)</button>{downloads}</div></details></div>'
        f"{outline}"
        f'<div id="viewport"{"" if whole else " hidden"}><canvas id="tree" aria-label="Interactive language classification tree. Click a node to open its page."></canvas>'
        '<div class="canvas-title"><span class="eyebrow">INTEGRATED · SOURCE-CONDITIONED</span><h2 id="view-title">Language families</h2>'
        '<p id="view-count">Loading records…</p></div><div id="tooltip" hidden></div>'
        '<div class="zoom"><button id="minus" type="button" aria-label="Zoom out">−</button><button id="fit" type="button">Fit</button>'
        '<button id="plus" type="button" aria-label="Zoom in">+</button></div>'
        "</div></div>"
    )


def hf_html(n):
    """Hugging Face models, loaded from the Hub when the section scrolls into view (dist/record-page.js)."""
    return (
        f'<section class="hf-models" id="hf-models" hidden data-name="{escape(n["name"])}" '
        f'data-level="{escape(n.get("level", ""))}" data-iso="{escape(n.get("iso", ""))}" aria-label="Hugging Face models"></section>'
    )


def breadcrumb(depth, ids, sid="glottolog"):
    """Classification path from the top page down to (not including) this record."""
    title = escape(
        sources.get(sid, {}).get("title", sid).split(" ")[0]
        if sid == "glottolog"
        else sources.get(sid, {}).get("title", sid)
    )
    items = f'<li><a href="{"../" * depth}">Top</a></li>'
    if sid != "glottolog":
        items += f'<li><a href="{escape(href_source(depth, sid))}">{escape(sources[sid]["title"])}</a></li>'
    items += "".join(
        f'<li><a href="{escape(href(depth, a))}">{escape(rec(a)["name"])}</a></li>'
        for a in ids
        if a not in study_root
    )
    return f'<nav class="lineage" aria-label="Classification according to {title}"><ol class="lineage-path">{items}</ol></nav>'


def lang_log_lineage(depth, i):
    """The record's ancestors in Lang Log's own classification (oldest first),
    shown under Glottolog's classification path."""
    up, p = [], lang_log_parent.get(i)
    while p:
        up.insert(0, p)
        p = lang_log_parent.get(p)
    if not up:
        return ""
    items = "".join(
        f'<li><a href="{escape(href(depth, a))}">{escape(nodes[a]["name"])}</a></li>' for a in up
    )
    return (
        '<nav class="lineage" aria-label="Classification according to Lang Log">'
        f'<ol class="lineage-path">{items}</ol></nav>'
    )


def lang_log_members(depth, i):
    """The record's children in Lang Log's own classification."""
    kids = sorted(lang_log_children.get(i, []), key=lambda c: nodes[c]["name"].lower())
    if not kids:
        return ""
    rows = [
        ([f'<a href="{escape(href(depth, c))}">{escape(nodes[c]["name"])}</a>'], "") for c in kids
    ]
    return (
        f'<section class="members"><h3>Members according to Lang Log · {len(kids)}</h3>'
        + data_table(["Name"], rows)
        + "</section>"
    )


def children_html(depth, i):
    if i in nodes:
        kids = [(c, "") for c in nodes[i]["children"]]
    else:  # members in the record's own source tree, with the source's sample label
        kids, seen = [], set()
        for e in by_source.get((extra[i]["source"], i), []):
            if e["child"] not in seen:
                seen.add(e["child"])
                kids.append((e["child"], e.get("sample", "")))
    if not kids:
        return ""
    kids.sort(key=lambda c: rec(c[0])["name"].lower())
    samples = any(sm and sm != rec(c)["name"] for c, sm in kids)
    head = ["Name", "Source sample / record"] if samples else ["Name"]
    rows = [
        (
            [record_link(depth, c)]
            + ([escape(sm) if sm and sm != rec(c)["name"] else ""] if samples else []),
            "",
        )
        for c, sm in kids
    ]
    return (
        f'<section class="members"><h3>Members · {len(kids)}</h3>{data_table(head, rows)}</section>'
    )


def group(title, inner, hidden=False):
    """One group of a record page (names, codes, classification ...): a heading and its tables.
    The groups and their order are the owner's (2026-11-23); a group with nothing in it is left out."""
    if not inner:
        return ""
    return f'<section class="record-group"{" hidden" if hidden else ""}><h2>{escape(title)}</h2>{inner}</section>'


def codes_rows(n, f):
    """The record's identifiers: its Lang Log id (a Glottocode for Glottolog records) and codes."""
    i = n["id"]
    rows = [("Glottocode" if i in nodes else "ID", escape(i))]
    if i in extra:
        rows.append(("Source", escape(sources[n["source"]]["title"])))
    if n.get("iso"):
        rows.append(("ISO 639-3", escape(n["iso"])))
        if n["iso"] in iso_639_1:
            rows.append(("ISO 639-1", escape(iso_639_1[n["iso"]])))
    meta = f["linguameta"]
    if meta and meta["iso639_2b"]:
        rows.append(("ISO 639-2/B", escape(meta["iso639_2b"])))
    registry = f["registry"]
    if registry:
        rows.append(("Language tag", f'<span dir="ltr">{escape(registry["tag"])}</span>'))
        rows.append(("Code scope", f"<span>{escape(SCOPES[registry['scope']])}</span>"))
        if registry["macrolanguage"]:
            rows.append(("Macrolanguage", escape(registry["macrolanguage"])))
        if registry["replaced_by"]:
            rows.append(("Replaced by", escape(registry["replaced_by"])))
        if registry["retired"]:
            rows.append(("Retired tags", escape(", ".join(registry["retired"]))))
    if n.get("wals"):
        rows.append(("WALS code", escape(", ".join(n["wals"]))))
    return rows


# Display names of the values the sources give (tools/record_facts.py), as interface text.
SCOPES = {
    "individual": "Individual language",
    "macrolanguage": "Macrolanguage",
    "collection": "Collection",
    "special": "Special",
    "private-use": "Special",
}
OFFICIAL = {
    "official": "Official",
    "de_facto_official": "Official in practice",
    "official_regional": "Official in a region",
}


def sentence_case(value):
    """A source's value name ("nearly extinct") as a label ("Nearly extinct")."""
    return value[:1].upper() + value[1:]


def scripts_html(scripts):
    # Script codes, named by dist/record-page.js in the page's language (Intl.DisplayNames).
    return ", ".join(
        f'<span class="script" data-script="{escape(s["script"])}">{escape(s["script"])}</span>'
        for s in scripts
    )


def percent_html(value):
    # A plain number here; dist/record-page.js writes it in the page's language.
    return f'<span class="percent" data-percent="{value:g}" dir="ltr">{value:g}%</span>'


def number_html(value):
    # A plain number here; dist/record-page.js writes it in the page's language.
    return f'<span class="number" data-number="{value}" dir="ltr">{value}</span>'


def speakers_html(f):
    out = ""
    meta = f["linguameta"]
    if meta and meta["speakers"]:
        out += facts_table([("Estimated speakers", number_html(meta["speakers"]))])
    societies = [
        (
            [
                f'<a class="notranslate" href="https://d-place.org/society/{escape(x["society"])}" '
                f'target="_blank" rel="noopener noreferrer">{escape(x["name"])} ↗</a>',
                f'<span class="notranslate">{escape(x["region"])}</span>' if x["region"] else "",
                f'<span dir="ltr">{x["focal_year"]}</span>' if x["focal_year"] is not None else "",
            ],
            "",
        )
        for x in f["societies"]
    ]
    if societies:
        out += data_table(["Society", "Region", "Focal year"], societies)
    rows = [
        ([region_html(c["country"]), percent_html(c["population_percent"])], "")
        for c in f["speakers_by_country"]
    ]
    if rows:
        out += data_table(["Country", "Share of the population"], rows)
    return out


def society_html(f):
    rows = [
        (
            [region_html(c["country"]), f"<span>{escape(OFFICIAL[c['official_status']])}</span>"],
            "",
        )
        for c in f["speakers_by_country"]
        if c["official_status"]
    ]
    return data_table(["Country", "Status"], rows) if rows else ""


def vitality_html(f):
    # Each source's own scale, side by side, never merged (.claude/rules/data.md).
    rows = []
    if f["endangerment"]:
        rows.append((sentence_case(f["endangerment"]["value"]), "glottolog"))
    if f["linguameta"] and f["linguameta"]["endangerment"]:
        rows.append((f["linguameta"]["endangerment"], "linguameta"))
    if not rows:
        return ""
    return data_table(
        ["Endangerment", "Source"],
        [([f"<span>{escape(v)}</span>", escape(SOURCE_TITLES[sid])], "") for v, sid in rows],
    )


def features_html(n, f):
    out = ""
    plural = f["plural_categories"]
    if plural:
        words = escape(", ".join(plural["values"]))
        out += facts_table(
            [("Plural categories", f'<span class="notranslate" dir="ltr">{words}</span>')]
        )
    inventories = [
        (
            [
                f'<a class="notranslate" href="https://phoible.org/inventories/view/{escape(x["inventory"])}" '
                f'target="_blank" rel="noopener noreferrer">{escape(x["contributor"])} {escape(x["inventory"])} ↗</a>',
            ]
            + [
                f'<span dir="ltr"><span>{len(x[k])}</span> <span class="notranslate phonemes">{escape(" ".join(x[k]))}</span></span>'
                if x[k]
                else ""
                for k in ("consonants", "vowels", "tones")
            ],
            "",
        )
        for x in f["phonemes"]
    ]
    if inventories:
        out += data_table(["Inventory", "Consonants", "Vowels", "Tones"], inventories)
    seen = {}
    for w in n.get("wals") or []:
        for feature, value in wals_values.get(w, []):
            seen.setdefault(feature, value)
    if seen:
        rows = [
            ([f"<span>{escape(name)}</span>", f"<span>{escape(v)}</span>"], "")
            for (_, name), v in sorted(seen.items())
        ]
        # As long as a hundred rows, so folded like the recorded names (names_rows).
        out += facts_table(
            [
                (
                    "Feature values",
                    f"<details><summary>{len(rows)}</summary>{data_table(['Feature', 'Value'], rows)}</details>",
                )
            ]
        )
    return out


def description_rows(f):
    d = f["description"]
    if not d:
        return []
    value = f"<span>{escape(sentence_case(d['value']))}</span>"
    if d.get("reference"):
        value += f'<br><span class="notranslate">{escape(d["reference"])}</span>'
    return [("Most extensive description", value)]


def medium_rows(n, f):
    # Every languoid is labelled with its medium (tools/modality.py); records that
    # exist only in a study tree or WALS are spoken languages. Each word is its own
    # element, so dist/lang.js translates them one by one.
    words = medium_words(n if "modality" in n else labels(None))
    rows = [("Medium", " · ".join(f"<span>{escape(w)}</span>" for w in words))]
    main = [s for s in f["scripts"] if s["use"] == "main"]
    other = [s for s in f["scripts"] if s["use"] == "other"]
    if main:
        rows.append(("Scripts", scripts_html(main)))
    if other:
        rows.append(("Other scripts", scripts_html(other)))
    return rows


def region_html(code):
    # A country code, named by dist/record-page.js in the page's language (Intl.DisplayNames).
    return f'<span class="region" data-region="{escape(code)}">{escape(code)}</span>'


def place_rows(n):
    """Area, countries (named by dist/record-page.js in the page's language) and the point."""
    rows = []
    if n.get("area"):
        rows.append(("Area", f"<span>{escape(n['area'])}</span>"))
    if n.get("countries"):
        rows.append(
            (
                "Countries",
                ", ".join(region_html(c) for c in n["countries"].split(";")),
            )
        )
    if n["id"] in coords:
        lon, lat = coords[n["id"]]
        rows.append(("Coordinates", f'<span dir="ltr">{lat}, {lon}</span>'))
    return rows


def record_body(depth, i, sid):
    """Everything on a record page after the breadcrumb, in the owner's groups (2026-11-23):
    names, codes, medium and writing, classification, place, speakers, vitality, status in
    society, features, records and resources, links. A group with nothing in it is left out."""
    n = rec(i)
    names = names_rows(n)
    place = place_rows(n)
    years = documented.get(i)
    f = facts(i if i in nodes else None, n.get("iso") or None)
    body = f"<h1>{escape(n['name'])}</h1>"
    # The map comes first, right under the name, with the tree of the record's descendants
    # as the list view behind the same switch as the top page's (owner, 2026-11-24). A
    # record with no descendants shows only the map; one with no map keeps the tree under
    # Classification.
    the_map = map_html(depth, i) if i in nodes else ""
    langs = languages_under(i) if the_map else []
    tree_in_views = bool(langs)
    if the_map:
        body += record_views(depth, i, sid, the_map, langs)
    members = children_html(depth, i) + (lang_log_members(depth, i) if i in nodes else "")
    body += group("Names", facts_table(names) if names else "")
    body += group("Codes", facts_table(codes_rows(n, f)))
    body += group("Medium and writing", facts_table(medium_rows(n, f)))
    body += group(
        "Classification",
        classification_html(depth, i)
        + conflicts_html(depth, i)
        + debates_html(i)
        + members
        + ("" if tree_in_views else tree_html(depth, i, sid)),
    )
    body += group("Place", facts_table(place) if place else "")
    body += group("Speakers", speakers_html(f))
    body += group("Vitality", vitality_html(f))
    body += group("Status in society", society_html(f))
    body += group("Features", features_html(n, f))
    record_rows = [("Years of documentation", escape("–".join(years)))] if years else []
    record_rows += description_rows(f)
    records = facts_table(record_rows) if record_rows else ""
    # The models section needs JavaScript; with nothing else in the group, the group starts
    # hidden and dist/record-page.js shows it with the models.
    body += group("Records and resources", records + hf_html(n), hidden=not records)
    if i in extra:
        links = [ext_link(n["source"])]
    else:
        links = [
            f'<a href="https://glottolog.org/resource/languoid/id/{escape(i)}" target="_blank" rel="noopener noreferrer">Glottolog record ↗</a>'
        ]
    links.append(
        f'<a href="{"../" * depth}record.html?domain=language&amp;id={escape(i)}">Full source detail</a>'
    )
    if f["linguameta"] and f["linguameta"]["wikidata"]:
        q = escape(f["linguameta"]["wikidata"])
        links.append(
            f'<a href="https://www.wikidata.org/wiki/{q}" target="_blank" rel="noopener noreferrer">Wikidata item ↗</a>'
        )
    links.append('<a href="record.json">This record as JSON</a>')
    body += group("Links", facts_table([("Links", " · ".join(links))]))
    return body


def record_views(depth, i, sid, the_map, langs):
    """The top of a record page: its map and, when it has descendants, the same explorer as
    the top page's (tools/explore_panel.py, run by dist/explore.js): the switch between the
    map and the tree of its descendants (the list view), and the conditions, which narrow
    both to its languages. The map is shown first (?view=list for the tree). Without
    scripts only the map is shown. `langs`: languages_under(i)."""
    if not langs:
        return f'<section class="record-views">{the_map}</section>'
    return (
        explore_open("record-views", "../" * depth, "map", len(langs), langs)
        + f'<div class="explore-view" data-view="list" hidden>{atlas_html("../" * depth, root=i, src=sid)}</div>'
        + f'<div class="explore-view" data-view="map">{the_map}</div></section>'
    )


def languages_under(i):
    """The languages the conditions choose from (condition_languages() in
    tools/build_wals_map.py) that are among the record's descendants, sorted; empty when
    the record has no descendants."""
    if not nodes[i]["children"]:
        return []
    found, todo = [], list(nodes[i]["children"])
    while todo:
        c = todo.pop()
        if c not in nodes:
            continue
        if c in condition_ids:
            found.append(c)
        todo.extend(nodes[c]["children"])
    return sorted(found)


def map_html(depth, i):
    # The same steps for every record, whatever its level (family, language, dialect): the
    # deepest points on its branches (its own point when it has none below), all drawn alike,
    # and the rest of its parent's points as sisters.
    n = nodes[i]
    main_ids = points_under[i]
    main = [coords[c] for c in main_ids]
    parent = n.get("parent")
    context_ids = []
    if parent in nodes:
        mine = set(main_ids) | {i}
        context_ids = [c for c in points_under[parent] if c not in mine]
    context = [coords[c] for c in context_ids]
    label = f"Map: location of {n['name']}"
    svg = map_svg(
        "../" * depth + "map/",
        main,
        context,
        None,
        label,
        main_ids=main_ids,
        context_ids=context_ids,
    )
    if not svg:
        return ""
    # The key: what each kind of point stands for, named by record (no kind labels).
    # dist/map-zoom.js moves it into the map box, so the map view shows it too.
    # data-points names the points of each entry; dist/map-zoom.js makes the entry a button
    # that steps through them.
    main_points = escape(".lmap-main circle, .lmap-self circle")
    ctx_points = escape(".lmap-ctx rect")
    key = []
    if main_ids == [i]:
        key.append(
            f'<li class="lmap-key-main notranslate" data-points="{main_points}">{escape(n["name"])}</li>'
        )
    elif main:
        key.append(
            f'<li class="lmap-key-main" data-points="{main_points}">Members of {escape(n["name"])}</li>'
        )
    if context:
        key.append(f'<li class="lmap-key-ctx" data-points="{ctx_points}">Sister languoids</li>')
    key_html = f'<ul class="lmap-key">{"".join(key)}</ul>' if key else ""
    # No caption under the map (owner, 2026-11-22): the sources are credited in the footer
    # and on the Sources page.
    return f'<figure class="lmap-figure">{svg}{key_html}</figure>'


# Credit for the data on every page: Glottolog and WALS (CC BY 4.0 requires it), the IANA
# registry and Unicode CLDR (tools/record_facts.py; sources in source-data/sources.json).
# One source per line (owner, 2026-11-24), then the contact line.
_NEW = 'target="_blank" rel="noopener noreferrer"'
CC_BY = "https://creativecommons.org/licenses/by/4.0/"


def _credit(what, name, url, license_name=None, license_url=None, cite=""):
    """One line of the credit: what the data is, its source, and the license it is used under.
    The citation sits in its own span, so ", used under" stays a text node dist/lang.js knows."""
    line = f'<li>{what} <a href="{url}" {_NEW}>{name}</a>'
    if cite:
        # A citation is data in English: kept left to right inside right-to-left pages.
        line += f' <span class="cite" dir="ltr">({cite})</span>'
    if license_name:
        line += f', used under <a href="{license_url}" {_NEW}>{license_name}</a>'
    return line + "</li>"


FOOTER = (
    '<footer class="credit"><ul class="credit-list">'
    + _credit(
        "Classification, names, endangerment and descriptions from",
        GLOTTOLOG,
        "https://glottolog.org/",
        "CC BY 4.0",
        CC_BY,
        "Hammarström, Forkel, Haspelmath &amp; Bank 2026, "
        f'<a href="https://doi.org/10.5281/zenodo.18840935" {_NEW}>doi:10.5281/zenodo.18840935</a>',
    )
    + _credit(
        "Language tags from",
        "IANA Language Subtag Registry",
        "https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry",
    )
    + _credit(
        "Scripts, speakers and official status from",
        CLDR,
        "https://cldr.unicode.org/",
        "Unicode License v3",
        "https://www.unicode.org/license.txt",
    )
    + _credit("Feature values from", "WALS Online", "https://wals.info/", "CC BY 4.0", CC_BY)
    + _credit("Phoneme inventories from", "PHOIBLE", "https://phoible.org/", "CC BY 4.0", CC_BY)
    # Share-alike and non-commercial data, named with their licenses (.claude/rules/license.md).
    + _credit(
        "Estimated speakers, scripts, endangerment and Wikidata items from",
        "LinguaMeta",
        "https://github.com/google-research/url-nlp/tree/main/linguameta",
        "CC BY-SA 4.0",
        "https://creativecommons.org/licenses/by-sa/4.0/",
    )
    + _credit(
        "Societies from",
        "D-PLACE",
        "https://d-place.org/",
        "CC BY-NC 4.0",
        "https://creativecommons.org/licenses/by-nc/4.0/",
    )
    + "</ul>"
    + contact_line("p")
    + "</footer>"
)


# Links to the three atlases. No generated page shows them any more (owner, 2026-11-07:
# Lang Log is one tree, not three domains); kept so the UI can be reused.
def domain_nav(up, current="language"):
    items = [
        ("language", up, "Language families"),
        ("sign", f"{up}signs-and-scripts.html?domain=sign", "Sign languages"),
        ("scripts", f"{up}signs-and-scripts.html?domain=scripts", "Writing systems"),
    ]
    return (
        '<nav class="domain-nav" aria-label="Atlas domains">'
        + "".join(
            f'<a href="{escape(h)}"'
            + (' aria-current="page"' if k == current else "")
            + f">{t}</a>"
            for k, h, t in items
        )
        + "</nav>"
    )


# Scripts at the end of every record page: the branch tree, the explorer above it (the map
# and the tree with the top page's conditions) and the Hugging Face models.
def page_scripts(up):
    return "".join(
        f'<script src="{up}{f}"></script>'
        for f in [
            "atlas-data.js",
            "lineage-paths.js",
            "hf-iso-map.js",
            "hf-models.js",
            "tree.js",
            "explore.js",
            "record-page.js",
        ]
    )


def page(depth, title, body):
    up = "../" * depth
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"{SECURITY_HEAD}"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}{TITLE_SUFFIX}</title>"
        + icon_links(up)
        + SITE_NAME_META
        + pwa_head(up)
        + f'<link rel="stylesheet" href="{up}style.css"><link rel="stylesheet" href="{up}signs-and-scripts.css"><link rel="stylesheet" href="{up}record.css"><link rel="stylesheet" href="{up}explore.css"><script src="{up}theme.js"></script><script src="{up}i18n.js"></script><script src="{up}lang.js"></script><script src="{up}map-zoom.js" defer></script></head>'
        f'<body class="variant-page"><header><div class="brand"><a class="home" href="{up}"><svg class="logo" role="img" aria-label="LANG LOG"><use href="{up}logo.svg#logo"/></svg></a> {by_yoshi()}</div></header>'
        f"<main>{body}</main>{FOOTER}{page_scripts(up)}</body></html>"
    )


def record_json(i):
    if i in extra:
        n = extra[i]
        return {
            "id": i,
            "name": n["name"],
            "level": n["level"],
            "iso": n.get("iso", ""),
            "category": n.get("category", ""),
            "path": path_of(i),
            "source": sources[n["source"]]["title"],
            "lineage": [
                {"id": a, "name": extra[a]["name"], "path": path_of(a)}
                for a in extra_lineage(i)[:-1]
            ],
            "children": [
                {
                    "id": e["child"],
                    "name": rec(e["child"])["name"],
                    "level": rec(e["child"])["level"],
                    "path": path_of(e["child"]),
                    "sample": e.get("sample", ""),
                }
                for e in by_source.get((n["source"], i), [])
            ],
            "placements": [e for e in unified["placements"].get(i, [])],
        }
    n = nodes[i]
    return {
        "id": i,
        "name": n["name"],
        "level": n["level"],
        "iso": n.get("iso", ""),
        "coordinates": (
            {"latitude": coords[i][1], "longitude": coords[i][0]} if i in coords else None
        ),
        "area": n.get("area", ""),
        "countries": n.get("countries", ""),
        "isolate": n.get("isolate", False),
        "path": path_of(i),
        "lineage": [
            {"id": a, "name": nodes[a]["name"], "path": path_of(a)} for a in lineage(i)[:-1]
        ],
        "children": [
            {"id": c, "name": nodes[c]["name"], "level": nodes[c]["level"], "path": path_of(c)}
            for c in n["children"]
        ],
        "langLog": {
            "parent": (
                {
                    "id": lang_log_parent[i],
                    "name": nodes[lang_log_parent[i]]["name"],
                    "path": path_of(lang_log_parent[i]),
                }
                if i in lang_log_parent
                else None
            ),
            "children": [
                {"id": c, "name": nodes[c]["name"], "path": path_of(c)}
                for c in lang_log_children.get(i, [])
            ],
        },
        "names": n.get("names", []),
        "nativeNames": n.get("nativeNames", []),
        "placements": [e for e in unified["placements"].get(i, [])],
        "source": f"{GLOTTOLOG} (CC BY 4.0)",
    }


def extra_lineage(i):
    out = []
    while i in extra:
        out.insert(0, i)
        i = extra[i].get("parent")
    return out


def source_page_body(sid):
    """Top of a source's tree: what the source is, and its top-level records."""
    src = sources[sid]
    body = (
        f'<nav class="lineage" aria-label="Classification according to {escape(src["title"])}">'
        '<ol class="lineage-path"><li><a href="../">Top</a></li></ol></nav>'
        f'<h1>{escape(src["title"])}</h1><div class="meta"><span>{"catalog" if src.get("kind") == "catalog" else "study tree"}</span>'
        + (f"<span>{escape(src['family'])}</span>" if src.get("family") else "")
        + f"<span>{escape(src.get('license', ''))}</span></div>"
    )
    if src.get("citation"):
        body += f"<p>{escape(src['citation'])}</p>"
    links = [ext_link(sid)]
    if src.get("dataset"):
        links.append(
            f'<a href="{escape(src["dataset"])}" target="_blank" rel="noopener noreferrer">Source tree &amp; data ↗</a>'
        )
    body += "<p>" + " · ".join(links) + "</p>"
    attached = sorted(
        {
            g
            for g, lst in unified["anchors"].items()
            if g in nodes
            for a in lst
            if a["source"] == sid
        },
        key=lambda g: nodes[g]["name"].lower(),
    )
    if attached:
        body += (
            '<section class="attached"><h2>Where Lang Log attaches this tree</h2><ul class="record-links">'
            + "".join(
                f'<li>{record_link(1, g)} <span class="muted">Glottolog</span></li>'
                for g in attached
            )
            + "</ul></section>"
        )
    return body


def write_page(i, body, title):
    target = OUT / path_of(i)
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(
        page(path_of(i).count("/") + 1, title, body), encoding="utf-8"
    )
    (target / "record.json").write_text(
        json.dumps(record_json(i), ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def write_source_pages():
    """One page per source-only record, under its source; returns the number written."""
    written = 0
    for i, n in extra.items():
        sid = n["source"]
        depth = path_of(i).count("/") + 1
        if i in study_root:
            body = source_page_body(sid) + group("Classification", children_html(depth, i))
        else:
            body = breadcrumb(depth, extra_lineage(i)[:-1], sid) + record_body(depth, i, sid)
        if i in study_root:  # a record page has these in its groups
            body += tree_html(depth, i, sid) + hf_html(n)
            body += '<p class="muted"><a href="record.json">This record as JSON</a></p>'
        write_page(i, body, sources[sid]["title"] if i in study_root else n["name"])
        written += 1
    # dist/wals/: the WALS catalog and its families.
    fams = sorted(
        (i for i, n in extra.items() if n["source"] == "wals" and not n.get("parent")),
        key=lambda i: extra[i]["name"].lower(),
    )
    target = OUT / SOURCE_SLUG["wals"]
    target.mkdir(parents=True, exist_ok=True)
    rows = "".join(f"<li>{record_link(1, f)}</li>" for f in fams)
    body = (
        source_page_body("wals")
        + f'<section class="members"><h2>Families · {len(fams)}</h2><ul class="record-links">{rows}</ul></section>'
    )
    (target / "index.html").write_text(page(1, sources["wals"]["title"], body), encoding="utf-8")
    return written


def main():
    top = {segment[r] for r in data["roots"]}
    src_top = set(SOURCE_SLUG.values())
    clash = sorted((top | src_top) & RESERVED) + sorted(top & src_top)
    if clash or len(src_top) != len(SOURCE_SLUG):
        sys.exit(
            f"Top-level slug(s) {clash} clash with each other or with names reserved in dist/; add a rule for them."
        )
    # Remove pages from an earlier run: each family and source directory, and directories no longer built.
    for name in top | src_top | OLD_DIRS:
        if (OUT / name).is_dir():
            shutil.rmtree(OUT / name)
    written = 0
    for i in nodes:
        p = path_of(i)
        depth = p.count("/") + 1
        target = OUT / p
        target.mkdir(parents=True, exist_ok=True)
        anc = lineage(i)[:-1]
        body = (
            breadcrumb(depth, anc) + lang_log_lineage(depth, i) + record_body(depth, i, "glottolog")
        )
        (target / "index.html").write_text(page(depth, nodes[i]["name"], body), encoding="utf-8")
        (target / "record.json").write_text(
            json.dumps(record_json(i), ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
        written += 1
    written_sources = write_source_pages()
    (OUT / "source-paths.json").write_text(
        json.dumps({i: path_of(i) + "/" for i in extra}, separators=(",", ":")), encoding="utf-8"
    )
    if "--paths" in sys.argv:  # for checking dist/lineage-paths.js against these rules
        (OUT / "paths.json").write_text(
            json.dumps({i: path_of(i) + "/" for i in nodes}), encoding="utf-8"
        )
    print(
        f"Wrote {written} Glottolog record pages and {written_sources} source-only record pages under dist/"
    )


if __name__ == "__main__":
    main()
