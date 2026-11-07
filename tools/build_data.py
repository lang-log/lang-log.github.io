import csv
import json
import re
import collections
import pathlib

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
missing = [
    n["id"]
    for n in nodes.values()
    if not n["parent"] and next(r for r in rows if r["ID"] == n["id"])["Family_ID"]
]
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
for n in nodes.values():
    rn = nodes[n["root"]]["name"]
    n["category"] = rn if rn in catnames else "Spoken genealogy"


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
for id, n in wn.items():
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
    "wals": wn,
    "walsRoots": sorted(wroots, key=lambda x: wn[x]["name"]),
    "stats": stats,
    "retrieved": "2026-10-12",
    "glottologVersion": "5.3",
}
(out / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
print(json.dumps(stats, indent=2))
