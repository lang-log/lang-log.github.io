import csv
import json
import re
import collections
import hashlib
import pathlib

from not_languoids import NOT_LANGUOIDS, lift

src = pathlib.Path("source-data")
out = pathlib.Path("dist")
rows = list(csv.DictReader(open(src / "languages.csv")))
nodes = {
    r["ID"]: {
        "id": r["ID"],
        "name": r["Name"],
        "level": r["Level"],
        "area": r["Macroarea"],
        "iso": r["ISO639P3code"],
        "countries": r["Countries"],
        "isolate": r["Is_Isolate"] == "true",
        "parent": None,
        "children": [],
    }
    for r in rows
}
parents = {}


def edge(child, parent):
    if child in parents:
        assert parents[child] == parent, (child, parent, parents[child])
    parents[child] = parent


for line in open(src / "classification.nex"):
    if " = [&R] " not in line:
        continue
    ts = re.findall(r"[a-z0-9]{4}[0-9]{4}|[(),;]", line.split(" = [&R] ")[1])
    pos = 0

    # Defined and called within one loop iteration, so the loop variables it reads
    # are always the current ones (the noqa: B023 marks below).
    def parse():
        global pos
        children = []
        if ts[pos] == "(":  # noqa: B023
            pos += 1
            while True:
                children.append(parse())
                if ts[pos] == ")":  # noqa: B023
                    pos += 1
                    break
                assert ts[pos] == ","  # noqa: B023
                pos += 1
        name = ts[pos]  # noqa: B023
        pos += 1
        for ch in children:
            edge(ch, name)
        return name

    parse()
for path in re.findall(r"\(tree/([^)]*)/md.ini\)", open(src / "dialects.md").read()):
    ids = path.split("/")
    for a, b in zip(ids, ids[1:], strict=False):
        edge(b, a)
# Glottolog's top-level groupings (Sign Language, Pidgin, Bookkeeping ...) give
# each record its category; read it from the full tree before the groups that
# are not languoids are left out (tools/not_languoids.py).
catnames = {
    "Sign Language",
    "Unclassifiable",
    "Pidgin",
    "Unattested",
    "Artificial Language",
    "Speech Register",
    "Mixed Language",
    "Bookkeeping",
}


def top(id):
    while parents.get(id):
        id = parents[id]
    return id


category = {
    id: nodes[top(id)]["name"] if nodes[top(id)]["name"] in catnames else "Spoken genealogy"
    for id in nodes
}
unparented = [
    id
    for id in nodes
    if not parents.get(id) and next(r for r in rows if r["ID"] == id)["Family_ID"]
]
parents, grouping = lift(parents, "glottolog")
for id in NOT_LANGUOIDS["glottolog"]:
    del nodes[id]
roots = []
for id, n in nodes.items():
    n["parent"] = parents.get(id)
    if n["parent"]:
        nodes[n["parent"]]["children"].append(id)
    else:
        roots.append(id)
for n in nodes.values():
    n["children"].sort(key=lambda x: nodes[x]["name"].casefold())
print("roots", len(roots))
print([(nodes[x]["name"], nodes[x]["level"]) for x in roots if nodes[x]["level"] == "family"])
missing = unparented
print("Missing parents", missing)
assert not missing
for n in nodes.values():
    seen = set()
    p = n
    while p["parent"]:
        assert p["id"] not in seen
        seen.add(p["id"])
        p = nodes[p["parent"]]
    n["root"] = p["id"]
for n in nodes.values():
    n["category"] = category[n["id"]]


def count(id):
    n = nodes[id]
    n["size"] = 1 + sum(count(c) for c in n["children"])
    return n["size"]


for id in roots:
    count(id)
wrows = list(csv.DictReader(open(src / "wals.csv")))
wn = {}
wroots = []
matches = collections.defaultdict(list)
for r in wrows:
    id = r["ID"]
    parent = r["Parent_ID"] or None
    wn[id] = {
        "id": id,
        "name": r["Name"],
        "parent": parent,
        "children": [],
        "level": "language"
        if not id.startswith(("family-", "subfamily-", "genus-"))
        else id.split("-")[0],
        "glottocode": r["Glottocode"],
        "family": r["Family"],
        "genus": r["Genus"],
        "area": r["Macroarea"],
        "iso": r["ISO639P3code"],
        "source": r["Source"],
    }
    if r["Glottocode"] in nodes:
        matches[r["Glottocode"]].append(id)
wparents, _ = lift({id: n["parent"] for id, n in wn.items()}, "wals")
for id in NOT_LANGUOIDS["wals"]:
    del wn[id]
for id, n in wn.items():
    n["parent"] = wparents[id]
    if n["parent"]:
        wn[n["parent"]]["children"].append(id)
    else:
        wroots.append(id)
for n in wn.values():
    n["children"].sort(key=lambda x: wn[x]["name"].casefold())
for n in nodes.values():
    n["wals"] = matches[n["id"]]
stats = {
    "total": len(nodes),
    "levels": dict(collections.Counter(n["level"] for n in nodes.values())),
    "roots": len(roots),
    "genealogicalFamilies": sum(
        nodes[x]["level"] == "family" and nodes[x]["category"] == "Spoken genealogy" for x in roots
    ),
    "isolates": sum(n["isolate"] for n in nodes.values()),
    "walsNodes": len(wn),
    "walsMatched": len([x for x in matches.values() if x]),
    "categories": dict(collections.Counter(n["category"] for n in nodes.values())),
}
data = {
    "nodes": nodes,
    "roots": sorted(
        roots, key=lambda x: (nodes[x]["category"] != "Spoken genealogy", -nodes[x]["size"])
    ),
    # Records Glottolog lists under a group that is not a languoid: {id: group name}.
    "groupings": grouping,
    "wals": wn,
    "walsRoots": sorted(wroots, key=lambda x: wn[x]["name"]),
    "stats": stats,
    "retrieved": "2026-10-12",
    "glottologVersion": "5.3",
}
(out / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
print(json.dumps(stats, indent=2))

# The start of dist/provenance.json: the sources and a hash of each file read
# here. tools/enrich.py and tools/finish_unified.py add the rest.
provenance = {
    "retrieved": "2026-10-12",
    "sources": [
        {
            "name": "Glottolog 5.3",
            "authors": "Hammarström, Harald; Forkel, Robert; Haspelmath, Martin; Bank, Sebastian",
            "year": 2026,
            "doi": "10.5281/zenodo.18840935",
            "data": "https://github.com/glottolog/glottolog-cldf/tree/v5.3",
            "classification": "https://github.com/glottolog/glottolog/tree/v5.3",
            "license": "CC BY 4.0",
        },
        {
            "name": "WALS Online CLDF",
            "authors": "Dryer, Matthew S. & Haspelmath, Martin (eds.)",
            "year": 2013,
            "data": "https://github.com/cldf-datasets/wals",
            "version": "default-branch file snapshot retrieved 2026-10-12; file hash below",
            "license": "CC BY 4.0",
        },
    ],
    "files": {
        name: {
            "sha256": hashlib.sha256((src / name).read_bytes()).hexdigest(),
            "bytes": (src / name).stat().st_size,
        }
        for name in ["classification.nex", "languages.csv", "dialects.md", "wals.csv"]
    },
    "method": "Complete Glottolog languoid CSV; direct-parent edges from Glottolog v5.3 NEXUS plus all 27 dialect indexes. Separate WALS hierarchy. Exact Glottocode links only. No synthetic genealogical edges.",
    # tools/finish_unified.py writes the final list.
    "limitations": [],
}
(out / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2))
