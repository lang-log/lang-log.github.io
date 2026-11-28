"""The top page's conditions beyond the WALS features (owner, 2026-11-22: every
condition the current data can give, from the list in the thread "フィルタの絞り込み
条件の候補を列挙する"). tools/build_wals_map.py calls features() and writes what it
returns into dist/data/features/ next to the WALS features.

Each feature is one entry of features.json and one file f/<id>.json with one value
per language of languages.json, in its order. A feature's "type" says how
dist/components/explorer/explorer.js reads that file:

  (none)    a category: a value number (0 = no data) or, with "multi", a list of
            value numbers (empty = no data); "values" lists the numbers, their
            names and counts. "names" says how the names are shown: "data" (names
            from a source, never translated), "region" (ISO 3166 codes, which the
            page names in its own language), or left out (interface text,
            translated with i18n/<code>.yaml).
  number    a number, or null for no data; "min" and "max" are the range of the
            data, "wrap" marks a longitude (a range from east to west across 180).
  text      no file: the condition matches the language's name in languages.json.
  relative  a number the page works out for a language the visitor chooses:
            "shared" (WALS values in common, from wals.json) or "km" (distance,
            from the lat and lon features).

Kinds of record (isolate, dialect, family) are never conditions
(.claude/rules/interface-text.md).
"""

import collections
import csv
import json
import re

from locations import DIST, SOURCE_DATA

# Groups of the feature menu, by what a feature is about (owner, 2026-11-22: no source
# names such as WALS or Glottolog in the menu; sources are credited in the footer and on
# the Sources page).
PLACE, CLASSIFICATION, NAMES, FEATURE_DATA = (
    "Place",
    "Classification",
    "Names and codes",
    "Feature data",
)
# The group of each feature below; features() sets it last, so the code of each feature
# says only where its data comes from.
GROUP_OF = {
    PLACE: "macroarea country countries lat lon point distance",
    CLASSIFICATION: "top group depth size dialects grouping medium constructed"
    " study nstudies debate stage power",
    NAMES: "name names native provider iso",
    FEATURE_DATA: "inwals sample wfamily wsubfamily wgenus wcountry wcount wareas"
    " wdisagree wref wshared nsources",
}
GROUP = ""  # replaced by the feature's group from GROUP_OF
YES, NO = 1, 2
# Decimal places kept for latitudes and longitudes (about 1 km).
COORD_PLACES = 2
# A WALS reference is written "Author-Year[pages]"; the pages are left out.
PAGES = re.compile(r"\[[^\]]*\]")


def yes_no(got):
    return [YES if x else NO for x in got]


def category(fid, name, area, per_lang, names=None, order=None, multi=False):
    """A category feature from one value (or, with multi, a list of values) per
    language, written as names; None or [] is no data. Values are numbered in
    order (a list of names) or else by name."""
    seen = set()
    for v in per_lang:
        seen.update(v if multi else ([v] if v is not None else []))
    keys = [k for k in order if k in seen] if order else sorted(seen, key=str.casefold)
    num = {k: i + 1 for i, k in enumerate(keys)}
    if multi:
        data = [sorted(num[k] for k in set(v)) for v in per_lang]
    else:
        data = [num[v] if v is not None else 0 for v in per_lang]
    counts = collections.Counter(n for v in data for n in (v if multi else [v]) if n)
    entry = {
        "id": fid,
        "name": name,
        "area": area,
        "languages": sum(1 for v in data if v),
        "source": "langlog",
        "values": [{"n": num[k], "name": k, "count": counts[num[k]]} for k in keys],
    }
    if multi:
        entry["multi"] = True
    if names:
        entry["names"] = names
    return entry, data


def yes_no_feature(fid, name, area, got):
    data = yes_no(got)
    return {
        "id": fid,
        "name": name,
        "area": area,
        "languages": len(data),
        "source": "langlog",
        "values": [
            {"n": YES, "name": "Yes", "count": data.count(YES)},
            {"n": NO, "name": "No", "count": data.count(NO)},
        ],
    }, data


def number(fid, name, area, data, wrap=False):
    got = [v for v in data if v is not None]
    entry = {
        "id": fid,
        "name": name,
        "area": area,
        "languages": len(got),
        "source": "langlog",
        "type": "number",
        "min": min(got),
        "max": max(got),
    }
    if wrap:
        entry["wrap"] = True
    return entry, data


def features(langs, nodes, wals_lects, wals_values, area_of):
    """[(entry, data or None)] for every condition below, in the order of the menu.

    langs: the rows of Glottolog's languages.csv in languages.json's order.
    nodes: dist/data.json's records (the Lang Log tree).
    wals_lects: {language index: [rows of wals.csv]} for the WALS lects of each.
    wals_values: the rows of WALS values.csv with "i", the language index.
    area_of: WALS parameter id -> its area name.
    """
    unified = json.loads((DIST / "integrated.json").read_text(encoding="utf-8"))
    ids = [r["ID"] for r in langs]
    node = [nodes.get(i, {}) for i in ids]
    out = []

    def below(gid):
        todo, got = [gid], []
        while todo:
            n = todo.pop()
            got.append(n)
            todo.extend(nodes.get(n, {}).get("children", []))
        return got

    def ancestors(gid):
        got, p = [], nodes.get(gid, {}).get("parent")
        while p:
            got.append(p)
            p = nodes[p].get("parent")
        return got

    # From Glottolog
    out.append(
        category(
            "macroarea",
            "Macroarea",
            GROUP,
            [r["Macroarea"].split(";") if r["Macroarea"] else [] for r in langs],
            multi=True,
        )
    )
    countries = [r["Countries"].split(";") if r["Countries"] else [] for r in langs]
    out.append(category("country", "Country", GROUP, countries, names="region", multi=True))
    out.append(
        number("countries", "Number of countries", GROUP, [len(c) or None for c in countries])
    )
    top = [nodes[n["root"]]["name"] if n.get("root") in nodes else None for n in node]
    out.append(category("top", "Top-level languoid", GROUP, top, names="data"))

    # A higher record is named with its top-level languoid, as names repeat ("Northern").
    def label(gid):
        n, r = nodes[gid], nodes[nodes[gid]["root"]]
        return n["name"] if gid == n["root"] else f"{n['name']} · {r['name']}"

    out.append(
        category(
            "group",
            "Belongs to",
            GROUP,
            [[label(a) for a in ancestors(i)] for i in ids],
            names="data",
            multi=True,
        )
    )
    media = [n.get("modality") for n in node]
    out.append(category("medium", "Medium", GROUP, media, order=["spoken", "signed", "written"]))
    out.append(
        yes_no_feature(
            "constructed", "Constructed language", GROUP, [n.get("constructed") for n in node]
        )
    )
    out.append(
        category(
            "grouping",
            "Type",
            GROUP,
            [n.get("category") for n in node],
            names="data",
        )
    )
    out.append(
        category(
            "iso",
            "ISO 639-3 code",
            GROUP,
            [
                "Own code"
                if r["ISO639P3code"]
                else "Closest code only"
                if r["Closest_ISO369P3code"]
                else "None"
                for r in langs
            ],
            order=["Own code", "Closest code only", "None"],
        )
    )
    out.append(
        yes_no_feature("point", "Point on the map", GROUP, [bool(r["Latitude"]) for r in langs])
    )
    out.append(number("dialects", "Number of dialects", GROUP, [len(below(i)) - 1 for i in ids]))
    out.append(number("depth", "Depth in the tree", GROUP, [len(ancestors(i)) for i in ids]))
    languages_in = collections.Counter(
        n["root"] for n in nodes.values() if n["level"] == "language"
    )
    out.append(
        number(
            "size",
            "Languages in its top-level languoid",
            GROUP,
            [languages_in[n["root"]] if n.get("root") else None for n in node],
        )
    )

    def coord(r, key):
        return round(float(r[key]), COORD_PLACES) if r[key] else None

    out.append(number("lat", "Latitude", GROUP, [coord(r, "Latitude") for r in langs]))
    out.append(number("lon", "Longitude", GROUP, [coord(r, "Longitude") for r in langs], wrap=True))
    out.append(number("names", "Number of names", GROUP, [len(n.get("names", [])) for n in node]))
    out.append(
        yes_no_feature(
            "native", "Name in the language itself", GROUP, [n.get("nativeNames") for n in node]
        )
    )
    out.append(
        category(
            "provider",
            "Name source",
            GROUP,
            [[x["provider"] for x in n.get("names", [])] for n in node],
            names="data",
            multi=True,
        )
    )
    out.append(
        (
            {"id": "name", "name": "Name", "area": GROUP, "source": "langlog", "type": "text"},
            None,
        )
    )

    # From WALS
    lects = [wals_lects.get(i, []) for i in range(len(langs))]
    out.append(yes_no_feature("inwals", "Has feature data", GROUP, lects))
    out.append(
        category(
            "sample",
            "Feature sample",
            GROUP,
            [
                [
                    s
                    for k, s in (
                        ("Samples_100", "100-language sample"),
                        ("Samples_200", "200-language sample"),
                    )
                    if any(w[k] == "true" for w in ls)
                ]
                for ls in lects
            ],
            order=["100-language sample", "200-language sample"],
            multi=True,
        )
    )
    for fid, name, key in (
        ("wfamily", "Family in the feature data", "Family"),
        ("wsubfamily", "Subfamily in the feature data", "Subfamily"),
        ("wgenus", "Genus", "Genus"),
    ):
        out.append(
            category(
                fid,
                name,
                GROUP,
                [[w[key] for w in ls if w[key]] for ls in lects],
                names="data",
                multi=True,
            )
        )
    out.append(
        category(
            "wcountry",
            "Country in the feature data",
            GROUP,
            [[c for w in ls for c in w["Country_ID"].split() if c] for ls in lects],
            names="region",
            multi=True,
        )
    )
    per_lang = collections.defaultdict(lambda: collections.defaultdict(set))
    refs = collections.defaultdict(set)
    for v in wals_values:
        per_lang[v["i"]][v["Parameter_ID"]].add(v["Value"])
        for s in v["Source"].split(";"):
            s = PAGES.sub("", s).strip()
            if s:
                refs[v["i"]].add(s)
    n_lang = range(len(langs))
    out.append(
        number(
            "wcount",
            "Number of features with data",
            GROUP,
            [len(per_lang[i]) or None for i in n_lang],
        )
    )
    out.append(
        category(
            "wareas",
            "Feature areas with data",
            GROUP,
            [sorted({area_of[p] for p in per_lang[i]}) for i in n_lang],
            multi=True,
        )
    )
    out.append(
        yes_no_feature(
            "wdisagree",
            "Varieties disagree on a feature",
            GROUP,
            [any(len(s) > 1 for s in per_lang[i].values()) for i in n_lang],
        )
    )
    out.append(
        category(
            "wref",
            "Reference for feature data",
            GROUP,
            [sorted(refs[i]) for i in n_lang],
            names="data",
            multi=True,
        )
    )
    out.append(
        (
            {
                "id": "wshared",
                "name": "Features shared with a language",
                "area": GROUP,
                "source": "langlog",
                "type": "relative",
                "measure": "shared",
            },
            None,
        )
    )

    # From Lang Log's own data
    study_index = unified["studyIndex"]
    title = {k: s["title"] for k, s in unified["sources"].items()}
    studies = [sorted({title[s] for d in below(i) for s in study_index.get(d, [])}) for i in ids]
    out.append(category("study", "Research tree", GROUP, studies, names="data", multi=True))
    out.append(number("nstudies", "Number of research trees", GROUP, [len(s) for s in studies]))
    debate_title = {d["id"]: d["title"] for d in unified["debates"]}
    out.append(
        category(
            "debate",
            "Debate",
            GROUP,
            [
                sorted(
                    {
                        debate_title[x]
                        for a in [i, *ancestors(i)]
                        for x in unified["debateIndex"].get(a, [])
                    }
                )
                for i in ids
            ],
            names="data",
            multi=True,
        )
    )
    parents = json.loads(
        (SOURCE_DATA / "lang-log" / "classification.json").read_text(encoding="utf-8")
    )["parents"]
    stage_of = {p["parent"] for p in parents.values()}
    out.append(
        category(
            "stage",
            "Historical stage",
            GROUP,
            [
                [
                    s
                    for s, on in (
                        ("Has an earlier stage", i in parents),
                        ("Is an earlier stage", i in stage_of),
                    )
                    if on
                ]
                for i in ids
            ],
            order=["Has an earlier stage", "Is an earlier stage"],
            multi=True,
        )
    )
    out.append(
        number(
            "nsources",
            "Number of sources",
            GROUP,
            [1 + bool(lects[k]) + len(studies[k]) for k in n_lang],
        )
    )
    power = {}
    for r in csv.DictReader(
        (SOURCE_DATA / "signs-and-scripts" / "power-languages.csv").open(encoding="utf-8")
    ):
        if r["Glottocode"] and r["SubGroup"]:
            power.setdefault(r["Glottocode"], set()).add(r["SubGroup"])
    out.append(
        category(
            "power",
            "Sign language group",
            GROUP,
            [sorted({g for d in below(i) for g in power.get(d, ())}) for i in ids],
            names="data",
            multi=True,
        )
    )
    out.append(
        (
            {
                "id": "distance",
                "name": "Distance from a language (km)",
                "area": GROUP,
                "source": "langlog",
                "type": "relative",
                "measure": "km",
            },
            None,
        )
    )
    group = {fid: g for g, ids in GROUP_OF.items() for fid in ids.split()}
    for entry, _ in out:
        entry["area"] = group[entry["id"]]
    return out
