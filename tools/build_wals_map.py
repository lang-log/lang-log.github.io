"""Data for the WALS feature map (dist/wals-map.html).

Two steps:

  python3 tools/build_wals_map.py --fetch
      Downloads the feature values of WALS Online v2020.4 (CLDF, CC BY 4.0,
      https://github.com/cldf-datasets/wals) and writes the three small tables
      under source-data/wals-features/, which are committed. Run by hand only
      when moving to a new WALS release; it needs network access.

  python3 tools/build_wals_map.py
      Reads those tables and source-data/wals.csv (the language coordinates)
      and writes dist/wals/ (not committed; built in CI):
        languages.json  one entry per WALS language with a point: code, name,
                        family, genus, Glottocode and the point in the map's
                        SVG units (Equal Earth, central meridian 0, as
                        dist/map/land.svg; see languoid_map.py)
        features.json   every feature: id, name, area and its values with
                        their counts
        f/<ID>.json     one feature's values: a list with one number per
                        language in languages.json (0 = no data)

Points are WALS's representative coordinates, not the area where a language
is spoken.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import urllib.request

from languoid_map import project

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-data" / "wals-features"
OUT = ROOT / "dist" / "wals"
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


def area(chapter):
    for lo, hi, name in AREAS:
        if lo <= chapter <= hi:
            return name
    return "Other"


def fetch():
    SRC.mkdir(parents=True, exist_ok=True)
    tables = {
        "parameters.csv": ("ID", "Name", "Chapter_ID"),
        "codes.csv": ("ID", "Parameter_ID", "Name", "Number"),
        "values.csv": ("Language_ID", "Parameter_ID", "Value"),
    }
    for name, cols in tables.items():
        raw = urllib.request.urlopen(BASE + name, timeout=120).read()
        rows = csv.DictReader(io.StringIO(raw.decode("utf-8")))
        out = SRC / name
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cols)
            for r in rows:
                w.writerow([r[c] for c in cols])
        print(f"Wrote {out.relative_to(ROOT)} from {VERSION} (source SHA-256 {hashlib.sha256(raw).hexdigest()[:16]})")


def build():
    langs = []
    for r in csv.DictReader((ROOT / "source-data" / "wals.csv").open(encoding="utf-8")):
        if r["Latitude"] and r["Longitude"]:
            langs.append(r)
    langs.sort(key=lambda r: r["ID"])
    index = {r["ID"]: i for i, r in enumerate(langs)}
    names = {r["ID"]: r["Name"] for r in csv.DictReader((ROOT / "source-data" / "wals.csv").open(encoding="utf-8"))}

    params = list(csv.DictReader((SRC / "parameters.csv").open(encoding="utf-8")))
    codes = {}
    for c in csv.DictReader((SRC / "codes.csv").open(encoding="utf-8")):
        codes.setdefault(c["Parameter_ID"], []).append({"n": int(c["Number"]), "name": c["Name"]})
    values = {}
    for v in csv.DictReader((SRC / "values.csv").open(encoding="utf-8")):
        i = index.get(v["Language_ID"])
        if i is not None:
            values.setdefault(v["Parameter_ID"], {})[i] = int(v["Value"])

    OUT.joinpath("f").mkdir(parents=True, exist_ok=True)
    out_langs = []
    for r in langs:
        x, y = project(float(r["Longitude"]), float(r["Latitude"]))
        parent = r["Parent_ID"]
        genus = names.get(parent, "")
        family = r["Family"]
        out_langs.append([r["ID"], r["Name"], family, genus, r["Glottocode"], round(x, 1), round(y, 1)])
    write(OUT / "languages.json", {"fields": ["id", "name", "family", "genus", "glottocode", "x", "y"], "rows": out_langs})

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
        features.append({"id": pid, "name": p["Name"], "area": area(int(p["Chapter_ID"])),
                         "languages": len(got), "values": vals})
        write(OUT / "f" / f"{pid}.json", [got.get(i, 0) for i in range(len(langs))])
    write(OUT / "features.json", {"version": VERSION, "features": features})
    print(f"Wrote dist/wals/: {len(langs)} languages, {len(features)} features")


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    fetch() if "--fetch" in sys.argv[1:] else build()
