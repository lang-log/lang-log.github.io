import json
import re
import collections
import xml.etree.ElementTree as ET
from pathlib import Path

D = Path("dist")
x = json.loads((D / "signs-and-scripts.json").read_text())
n = x["nodes"]
e = x["assertions"]
b = json.loads((D / "data.json").read_text())["nodes"]
expected = {i for i, v in b.items() if v["category"] == "Sign Language"}
assert len(expected) == 344 and expected <= n.keys()
for i in expected:
    assert n[i]["aliases"] == b[i]["names"]
    assert n[i]["nativeNames"] == b[i]["nativeNames"]
    p = b[i]["parent"]
    if p:
        assert any(a["parent"] == p and a["child"] == i and a["source"] == "glottolog" for a in e)
iso = {
    r.split(";")[0]
    for r in Path("source-data/signs-and-scripts/iso15924.txt").read_text().splitlines()
    if r and not r.startswith("#")
}
assert iso <= n.keys() and len(iso) == 226
for a in e:
    assert a["parent"] in n and a["child"] in n and a["source"] in x["sources"]
for note in x["notes"]:
    assert set(note["nodes"]) <= n.keys() and set(note["sources"]) <= x["sources"].keys()
assert [len(t["tips"]) for t in x["studies"]] == [4, 15, 15]
assert len(set(i for t in x["studies"] for i in t["tips"])) == 19
assert all(len(set(t["tips"])) == len(t["tips"]) for t in x["studies"])
assert sum(a["kind"] == "manual-alphabet metadata subgroup" for a in e) == 76
assert any(a["parent"] == "Phlv" and a["child"] == "Avst" for a in e)
assert not any(a["parent"] == "Phlp" and a["child"] == "Avst" for a in e)
assert len({a["source"] for a in e if a["child"] == "Brah"}) == 2
out = collections.defaultdict(list)
for a in e:
    out[a["parent"]].append(a["child"])
seen = set()
active = set()


def visit(i):
    assert i not in active, ("cycle", i)
    if i in seen:
        return
    active.add(i)
    for j in out[i]:
        visit(j)
    active.remove(i)
    seen.add(i)


for i in n:
    visit(i)


# XML is lossless including uncertainty and source metadata.
def decode(el):
    t = el.get("type")
    if t == "object":
        return {c.get("name"): decode(c) for c in el}
    if t == "array":
        return [decode(c) for c in el]
    if t == "null":
        return None
    if t == "boolean":
        return el.text == "True"
    if t == "number":
        return json.loads(el.text)
    return el.text or ""


assert decode(ET.parse(D / "signs-and-scripts.xml").getroot()) == x
refs = {
    v.get("recordId")
    for v in ET.parse(D / "signs-and-scripts.opml").iter("outline")
    if v.get("recordId")
}
assert refs == set(n), set(n) - refs
assert len(x["usage"]) == 1001 and all(
    u["script"] in n and u["source"] == "cldr" for u in x["usage"]
)
assert all(not re.search(r"[<>]", i) for i in n)
print(
    "PASS: full snapshot coverage, aliases, sample mapping, source references, acyclic graph, competing Brahmi origins, lossless XML round-trip, complete OPML reachability and separate CLDR usage."
)
print(json.dumps(x["counts"], indent=2))
