import json
import pathlib
import xml.etree.ElementTree as E
import gzip
import collections

p = pathlib.Path("dist")
data = json.load(open(p / "data.json"))
u = json.load(open(p / "integrated.json"))
nodes = data["nodes"] | u["extraNodes"]
u["sources"]["hartmann_and_walkden2024"]["url"] = "https://doi.org/10.16995/glossa.10598"
u["sources"]["hartmann_and_walkden2024"]["interpretationNote"] = (
    "A study of phylogenetic signal in syntactic data. Its global tree is not treated here as evidence for one universal language family."
)
u["debates"] = [
    {
        "id": "transeurasian",
        "title": "Transeurasian relationship",
        "appliesTo": ["japo1237", "kore1284", "mong1329", "tung1282", "turk1311"],
        "status": "Disputed genealogical proposal; no consensus implied",
        "positions": [
            {
                "author": "Robbeets et al. (2021)",
                "claim": "Under the Transeurasian hypothesis, Japonic, Koreanic, Tungusic, Mongolic and Turkic are branches of one proposed genealogical group.",
                "url": "https://doi.org/10.1038/s41586-021-04108-8",
                "publication": "Nature article",
                "stance": "proposal",
            },
            {
                "author": "Tian et al. (2022)",
                "claim": "This critique argues that the linguistic, genetic and archaeological analyses do not provide conclusive evidence for that family or its proposed farming dispersal. This is rejection of the evidence, not a demonstrated alternative superfamily.",
                "url": "https://doi.org/10.1101/2022.06.09.495471",
                "publication": "bioRxiv preprint, version 1",
                "stance": "critique",
            },
            {
                "author": "Robbeets et al. (2022)",
                "claim": "The response revises datasets and approaches while defending the proposed relationship and the triangulation argument.",
                "url": "https://doi.org/10.1101/2022.10.05.510045",
                "publication": "bioRxiv preprint, version 1",
                "stance": "response",
            },
        ],
        "note": "This is a manually curated paper-level debate. Its full proposed topology has not been imported; the five family labels are not a reconstruction of its internal branching.",
    }
]
u["debateIndex"] = {id: ["transeurasian"] for id in u["debates"][0]["appliesTo"]}
# Identify records with additional source evidence and propagate study availability to backbone ancestors.
study_index = collections.defaultdict(set)
for id, ps in u["placements"].items():
    for e in ps:
        if e["source"] not in ["glottolog", "wals"]:
            cur = id
            while cur in data["nodes"]:
                study_index[cur].add(e["source"])
                cur = data["nodes"][cur]["parent"]
u["studyIndex"] = {id: sorted(ss) for id, ss in study_index.items()}
u["stats"] = {
    "canonicalRecords": len(nodes),
    "glottologRecords": len(data["nodes"]),
    "additionalRecords": len(u["extraNodes"]),
    "summaryTrees": len(u["studies"]),
    "assertions": len(u["assertions"]),
    "topologicalConflicts": len(u["conflicts"]),
    "recordsWithConflicts": len(u["conflictIndex"]),
    "sameLanguageLabels": data["stats"]["recordsWithNativeNames"],
}
(p / "integrated.json").write_text(json.dumps(u, ensure_ascii=False, separators=(",", ":")))
# Flat nodes plus source-conditioned assertions encode the multi-parent graph without inventing a consensus tree.
root = E.Element(
    "language-atlas",
    {
        "schema-version": "3",
        "retrieved": "2026-10-12",
        "representation": "source-conditioned-graph",
    },
)
E.SubElement(root, "method").text = u["method"]
ss = E.SubElement(root, "sources")
for id, s in u["sources"].items():
    el = E.SubElement(ss, "source", {"id": id, "kind": s["kind"], "url": s["url"]})
    for k in [
        "title",
        "citation",
        "paperTitle",
        "family",
        "license",
        "dataset",
        "interpretationNote",
    ]:
        if k in s:
            E.SubElement(el, k).text = str(s[k])
ns = E.SubElement(root, "nodes")
for id, n in nodes.items():
    el = E.SubElement(ns, "node", {"id": id, "name": n["name"], "level": n["level"]})
    na = E.SubElement(
        el,
        "names",
        {"same-language-status": "recorded" if n.get("nativeNames") else "not-recorded"},
    )
    native = {r["record"] for r in n.get("nativeNames", [])}
    for r in n.get("names", []):
        E.SubElement(
            na,
            "name",
            {
                "provider": r["provider"],
                "language-tag": r["lang"],
                "source-record": r["record"],
                "same-language": str(r["record"] in native).lower(),
                "placeholder": str(bool(r.get("placeholder"))).lower(),
            },
        ).text = r["text"]
es = E.SubElement(root, "assertions")
for e in u["assertions"]:
    E.SubElement(es, "placement", {k: str(v) for k, v in e.items() if v is not None})
cs = E.SubElement(root, "incompatible-summary-clades")
for c in u["conflicts"]:
    E.SubElement(
        cs,
        "conflict",
        {
            "source-a": c["a"],
            "source-b": c["b"],
            "clade-a": c["cladeA"],
            "clade-b": c["cladeB"],
            "witness": " ".join(c["witness"]),
            "shared-tips": str(c["sharedTips"]),
        },
    )
bs = E.SubElement(root, "paper-debates")
for d in u["debates"]:
    el = E.SubElement(
        bs,
        "debate",
        {
            "id": d["id"],
            "title": d["title"],
            "applies-to": " ".join(d["appliesTo"]),
            "status": d["status"],
        },
    )
    for r in d["positions"]:
        E.SubElement(el, "position", {k: v for k, v in r.items() if k != "claim"}).text = r["claim"]
E.ElementTree(root).write(p / "language-families.xml", encoding="utf-8", xml_declaration=True)
# Outline export: shared identity is retained via node-id and source attributes on each occurrence.
childmap = collections.defaultdict(list)
for e in u["assertions"]:
    if e["parent"]:
        childmap[(e["source"], e["parent"])].append(e)
op = E.Element("opml", {"version": "2.0"})
E.SubElement(E.SubElement(op, "head"), "title").text = "Lang Log — source-conditioned hypotheses"
body = E.SubElement(op, "body")


def outline(id, parent, sid="glottolog", path=None):
    path = set() if path is None else path
    if (sid, id) in path:
        return
    n = nodes[id]
    label = n["name"]
    native = list(dict.fromkeys(r["text"] for r in n.get("nativeNames", [])))
    if native:
        label += " · " + " / ".join(native)
    el = E.SubElement(parent, "outline", {"text": label, "node-id": id, "source": sid})
    newpath = path | {(sid, id)}
    ps = u["placements"].get(id, [])
    if len({e["source"] for e in ps}) > 1:
        al = E.SubElement(el, "outline", {"text": "Conditional placements"})
        seen = set()
        for e in ps:
            k = (e["source"], e["parent"], e.get("sample", ""))
            if k in seen:
                continue
            seen.add(k)
            E.SubElement(
                al,
                "outline",
                {
                    "text": "According to "
                    + u["sources"][e["source"]]["title"]
                    + ": "
                    + nodes[e["parent"]]["name"],
                    "url": u["sources"][e["source"]]["url"],
                    "node-ref": e["parent"],
                },
            )
    for debate in u["debates"]:
        if id in debate["appliesTo"] and sid == "glottolog":
            de = E.SubElement(el, "outline", {"text": debate["title"] + " — " + debate["status"]})
            for pos in debate["positions"]:
                E.SubElement(
                    de,
                    "outline",
                    {
                        "text": pos["author"] + ": " + pos["claim"],
                        "url": pos["url"],
                        "publication": pos["publication"],
                    },
                )
    for e in childmap.get((sid, id), []):
        outline(e["child"], el, sid, newpath)
    if sid == "glottolog":
        for a in u["anchors"].get(id, []):
            group = E.SubElement(
                el,
                "outline",
                {
                    "text": "If following "
                    + u["sources"][a["source"]]["title"]
                    + " — sampled classification",
                    "url": u["sources"][a["source"]]["url"],
                    "relation": "display-attachment-not-ancestry",
                },
            )
            outline(a["root"], group, a["source"], newpath)


for id in data["roots"]:
    outline(id, body)
un = E.SubElement(
    body,
    "outline",
    {"text": "Cross-family and otherwise unattached source trees", "relation": "navigation-only"},
)
for a in u["anchors"].get("__unplaced__", []):
    outline(
        a["root"],
        E.SubElement(
            un,
            "outline",
            {"text": u["sources"][a["source"]]["title"], "url": u["sources"][a["source"]]["url"]},
        ),
        a["source"],
    )
E.ElementTree(op).write(p / "language-families.opml", encoding="utf-8", xml_declaration=True)
for f in ["language-families.xml", "language-families.opml"]:
    raw = (p / f).read_bytes()
    if len(raw) >= 25 * 1024 * 1024:
        with gzip.open(p / (f + ".gz"), "wb") as g:
            g.write(raw)
    print(f, len(raw))
prov = json.load(open(p / "provenance.json"))
prov["integrated_classifications"] = {
    "method": u["method"],
    "phlorest": u["catalogDiscovery"],
    "stats": u["stats"],
    "source_files": u["hashes"],
    "coverage": u["coverage"],
}
prov["limitations"] = [
    "No claim to include every language or every published classification worldwide.",
    "All 30 Phlorest catalogued dataset summary trees were imported; posterior tree samples were not imported.",
    "Entire Glottolog 5.3 node inventory and WALS classification snapshot retained. Underlying catalog bibliographies and all regional monographs are not fully ingested.",
    "Exact Glottocode identity only. Unmatched samples remain separate. Multiple samples of one Glottocode are preserved as source edge labels and excluded from automatic common-tip conflict detection.",
    "Computed topological incompatibility is not a judgment of scientific validity.",
    "Explicit paper-level debate currently curated for Transeurasian only; other debates remain unreviewed.",
    "Most languages lack a same-language label in the imported names dataset.",
]
(p / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2))
print(u["stats"])
