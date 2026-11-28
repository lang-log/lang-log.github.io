"""Data for the top page's map view and its conditions (dist/components/explorer/explorer.js).

Two steps:

  python3 tools/build_wals_map.py --fetch
      Downloads the WALS Online v2020.4 tables (CLDF, CC BY 4.0,
      https://github.com/cldf-datasets/wals) unchanged into source-data/wals/,
      the one committed copy of WALS (listed in source-data/sources.json; also
      read by tools/build_languoids.py). Run by hand only when moving to a new
      WALS release; it needs network access.

  python3 tools/build_wals_map.py
      Reads those tables, source-data/languages.csv (Glottolog),
      source-data/wals.csv (WALS languages and their Glottocodes),
      dist/data.json and dist/integrated.json (tools/finish_unified.py) and
      writes dist/data/features/ (not committed; built in CI):
        languages.json  one entry per Glottolog language: Glottocode, name,
                        family, first WALS code (or ""), the point in the
                        map's SVG units (Web Mercator, as dist/map/land.svg;
                        see tools/components/map.py; null without coordinates) and
                        the top-level record it belongs to (its "root" in
                        dist/data.json), which the top-page list uses
        features.json   every feature: id, name, area, source ("wals" or
                        "langlog") and its values with their counts
        f/<ID>.json     one feature's values: a list with one entry per
                        language in languages.json (0 = no data)
        f/<ID>.values.json  the values of a feature with more than
                        LONG_VALUES of them (features.json has null)
        wals.json       every language's WALS values in one table

Besides the WALS features, Lang Log's own evidence gives two features that
every language has a value for (LANGLOG_FEATURES): whether the language (or
one of its dialects) is in a conflict between study trees, and whether it is
placed in a research tree. They take the place of the evidence filter of the
former whole tree on the top page (owner, 2026-11-08). The other conditions
(Glottolog, WALS and Lang Log data) come from tools/condition_features.py.

Points are Glottolog's representative coordinates, not the area where a
language is spoken.
"""

import csv
import hashlib
import json
import sys
import urllib.request

from condition_features import features as condition_features
from locations import DIST, ROOT
from components.map import project

SRC = ROOT / "source-data" / "wals"
OUT = ROOT / "dist" / "data" / "features"
VERSION = "v2020.4"
BASE = f"https://raw.githubusercontent.com/cldf-datasets/wals/{VERSION}/cldf/"

# Chapter areas of WALS Online (https://wals.info/chapter), by chapter number.
AREAS = [
    (1, 19, "Phonology"),
    (20, 29, "Morphology"),
    (30, 57, "Nominal categories"),
    (58, 64, "Nominal syntax"),
    (65, 80, "Verbal categories"),
    (81, 97, "Word order"),
    (98, 121, "Simple clauses"),
    (122, 128, "Complex sentences"),
    (129, 138, "Lexicon"),
    (139, 140, "Sign languages"),
    (141, 142, "Other"),
    (143, 144, "Word order"),
]


# Lang Log's own features: (id, name, index in dist/integrated.json). A language
# has value 1 ("Yes") when it or one of its dialects is a key of the index, else 2.
LANGLOG_FEATURES = [
    ("conflicts", "Conflicting study clades", "conflictIndex"),
    ("studies", "Research trees", "studyIndex"),
]
LANGLOG_AREA = "Lang Log"
YES, NO = 1, 2
# A feature with more values than this keeps them in f/<ID>.values.json, which the page
# loads only when the feature is chosen, so features.json stays small.
LONG_VALUES = 60


def area(chapter):
    for lo, hi, name in AREAS:
        if lo <= chapter <= hi:
            return name
    return "Other"


def fetch():
    SRC.mkdir(parents=True, exist_ok=True)
    for name in ("values.csv", "parameters.csv", "codes.csv", "chapters.csv", "areas.csv"):
        raw = urllib.request.urlopen(BASE + name, timeout=120).read()
        (SRC / name).write_bytes(raw)
        print(
            f"Wrote {(SRC / name).relative_to(ROOT)} from {VERSION} (SHA-256 {hashlib.sha256(raw).hexdigest()[:16]})"
        )


def glottolog():
    """The rows of Glottolog's languages.csv."""
    return list(csv.DictReader((ROOT / "source-data" / "languages.csv").open(encoding="utf-8")))


def condition_languages(glotto):
    """The languages the conditions choose from, one row each in languages.json, in its
    order: every Glottolog language, with or without a point on the map.
    tools/build_home.py counts them for the top page's first count line."""
    return sorted((r for r in glotto if r["Level"] == "language"), key=lambda r: r["ID"])


def build():
    """The languages are every Glottolog language (level "language"), so the conditions
    start from all languages, not only those in WALS; the map draws those with
    coordinates. Each WALS language is
    attached to its Glottolog language: a WALS lect mapped to a dialect counts for the
    dialect's language; one mapped to a family, or to nothing, is left out. When
    several WALS lects fall on one language, the first in WALS code order with a value
    for a feature gives that value."""
    glotto = glottolog()
    by_id = {r["ID"]: r for r in glotto}
    langs = condition_languages(glotto)
    index = {r["ID"]: i for i, r in enumerate(langs)}

    wals_to = {}  # WALS code -> index in langs
    wals_codes = {}  # index -> first WALS code
    wals_lects = {}  # index -> rows of wals.csv
    for w in sorted(
        csv.DictReader((ROOT / "source-data" / "wals.csv").open(encoding="utf-8")),
        key=lambda r: r["ID"],
    ):
        g = by_id.get(w["Glottocode"])
        if not g:
            continue
        if g["Level"] == "dialect":
            g = by_id.get(g["Language_ID"])
        i = index.get(g["ID"]) if g else None
        if i is None:
            continue
        wals_to[w["ID"]] = i
        wals_codes.setdefault(i, w["ID"])
        wals_lects.setdefault(i, []).append(w)

    params = list(csv.DictReader((SRC / "parameters.csv").open(encoding="utf-8")))
    codes = {}
    for c in csv.DictReader((SRC / "codes.csv").open(encoding="utf-8")):
        codes.setdefault(c["Parameter_ID"], []).append({"n": int(c["Number"]), "name": c["Name"]})
    values = {}
    attached = []  # the WALS values of the languages, each with "i", its index
    for v in sorted(
        csv.DictReader((SRC / "values.csv").open(encoding="utf-8")), key=lambda r: r["Language_ID"]
    ):
        i = wals_to.get(v["Language_ID"])
        if i is not None:
            values.setdefault(v["Parameter_ID"], {}).setdefault(i, int(v["Value"]))
            attached.append({**v, "i": i})

    OUT.joinpath("f").mkdir(parents=True, exist_ok=True)
    nodes = json.loads((DIST / "data.json").read_text(encoding="utf-8"))["nodes"]
    rows = []
    for i, r in enumerate(langs):
        # A language without coordinates has no point (x and y null).
        x, y = (
            (round(c, 1) for c in project(float(r["Longitude"]), float(r["Latitude"])))
            if r["Latitude"] and r["Longitude"]
            else (None, None)
        )
        fam = by_id.get(r["Family_ID"], {}).get("Name", "") if r["Family_ID"] else ""
        root = nodes[r["ID"]]["root"] if r["ID"] in nodes else ""
        rows.append([r["ID"], r["Name"], fam, wals_codes.get(i, ""), x, y, root])
    write(
        OUT / "languages.json",
        {"fields": ["glottocode", "name", "family", "wals", "x", "y", "root"], "rows": rows},
    )

    features = []
    for p in params:
        pid = p["ID"]
        got = values.get(pid, {})
        if not got:
            continue
        counts = {}
        for n in got.values():
            counts[n] = counts.get(n, 0) + 1
        vals = sorted(codes.get(pid, []), key=lambda c: c["n"])
        for c in vals:
            c["count"] = counts.get(c["n"], 0)
        features.append(
            {
                "id": pid,
                "name": p["Name"],
                "area": area(int(p["Chapter_ID"])),
                "languages": len(got),
                "source": "wals",
                "values": vals,
            }
        )
        write(OUT / "f" / f"{pid}.json", [got.get(i, 0) for i in range(len(langs))])
    # Every language's WALS values in one table, for the condition "WALS values shared
    # with a language" (dist/components/explorer/explorer.js): {"features": [ids], "rows": {index: [values]}}.
    ids = [f["id"] for f in features]
    write(
        OUT / "wals.json",
        {
            "features": ids,
            "rows": {
                i: [values[f].get(i, 0) for f in ids]
                for i in sorted({i for got in values.values() for i in got})
            },
        },
    )
    features += langlog_features(langs, nodes)
    area_of = {p["ID"]: area(int(p["Chapter_ID"])) for p in params}
    for entry, data in condition_features(langs, nodes, wals_lects, attached, area_of):
        if data is not None:
            write(OUT / "f" / f"{entry['id']}.json", data)
        if len(entry.get("values", [])) > LONG_VALUES:
            write(OUT / "f" / f"{entry['id']}.values.json", entry["values"])
            entry["values"] = None
        features.append(entry)
    write(OUT / "features.json", {"version": VERSION, "features": features})
    print(
        f"Wrote dist/data/features/: {len(langs)} Glottolog languages, {len(wals_codes)} with WALS data, {len(features)} features"
    )


def self_and_below(i, nodes):
    """i and every record below it in Glottolog (a language's dialects)."""
    out, todo = [], [i]
    while todo:
        n = todo.pop()
        out.append(n)
        todo.extend(nodes.get(n, {}).get("children", []))
    return out


def langlog_features(langs, nodes):
    """LANGLOG_FEATURES for every language in langs; writes their f/<ID>.json."""
    unified = json.loads((DIST / "integrated.json").read_text(encoding="utf-8"))
    out = []
    for fid, name, key in LANGLOG_FEATURES:
        index = unified[key]
        got = [
            YES if any(d in index for d in self_and_below(r["ID"], nodes)) else NO for r in langs
        ]
        write(OUT / "f" / f"{fid}.json", got)
        out.append(
            {
                "id": fid,
                "name": name,
                "area": LANGLOG_AREA,
                "languages": len(got),
                "source": "langlog",
                "values": [
                    {"n": YES, "name": "Yes", "count": got.count(YES)},
                    {"n": NO, "name": "No", "count": got.count(NO)},
                ],
            }
        )
    return out


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    fetch() if "--fetch" in sys.argv[1:] else build()
