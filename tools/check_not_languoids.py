"""Fail when a group that is not a languoid is back in the tree or the pages.

The groups are listed in source-data/lang-log/not-languoids.json (tools/not_languoids.py).
Run by tools/build_site.sh after the pages and languoid.json files are written.
"""

import json
import sys

from locations import DIST
from not_languoids import NOT_LANGUOIDS


def load(name):
    return json.loads((DIST / name).read_text(encoding="utf-8"))


def main():
    glottolog = set(NOT_LANGUOIDS["glottolog"])
    # Ids as the other files write them: WALS groups are "wals:<id>" outside data.json.
    wals = set(NOT_LANGUOIDS["wals"])
    every = glottolog | wals | {"wals:" + i for i in wals}
    problems = []
    data = load("data.json")
    for i, n in data["nodes"].items():
        if i in glottolog or n["parent"] in glottolog:
            problems.append(f"data.json: {i}")
    problems += [f"data.json roots: {i}" for i in data["roots"] if i in glottolog]
    for i, n in data["wals"].items():
        if i in wals or n["parent"] in wals:
            problems.append(f"data.json wals: {i}")
    unified = load("integrated.json")
    problems += [f"integrated.json: {i}" for i in unified["extraNodes"] if i in every]
    problems += [
        f"integrated.json assertion: {a['parent']} > {a['child']}"
        for a in unified["assertions"]
        if a.get("parent") in every or a.get("child") in every
    ]
    visual = load("signs-and-scripts.json")
    problems += [f"signs-and-scripts.json: {i}" for i in visual["nodes"] if i in every]
    problems += [
        f"signs-and-scripts.json assertion: {a['parent']} > {a['child']}"
        for a in visual["assertions"]
        if a["parent"] in every or a["child"] in every
    ]
    for f in DIST.rglob("languoid.json"):
        n = json.loads(f.read_text(encoding="utf-8"))
        if n["id"] in every or any(c["parent"] in every for c in n["classification"].values()):
            problems.append(f"{f.relative_to(DIST)}")
    if problems:
        print(
            "Groups that are not languoids are in the tree (source-data/lang-log/not-languoids.json):"
        )
        print("\n".join(problems[:20]))
        sys.exit(1)
    print(f"no group that is not a languoid in the tree ({len(every)} ids checked)")


if __name__ == "__main__":
    main()
