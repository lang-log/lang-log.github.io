"""Facts about a record beyond the tree, read from the sources that give them.

Each source is read by its own function, which takes only that source's files
(source-data/, listed in source-data/sources.json) and returns its values with
the source named on each, so a new release of one source changes only its own
values. tools/build_paths.py shows them on the record pages and
tools/build_languoids.py writes them into languoid.json
(schema/languoid.schema.json); both call facts().

- Glottolog (values.csv, codes.csv): endangerment and the most extensive
  description, by Glottocode.
- IANA Language Subtag Registry (iana/registry.json): the language tag, its
  scope, macrolanguage and retired tags, and the script a tag leaves out.
- Unicode CLDR (cldr/): scripts, the share of each country's population that
  speaks the language and its official status there, and plural categories.

- LinguaMeta (linguameta/linguameta.tsv, CC BY-SA 4.0): estimated speakers,
  scripts, an endangerment status, the ISO 639-2/B code and the Wikidata item.
- PHOIBLE (phoible/phoible.csv): phoneme inventories, by Glottocode.
- D-PLACE (dplace/societies.csv, CC BY-NC 4.0): the societies that speak the
  language, by Glottocode.

Values from share-alike or non-commercial sources keep their source on every
value, so they can be told apart and kept out of paid features (license.md).

The ISO 639-3 code tables themselves are not kept here: their terms allow no
redistribution of the code set (https://iso639-3.sil.org/code_tables/download_tables).
"""

import ast
import csv
import functools
import json

from locations import SOURCE_DATA

SRC = SOURCE_DATA


@functools.cache
def glottolog_values():
    """Glottocode -> {"endangerment": ..., "description": ...} from Glottolog's values."""
    with open(SRC / "codes.csv", encoding="utf-8", newline="") as f:
        names = {r["ID"]: r["Name"] for r in csv.DictReader(f)}
    out = {}
    citations = {}
    with open(SRC / "values.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            p = r["Parameter_ID"]
            if p == "aes":
                out.setdefault(r["Language_ID"], {})["endangerment"] = {
                    "value": names[r["Code_ID"]],
                    "source": "glottolog",
                }
            elif p == "med":
                out.setdefault(r["Language_ID"], {})["description"] = {
                    "value": names[r["Code_ID"]],
                    "reference_id": r["Source"],
                    "source": "glottolog",
                }
            elif p == "medovertime":
                # The citations of the descriptions over time, in the order of their ids in
                # Source ("<id>[<year>];..."); the most extensive one is cited from here.
                ids = [s.split("[")[0] for s in r["Source"].split(";")]
                citations[r["Language_ID"]] = dict(
                    zip(ids, ast.literal_eval(r["Value"]), strict=True)
                )
    for i, v in out.items():
        d = v.get("description")
        if d:
            ref = citations.get(i, {}).get(d.pop("reference_id"))
            if ref:
                d["reference"] = ref
    return out


@functools.cache
def iana_registry():
    """Language subtag -> its registry entry, and preferred tag -> the retired tags it replaced."""
    entries = json.loads((SRC / "iana" / "registry.json").read_text(encoding="utf-8"))
    languages = {e["Subtag"]: e for e in entries if e["Type"] == "language"}
    retired = {}
    for e in languages.values():
        if e.get("Deprecated") and e.get("Preferred-Value"):
            retired.setdefault(e["Preferred-Value"], []).append(e["Subtag"])
    return languages, retired


def iana(iso):
    """The registry's facts for an ISO 639-3 code: its tag and what the registry says of it."""
    languages, retired = iana_registry()
    short = {three: two for two, three in iso_map().items()}
    tag = short.get(iso, iso)
    e = languages.get(tag)
    if not e:
        return None
    return {
        "tag": tag,
        "scope": e.get("Scope", "individual"),
        "macrolanguage": e.get("Macrolanguage"),
        "replaced_by": e.get("Preferred-Value") if e.get("Deprecated") else None,
        "retired": sorted(retired.get(tag, [])),
        "script": e.get("Suppress-Script"),
        "source": "iana",
    }


@functools.cache
def iso_map():
    """ISO 639-1 -> ISO 639-3, as Glottolog publishes it (source-data/iso-map.json)."""
    return json.loads((SRC / "iso-map.json").read_text(encoding="utf-8"))


@functools.cache
def cldr_data():
    def read(name):
        return json.loads((SRC / "cldr" / name).read_text(encoding="utf-8"))["supplemental"]

    aliases = read("aliases.json")["metadata"]["alias"]["languageAlias"]
    languages = read("languageData.json")["languageData"]
    territories = read("territoryInfo.json")["territoryInfo"]
    plurals = read("plurals.json")["plurals-type-cardinal"]
    by_language = {}
    for country, t in territories.items():
        for code, p in t.get("languagePopulation", {}).items():
            by_language.setdefault(code.split("_")[0], {})[country] = {
                "country": country,
                "population_percent": float(p["_populationPercent"]),
                "official_status": p.get("_officialStatus"),
                "source": "cldr",
            }
    return aliases, languages, by_language, plurals


def cldr(iso):
    """CLDR's facts for an ISO 639-3 code. CLDR names a language by its shortest code (its
    "overlong" aliases: jpn is ja). CLDR's macrolanguage codes (zh for cmn) are not followed:
    their figures cover the whole macrolanguage, not the one language."""
    aliases, languages, by_language, plurals = cldr_data()
    a = aliases.get(iso, {})
    code = a["_replacement"] if a.get("_reason") == "overlong" else iso
    scripts = [
        {"script": s, "use": use, "source": "cldr"}
        for key, use in ((code, "main"), (code + "-alt-secondary", "other"))
        for s in languages.get(key, {}).get("_scripts", [])
    ]
    countries = sorted(
        by_language.get(code, {}).values(), key=lambda c: (-c["population_percent"], c["country"])
    )
    rules = plurals.get(code)
    plural = {"values": [k.rsplit("-", 1)[1] for k in rules], "source": "cldr"} if rules else None
    return {"scripts": scripts, "countries": countries, "plural_categories": plural}


@functools.cache
def linguameta_rows():
    """Glottocode and ISO 639-3 code -> the LinguaMeta overview row."""
    with open(SRC / "linguameta" / "linguameta.tsv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    by_glottocode = {r["glottocode"]: r for r in rows if r["glottocode"]}
    by_iso = {r["iso_639_3_code"]: r for r in rows if r["iso_639_3_code"]}
    return by_glottocode, by_iso


def linguameta(glottocode, iso):
    by_glottocode, by_iso = linguameta_rows()
    r = by_glottocode.get(glottocode) or by_iso.get(iso)
    if not r:
        return None
    return {
        "speakers": int(r["estimated_number_of_speakers"])
        if r["estimated_number_of_speakers"]
        else None,
        "scripts": [s.strip() for s in r["writing_systems"].split(",") if s.strip()],
        "endangerment": r["endangerment_status"] or None,
        "iso639_2b": r["iso_639_2b_code"] or None,
        "wikidata": r["wikidata_id"] or None,
        "source": "linguameta",
    }


@functools.cache
def phoible_inventories():
    """Glottocode -> PHOIBLE's inventories, each with its phonemes by class."""
    inventories = {}
    with open(SRC / "phoible" / "phoible.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            inv = inventories.setdefault(
                r["InventoryID"],
                {
                    "glottocode": r["Glottocode"],
                    "inventory": r["InventoryID"],
                    "contributor": r["Source"],
                    "consonant": [],
                    "vowel": [],
                    "tone": [],
                },
            )
            inv[r["SegmentClass"]].append(r["Phoneme"])
    out = {}
    for inv in inventories.values():
        g = inv.pop("glottocode")
        out.setdefault(g, []).append(
            {
                "inventory": inv["inventory"],
                "contributor": inv["contributor"],
                "consonants": inv["consonant"],
                "vowels": inv["vowel"],
                "tones": inv["tone"],
                "source": "phoible",
            }
        )
    for v in out.values():
        v.sort(key=lambda i: int(i["inventory"]))
    return out


@functools.cache
def dplace_societies():
    """Glottocode -> the D-PLACE societies whose language it is."""
    out = {}
    with open(SRC / "dplace" / "societies.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["Glottocode"]:
                out.setdefault(r["Glottocode"], []).append(
                    {
                        "society": r["ID"],
                        "name": r["Name"],
                        "region": r["region"] or None,
                        "focal_year": int(r["main_focal_year"])
                        if r["main_focal_year"].lstrip("-").isdigit()
                        else None,
                        "source": "dplace",
                    }
                )
    return out


def facts(glottocode, iso):
    """Every fact above for one record, with the same keys for every record."""
    g = glottolog_values().get(glottocode, {}) if glottocode else {}
    c = cldr(iso) if iso else {"scripts": [], "countries": [], "plural_categories": None}
    registry = iana(iso) if iso else None
    scripts = c["scripts"]
    if (
        registry
        and registry["script"]
        and not any(s["script"] == registry["script"] for s in scripts)
    ):
        scripts = [{"script": registry["script"], "use": "main", "source": "iana"}] + scripts
    meta = linguameta(glottocode, iso)
    if meta:
        known = {x["script"] for x in scripts}
        scripts = scripts + [
            {"script": x, "use": "main", "source": "linguameta"}
            for x in meta["scripts"]
            if x not in known
        ]
    return {
        "registry": registry,
        "scripts": scripts,
        "linguameta": meta,
        "phonemes": phoible_inventories().get(glottocode, []) if glottocode else [],
        "societies": dplace_societies().get(glottocode, []) if glottocode else [],
        "speakers_by_country": c["countries"],
        "plural_categories": c["plural_categories"],
        "endangerment": g.get("endangerment"),
        "description": g.get("description"),
    }
