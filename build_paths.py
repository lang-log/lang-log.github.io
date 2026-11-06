"""Write one static page and one JSON file per Glottolog record, at a URL
that follows the classification: dist/<family>/<subgroup>/.../<language>/
(served as https://lang-log.github.io/<family>/.../<language>/).

Run after prepare_static.py (it reads dist/data.json and dist/integrated.json).

- Each path segment is an ASCII slug of the record name. When two siblings
  share a slug, both get "-<glottocode>" appended, so a URL never depends on
  the order of the data.
- Historical stages listed in source-data/historical-stages.json (for
  example Old English) have no directory of their own. They are a section of
  the modern language's page, reached as <modern path>/#<anchor> (for
  example .../english/#old). Their children live under
  <modern path>/<anchor>/<child>/.
- dist/families/ lists the top-level families and isolates.
- A top-level slug must not equal a name already used at the top of dist/
  (RESERVED); the build stops if one does.
- The pages need no JavaScript. dist/app.js and dist/variant-detail.js use the
  same rules (see pathOf in those files) to link here.
"""
from pathlib import Path
from html import escape
import csv
import json
import re
import shutil
import sys
import unicodedata

from languoid_map import map_svg

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
OUT = DIST
FAMILIES = DIST / "families"
# Top-level names in dist/ that a family slug must not take.
RESERVED = {"families", "map"}
TITLE_SUFFIX = " · Lang Log by yoshi"

data = json.loads((DIST / "data.json").read_text(encoding="utf-8"))
unified = json.loads((DIST / "integrated.json").read_text(encoding="utf-8"))
stages = json.loads((ROOT / "source-data" / "historical-stages.json").read_text(encoding="utf-8"))["stages"]
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


# Children per parent, with stages moved under their modern language.
stage_of = {s: v for s, v in stages.items() if s in nodes and v["modern"] in nodes}
segment = {}
segment.update(segments_for(data["roots"]))
for n in nodes.values():
    kids = [c for c in n["children"] if c not in stage_of]
    segment.update(segments_for(kids))

path_cache = {}

# Glottolog's representative point of each record, as (longitude, latitude).
coords = {}
with open(ROOT / "source-data" / "languages.csv", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        if row["Latitude"] and row["Longitude"] and row["ID"] in nodes:
            coords[row["ID"]] = (float(row["Longitude"]), float(row["Latitude"]))


def _points_under():
    """For a family: the languages below it; for a language: its dialects."""
    langs, dials = {}, {}

    def walk(i):
        la, di = [], []
        for c in nodes[i]["children"]:
            if c not in nodes:
                continue
            cl, cd = walk(c)
            la += cl
            di += cd
            lvl = nodes[c]["level"]
            if c in coords and lvl == "language":
                la.append(c)
            elif c in coords and lvl == "dialect":
                di.append(c)
        langs[i], dials[i] = la, di
        return la, di

    for r in data["roots"]:
        walk(r)
    for i in nodes:  # records not reached from a root
        if i not in langs:
            walk(i)
    return {i: (dials[i] if nodes[i]["level"] != "family" else langs[i]) for i in nodes}


points_under = _points_under()


def path_of(i):
    """URL path below the atlas root, without leading or trailing slash; stages end in #anchor."""
    if i in path_cache:
        return path_cache[i]
    if i in stage_of:
        p = path_of(stage_of[i]["modern"]) + "/#" + stage_of[i]["anchor"]
    else:
        parent = nodes[i].get("parent")
        if parent in stage_of:
            # Child of a stage: <modern>/<anchor>/<child>
            st = stage_of[parent]
            p = path_of(st["modern"]) + "/" + st["anchor"] + "/" + segment[i]
        else:
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
    p = path_of(target_id)
    if "/#" in p:
        d, a = p.split("/#")
        return "../" * from_dir_depth + d + "/#" + a
    return "../" * from_dir_depth + p + "/"


def source_link(sid):
    s = sources.get(sid)
    if not s:
        return escape(sid)
    return f'<a href="{escape(s["url"])}" target="_blank" rel="noopener">{escape(s["title"])}</a>'


def names_html(n):
    own = sorted({r["text"] for r in n.get("nativeNames", [])})
    seen = {}
    for r in n.get("names", []):
        if r.get("placeholder"):
            continue
        seen.setdefault((r["text"], r.get("lang", "")), set()).add(r.get("provider", ""))
    out = "<h3>Name in this language</h3>"
    out += (f'<p dir="auto">{" / ".join(escape(x) for x in own)}</p>' if own
            else '<p class="muted">Not recorded in the imported sources. No name inferred.</p>')
    if not seen:  # an empty toggle opens onto nothing, so say so in plain text
        return out + '<p class="muted">No other names or spellings recorded.</p>'
    out += f"<details><summary>Recorded names and spellings · {len(seen)}</summary><ul class=\"name-list\">"
    out += "".join(f'<li dir="auto">{escape(t)} <span class="muted">{escape(l or "tag unspecified")} · {escape(" · ".join(sorted(p)))}</span></li>'
                   for (t, l), p in sorted(seen.items()))
    return out + "</ul></details>"


def placements_html(i):
    rows = []
    seen = set()
    for e in unified["placements"].get(i, []):
        if e["source"] == "glottolog":
            continue
        key = (e["source"], e["parent"])
        if key in seen:
            continue
        seen.add(key)
        parent = nodes.get(e["parent"]) or extra.get(e["parent"]) or {"name": e["parent"]}
        rows.append(f'<li>According to {source_link(e["source"])}: under {escape(parent["name"])}'
                    + (f' <span class="muted">(sample: {escape(e["sample"])})</span>' if e.get("sample") else "") + "</li>")
    if not rows:
        return ""
    return f"<h3>Other classifications</h3><ul>{''.join(rows)}</ul>"


def breadcrumb(depth, ids):
    if not ids:
        return ""
    items = "".join(f'<li><a href="{escape(href(depth, a))}">{escape(nodes[a]["name"])}</a></li>' for a in ids)
    return f'<nav class="lineage" aria-label="Classification according to Glottolog"><span class="lineage-source">Glottolog</span><ol class="lineage-path">{items}</ol></nav>'


def children_html(depth, i):
    kids = [c for c in nodes[i]["children"] if c not in stage_of]
    if not kids:
        return ""
    kids.sort(key=lambda c: nodes[c]["name"].lower())
    rows = "".join(f'<li><a href="{escape(href(depth, c))}">{escape(nodes[c]["name"])}</a> <span class="muted">{escape(nodes[c]["level"])}</span></li>' for c in kids)
    # A section gets the rule and spacing that set it apart from the names above.
    return f'<section class="members"><h2>Members · {len(kids)}</h2><ul class="record-links">{rows}</ul></section>'


def meta_html(n):
    parts = [n["level"], n["id"]]
    if n.get("iso"):
        parts.append("ISO 639-3: " + n["iso"])
    if n.get("area"):
        parts.append(n["area"])
    return '<div class="meta">' + "".join(f"<span>{escape(p)}</span>" for p in parts) + "</div>"


def record_body(depth, i, heading="h1"):
    n = nodes[i]
    body = f'<{heading}>{escape(n["name"])}</{heading}>{meta_html(n)}'
    body += (f'<p><a href="{"../" * depth}#{escape(i)}">Open in the atlas</a> · '
             f'<a href="https://glottolog.org/resource/languoid/id/{escape(i)}" target="_blank" rel="noopener">Glottolog record ↗</a> · '
             f'<a href="{"../" * depth}variant-detail.html?domain=language&amp;id={escape(i)}">Full source detail</a></p>')
    if heading == "h1":
        body += map_html(depth, i)
    return body + names_html(n) + placements_html(i)


def map_html(depth, i):
    n = nodes[i]
    family = n["level"] == "family"
    own = None if family else coords.get(i)
    # Many dialects carry their language's own point; those add nothing to show.
    main = [coords[c] for c in points_under[i] if coords[c] != own]
    parent = n.get("parent")
    context = []
    if parent in nodes:
        mine = set(points_under[i]) | {i}
        context = [coords[c] for c in points_under[parent] if c not in mine]
    kind = "languages" if family else ("dialects" if n["level"] == "language" else "")
    if family:
        label = f"Map: {len(main)} languages of {n['name']}"
    else:
        label = f"Map: location of {n['name']}" + (f" and its {len(main)} {kind}" if main else "")
    svg = map_svg("../" * depth + "map/", main, context, own, label)
    if not svg:
        return ""
    notes = []
    if family:
        total = sum(1 for c in languages_under_all(i))
        missing = total - len(main)
        notes.append(f"{len(main)} languages shown" + (f"; {missing} have no coordinates in Glottolog" if missing else "") + ".")
    if context:
        notes.append("Faint points: other members of " + escape(nodes[parent]["name"]) + ".")
    legend = " ".join(notes)
    return (f'<figure class="lmap-figure">{svg}<figcaption>{legend} '
            "Each point is the one representative location Glottolog gives for a record, not the area where it is spoken. "
            'Points: Glottolog 5.3 (CC BY 4.0). Land: <a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">Natural Earth</a> (public domain). '
            "Projection: Equal Earth.</figcaption></figure>")


def languages_under_all(i):
    """Every language below a family, with or without coordinates."""
    out = []
    stack = list(nodes[i]["children"])
    while stack:
        c = stack.pop()
        if c not in nodes:
            continue
        if nodes[c]["level"] == "language":
            out.append(c)
        stack.extend(nodes[c]["children"])
    return out


# Credit for the Glottolog data, which CC BY 4.0 requires on every page that uses it.
FOOTER = ('<footer class="credit"><p>Classification and names from '
          '<a href="https://glottolog.org/" target="_blank" rel="noopener">Glottolog 5.3</a> '
          '(Hammarström, Forkel, Haspelmath &amp; Bank 2026, '
          '<a href="https://doi.org/10.5281/zenodo.18840935" target="_blank" rel="noopener">doi:10.5281/zenodo.18840935</a>), '
          'used under <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a>.</p></footer>')


def page(depth, title, body):
    up = "../" * depth
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{escape(title)}{TITLE_SUFFIX}</title>"
            f"<link rel=\"stylesheet\" href=\"{up}style.css\"><link rel=\"stylesheet\" href=\"{up}visual-atlas.css\"><link rel=\"stylesheet\" href=\"{up}variant-detail.css\"></head>"
            f"<body class=\"variant-page\"><header><a class=\"brand\" href=\"{up}\"><span class=\"mark\">✳</span> LANG LOG <span class=\"by\">by yoshi</span></a><a href=\"{up}families/\">All families</a></header>"
            f"<main>{body}</main>{FOOTER}</body></html>")


def record_json(i):
    n = nodes[i]
    return {
        "id": i, "name": n["name"], "level": n["level"], "iso": n.get("iso", ""),
        "coordinates": ({"latitude": coords[i][1], "longitude": coords[i][0]} if i in coords else None),
        "area": n.get("area", ""), "countries": n.get("countries", ""), "isolate": n.get("isolate", False),
        "path": path_of(i),
        "lineage": [{"id": a, "name": nodes[a]["name"], "path": path_of(a)} for a in lineage(i)[:-1]],
        "children": [{"id": c, "name": nodes[c]["name"], "level": nodes[c]["level"], "path": path_of(c)} for c in n["children"]],
        "stages": [{"id": s, "name": nodes[s]["name"], "anchor": v["anchor"]} for s, v in stage_of.items() if v["modern"] == i],
        "names": n.get("names", []), "nativeNames": n.get("nativeNames", []),
        "placements": [e for e in unified["placements"].get(i, [])],
        "source": "Glottolog 5.3 (CC BY 4.0)",
    }


def main():
    top = {segment[r] for r in data["roots"]}
    clash = sorted(top & RESERVED)
    if clash:
        sys.exit(f"Top-level slug(s) {clash} clash with names reserved in dist/; add a rule for them.")
    # Remove pages from an earlier run: each family directory and families/.
    for name in top | {"families"}:
        if (OUT / name).is_dir():
            shutil.rmtree(OUT / name)
    written = 0
    stages_by_modern = {}
    for s, v in stage_of.items():
        stages_by_modern.setdefault(v["modern"], []).append(s)
    for i in nodes:
        if i in stage_of:
            continue
        p = path_of(i)
        depth = p.count("/") + 1
        target = OUT / p
        target.mkdir(parents=True, exist_ok=True)
        anc = lineage(i)[:-1]
        body = breadcrumb(depth, anc) + record_body(depth, i)
        for s in sorted(stages_by_modern.get(i, []), key=lambda s: nodes[s]["name"]):
            st = stage_of[s]
            body += f'<section id="{escape(st["anchor"])}" class="stage"><p class="eyebrow">Historical stage · #{escape(st["anchor"])}</p>'
            body += record_body(depth, s, "h2")
            body += breadcrumb(depth, lineage(s)[:-1]).replace("aria-label=\"Classification according to Glottolog\"", "aria-label=\"Position in Glottolog\"")
            body += '<p class="muted">Position of this stage in the Glottolog tree. Glottolog does not record which modern language it is a stage of; that link is curated in this atlas.</p>'
            kids = sorted(nodes[s]["children"], key=lambda c: nodes[c]["name"].lower())
            if kids:
                body += "<ul class=\"record-links\">" + "".join(f'<li><a href="{escape(href(depth, c))}">{escape(nodes[c]["name"])}</a></li>' for c in kids) + "</ul>"
            body += "</section>"
        body += children_html(depth, i)
        body += f'<p class="muted"><a href="record.json">This record as JSON</a></p>'
        (target / "index.html").write_text(page(depth, nodes[i]["name"], body), encoding="utf-8")
        (target / "record.json").write_text(json.dumps(record_json(i), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        written += 1
    # A stage's anchor directory (e.g. .../korean/middle/) points back to the section.
    for s, v in stage_of.items():
        if nodes[s]["children"]:
            d = OUT / path_of(v["modern"]) / v["anchor"]
            d.mkdir(parents=True, exist_ok=True)
            if not (d / "index.html").exists():
                depth = path_of(v["modern"]).count("/") + 2
                (d / "index.html").write_text(page(depth, nodes[s]["name"], f'<h1>{escape(nodes[s]["name"])}</h1><p><a href="../#{escape(v["anchor"])}">See {escape(nodes[s]["name"])} on the {escape(nodes[v["modern"]]["name"])} page</a></p>'), encoding="utf-8")
    roots = sorted(data["roots"], key=lambda r: nodes[r]["name"].lower())
    rows = "".join(f'<li><a href="../{escape(path_of(r))}/">{escape(nodes[r]["name"])}</a> <span class="muted">{escape("isolate" if nodes[r].get("isolate") else nodes[r]["level"])}</span></li>' for r in roots)
    FAMILIES.mkdir(parents=True, exist_ok=True)
    (FAMILIES / "index.html").write_text(page(1, "All families", f"<h1>All families and isolates · {len(roots)}</h1><p class=\"muted\">Top-level entries of Glottolog 5.3. Each record has its own page at a URL that follows its classification.</p><ul class=\"record-links\">{rows}</ul>"), encoding="utf-8")
    (OUT / "stages.json").write_text(json.dumps({k: {"modern": v["modern"], "anchor": v["anchor"]} for k, v in stage_of.items()}), encoding="utf-8")
    if "--paths" in sys.argv:  # for checking dist/lineage-paths.js against these rules
        (OUT / "paths.json").write_text(json.dumps({i: (path_of(i) if "/#" in path_of(i) else path_of(i) + "/") for i in nodes}), encoding="utf-8")
    print(f"Wrote {written} record pages under dist/")


main()
