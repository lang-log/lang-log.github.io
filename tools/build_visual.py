"""Build source-conditioned sign-language and writing-system graphs. No synthetic universal ancestor."""

import csv, json, re, hashlib, collections, xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser

P = Path("source-data/signs-and-scripts")
D = Path("dist")
B = json.loads((D / "data.json").read_text())["nodes"]
N = {}
E = []
S = {}
notes = []
usage = []


def src(i, title, url, kind, **kw):
    S[i] = dict(id=i, title=title, url=url, kind=kind, **kw)


def node(i, name, domain, kind, **kw):
    N[i] = dict(id=i, name=name, domain=domain, kind=kind, aliases=[], nativeNames=[], **kw)
    return i


def edge(p, c, s, kind="historical descent", status="reported", **kw):
    assert p in N and c in N, (p, c)
    E.append(dict(parent=p, child=c, source=s, kind=kind, status=status, **kw))


def note(ids, title, text, sources):
    notes.append(dict(nodes=ids, title=title, text=text, sources=sources))


src(
    "glottolog",
    "Glottolog 5.3",
    "https://doi.org/10.5281/zenodo.18840935",
    "catalog",
    license="CC BY 4.0",
)
src(
    "power2020",
    "Power, Grimm & List (2020) · Evolutionary dynamics in the dispersal of sign languages",
    "https://doi.org/10.1098/rsos.191100",
    "research",
    dataset="https://github.com/lexibank/powerma",
    license="CLDF dataset: GPL-3.0; paper: CC BY 4.0",
    scope="All language/sample rows and published SubGroup metadata; not a reconstruction of the paper’s reticulate network.",
)
src(
    "abner2024",
    "Abner et al. (2024) · Computational phylogenetics reveal histories of sign languages",
    "https://doi.org/10.1126/science.add7766",
    "research",
    dataset="https://github.com/GClarte/SignLanguagesPhylogeny",
    scope="Three annotated consensus trees: Asia and two independent European/New Zealand replicates. 19 distinct language samples. No all-sign-languages tree, posterior tree sample or calendar-time interpretation.",
)
src(
    "power2022",
    "Power (2022) · Historical Linguistics of Sign Languages: Progress and Problems",
    "https://doi.org/10.3389/fpsyg.2022.818753",
    "review",
    scope="Methodological context, not another imported tree.",
)
src(
    "power2025",
    "Power (2025) · Advances in the Historical Linguistics of Signed Languages",
    "https://doi.org/10.1111/lnc3.70026",
    "review",
    scope="Comparison of lexical and manual-alphabet results; selected claims, not full article import.",
)
src(
    "iso",
    "ISO 15924 Registration Authority · complete downloaded code table",
    "https://unicode.org/iso15924/iso15924.txt",
    "catalog",
    license="Unicode terms of use",
    scope="Every non-comment code row, including script variants, collections and special-purpose codes.",
)
src(
    "sil",
    "SIL · Writing Systems Technical Resources, Scripts Index",
    "https://writingsystems.info/scrlang/scripts-index/",
    "catalog",
    license="CC BY-SA 4.0",
    scope="All 325 rows of the downloaded index, including non-ISO local identifiers. Reported types and statuses are catalog metadata, not independently verified genealogy.",
)
src(
    "cldr",
    "Unicode CLDR · supplemental languageData",
    "https://github.com/unicode-org/cldr/blob/main/common/supplemental/supplementalData.xml",
    "usage data",
    license="Unicode-3.0",
    scope="All explicit script entries under languageData. Primary/secondary designation preserved. Not a complete global orthography inventory; no inferred language genealogy.",
)
src(
    "ucd",
    "Unicode 17.0 · Scripts and UnicodeData",
    "https://www.unicode.org/Public/17.0.0/ucd/",
    "character data",
    license="Unicode-3.0",
    scope="Up to six letter characters per script for illustrative glyph samples; samples are not native names.",
)
for ch, title in [
    (7, "Europe I"),
    (8, "Europe II"),
    (9, "Middle East I"),
    (10, "Middle East II"),
    (11, "Cuneiform and Hieroglyphs"),
    (12, "South and Central Asia I"),
    (13, "South and Central Asia II"),
    (14, "South and Central Asia III"),
    (15, "South and Central Asia IV"),
    (16, "Southeast Asia"),
    (17, "Indonesia and Oceania"),
    (18, "East Asia"),
    (19, "Africa"),
    (20, "America"),
]:
    src(
        "u" + str(ch),
        "Unicode 17.0, chapter " + str(ch) + " · " + title,
        f"https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-{ch}/",
        "standard chapter",
        scope="Selected historical relationships reviewed; chapter sections are not counted as independent research studies.",
    )
src(
    "pillai2023",
    "Pillai (2023) · The Hybrid Origin of Brāhmī Script from Aramaic, Phoenician and Greek Letters",
    "https://doi.org/10.5565/rev/indialogs.213",
    "research",
    scope="A proposed hybrid origin, not an established consensus.",
)
src(
    "lee2013",
    "Lee Ji-young (2013) · Hangeul, Academy of Korean Studies",
    "https://www.aks.ac.kr/ikorea/upload/intl/korean/UserFiles/UKS1_Hangeul_eng.pdf",
    "scholarly book",
    scope="Design principles and discussion of Ledyard’s proposed Phags-pa influence.",
)
src(
    "ledyard1966",
    "Ledyard (1966) · The Korean Language Reform of 1446",
    "https://books.google.com/books?id=1bELAQAAMAAJ",
    "thesis reference",
    scope="Bibliographic link; proposed influence summarized through Lee (2013), not a full-text import.",
)
src(
    "signwriting",
    "Sutton SignWriting · official project",
    "https://www.signwriting.org/",
    "project documentation",
    scope="Writing of sign languages, not their genealogy.",
)
src(
    "hamnosys",
    "University of Hamburg · HamNoSys",
    "https://www.sign-lang.uni-hamburg.de/dgs-korpus/hamnosys-97.html",
    "research infrastructure",
    scope="Sign-language transcription system, not a language family.",
)
src(
    "senghas2004",
    "Senghas, Kita & Özyürek (2004) · Children creating core properties of language",
    "https://doi.org/10.1126/science.1100199",
    "research",
    scope="Emergence of Nicaraguan Sign Language; not a comparative family tree.",
)
# Exact Glottocode identities; retain all aliases and native-name evidence.
for i, b in B.items():
    if b["category"] == "Sign Language":
        node(i, b["name"], "sign", b["level"], iso=b["iso"], area=b["area"], sources=["glottolog"])
        N[i]["aliases"] = b["names"]
        N[i]["nativeNames"] = b["nativeNames"]
category = {"sign1238", "deaf1237", "auxi1235", "pidg1253", "unun9986"}
for i, n in list(N.items()):
    p = B[i]["parent"]
    if p in N:
        edge(p, i, "glottolog", "catalog navigation" if p in category else "catalog classification")
    if i in category:
        n["kind"] = "navigation category"
iso = {n.get("iso"): i for i, n in N.items() if n.get("iso")}


# Import only the independent consensus trees sanctioned by the study README.
class Parser:
    def __init__(self, s):
        self.t = re.findall(r"\[[^\]]*\]|[(),:;]|[^\s(),:;\[\]]+", s)
        self.i = 0

    def parse(self):
        kids = []
        label = ""
        meta = ""
        length = ""
        while self.t[self.i].startswith("["):
            self.i += 1
        if self.t[self.i] == "(":
            self.i += 1
            while True:
                kids.append(self.parse())
                c = self.t[self.i]
                self.i += 1
                if c == ")":
                    break
                assert c == ","
        if self.t[self.i] not in [",", ")", ":", ";"] and not self.t[self.i].startswith("["):
            label = self.t[self.i]
            self.i += 1
        while self.t[self.i].startswith("["):
            meta += self.t[self.i]
            self.i += 1
        if self.t[self.i] == ":":
            self.i += 1
            length = self.t[self.i]
            self.i += 1
        pp = re.search(r"(?:,|\[&)posterior=([\d.]+)", meta)
        return dict(
            children=kids, label=label, length=length, posterior=float(pp[1]) if pp else None
        )


mapiso = {
    "Chinese": "csl",
    "Hong Kong": "hks",
    "Japanese": "jsl",
    "Taiwanese": "tss",
    "American": "ase",
    "Austrian": "asq",
    "Czech": "cse",
    "British": "bfi",
    "Estonian": "eso",
    "French": "fsl",
    "German": "gsg",
    "Italian": "ise",
    "Latvian": "lsl",
    "Lithuanian": "lls",
    "New Zealand": "nzs",
    "Polish": "pso",
    "Russian": "rsl",
    "Spanish": "ssp",
    "Ukrainian": "ukl",
}
studies = []
for run in ["Asia", "EBNZ_1", "EBNZ_2"]:
    s = (P / (run + ".nex")).read_text()
    trans = dict(
        re.findall(r'(\d+)\s+"([^"]+)"', re.split("translate", s, flags=re.I)[1].split(";")[0])
    )
    t = Parser(re.search(r"tree TREE1\s*=\s*(.*?);", s, re.S)[1] + ";").parse()
    count = [0]
    tips = []

    def walk(t, parent=None):
        count[0] += 1
        if t["children"]:
            i = node(
                "abner:" + run + ":" + str(count[0]),
                "Sampled clade",
                "sign",
                "study clade",
                sources=["abner2024"],
                run=run,
                posterior=t["posterior"],
            )
            members = []
            for k in t["children"]:
                members += walk(k, i)[1]
            N[i]["name"] = (
                ("Asia sample" if run == "Asia" else "Europe + New Zealand · replicate " + run[-1])
                if parent is None
                else "Clade: "
                + ", ".join(N[m]["name"].replace(" Sign Language", "") for m in members[:3])
                + (" …" if len(members) > 3 else "")
            )
        else:
            label = trans[t["label"]]
            i = iso[mapiso[label.replace(" SL", "")]]
            members = [i]
            tips.append(i)
        if parent:
            edge(
                parent,
                i,
                "abner2024",
                "lexical-feature phylogeny",
                run=run,
                branchLength=t["length"],
                posterior=t["posterior"],
                sample=trans.get(t["label"]),
            )
        return i, members

    root, members = walk(t)
    studies.append(dict(root=root, run=run, tips=tips, source="abner2024"))
# Manual-alphabet samples remain distinct: historical samples do not equal contemporary languages.
rows = list(csv.DictReader((P / "power-languages.csv").open()))
groups = {}
for r in rows:
    g = r["SubGroup"] or "Unassigned"
    if g not in groups:
        groups[g] = node(
            "power:group:" + g,
            g + " · manual-alphabet sample group",
            "sign",
            "sample grouping",
            sources=["power2020"],
        )
    i = node(
        "power:sample:" + r["ID"],
        r["Name"].replace("_", " "),
        "sign",
        "manual-alphabet sample",
        sources=["power2020"],
        sampleID=r["ID"],
        glottocode=r["Glottocode"],
        area=r["Macroarea"],
    )
    edge(groups[g], i, "power2020", "manual-alphabet metadata subgroup")
    if r["Glottocode"] in N:
        edge(i, r["Glottocode"], "power2020", "sample identity link")
note(
    ["czec1253"],
    "Different evidence, different placement",
    "Manual-alphabet comparisons group the Czech sample with two-handed alphabets; Abner’s lexical-feature analysis places Czech among European samples. This is a difference in the compared subsystem, not proof that one entire-language genealogy is wrong.",
    ["power2020", "abner2024", "power2025"],
)
note(
    ["lith1236", "poli1259"],
    "Compare lexical and manual-alphabet results",
    "The review describes Lithuanian and Polish manual alphabets as intermediate between Russian and Austrian groups. In the lexical analysis, Lithuanian clusters with eastern European samples while Polish is less resolved. Contact and different evidence can explain some differences.",
    ["power2020", "abner2024", "power2025"],
)
note(
    list(iso.values()),
    "How to read sign-language evidence",
    "Manual alphabets encode fingerspelling; lexical-feature trees compare properties of vocabulary. Neither should be silently substituted for an established cognate-based genealogy. Catalog categories are navigation, not a proposed ancestor of all sign languages.",
    ["power2022", "glottolog"],
)
if "ncs" in iso:
    note(
        [iso["ncs"]],
        "Language emergence",
        "Research on Nicaraguan Sign Language examines the emergence of structure across cohorts. It does not establish descent from the spoken language of the surrounding community.",
        ["senghas2004"],
    )
# ISO script catalog, including collection/special codes, exactly as published.
iso_rows = []
for line in (P / "iso15924.txt").read_text().splitlines():
    if not line or line.startswith("#"):
        continue
    code, num, en, fr, pva, version, date = line.split(";")
    iso_rows.append(code)
    node(
        code,
        en,
        "scripts",
        "script code",
        code=code,
        numericCode=num,
        pva=pva,
        unicodeVersion=version,
        codeDate=date,
        sources=["iso"],
    )
    N[code]["aliases"] = [dict(text=fr, lang="fr", source="iso")]
    if (
        code in ["Zinh", "Zyyy", "Zzzz", "Zxxx", "Zsym", "Zsye", "Zmth", "Qaaa", "Qabx"]
        or "collection" in en.lower()
    ):
        N[code]["kind"] = "special / collection code"


# SIL includes proposed, undeciphered and unencoded systems, not just Unicode scripts.
class Table(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, t, a):
        if t == "tr":
            self.row = []
        if t in ("td", "th"):
            self.cell = ""

    def handle_data(self, d):
        if self.cell is not None:
            self.cell += d

    def handle_endtag(self, t):
        if t in ("td", "th") and self.cell is not None:
            if self.row is not None:
                self.row.append(self.cell.strip())
            self.cell = None
        if t == "tr" and self.row:
            self.rows.append(self.row)
            self.row = None


p = Table()
p.feed((P / "sil-scripts.html").read_text())
silrows = p.rows[1:]
for code, name, region, typ, direction, status in silrows:
    i = code if code in N else "sil:" + code
    if i not in N:
        node(i, name, "scripts", "SIL script entry", code=code, sources=["sil"])
    else:
        N[i]["sources"].append("sil")
    N[i]["aliases"].append(dict(text=name, source="sil"))
    N[i].update(region=region, silType=typ, direction=direction, silStatus=status)


# Curated edges: explicit source-conditioned relationships, with broad ancestry marked.
def se(p, c, ch, kind="historical descent", status="reported", **kw):
    edge(p, c, "u" + str(ch), kind, status, **kw)


for p, c in [
    ("Phnx", "Grek"),
    ("Grek", "Ital"),
    ("Ital", "Latn"),
    ("Grek", "Cyrl"),
    ("Grek", "Copt"),
]:
    se(p, c, 7)
for c in ["Armn", "Geor"]:
    se("Grek", c, 7, "graphic influence")
for c in ["Armi"]:
    se("Phnx", c, 10)
for c in ["Hebr", "Nbat", "Palm", "Prti", "Phli", "Chrs"]:
    se("Armi", c, 10)
se("Armi", "Arab", 10, "historical descent · intermediate stages omitted")
se("Armi", "Sogd", 14, "historical descent · intermediate stages omitted")
se("Sogo", "Sogd", 14)
se("Sogd", "Ougr", 14)
se("Sogd", "Orkh", 14, status="tentative")
se("Phlv", "Avst", 10)
se("Syrc", "Mani", 10, "graphic influence")
se("Palm", "Mani", 10, "graphic influence")
se("Phnx", "Samr", 9, "historical descent · via Old Hebrew", status="probable")
se("Armi", "Mand", 9, status="tentative")
se("Egyd", "Merc", 11, "graphic model")
se("Egyp", "Mero", 11, "graphic model")
for c in ["Deva", "Beng", "Guru", "Gujr", "Orya", "Taml", "Telu", "Knda", "Mlym"]:
    se("Brah", c, 12, "historical descent · intermediate stages omitted")
for c in ["Sinh", "Tibt"]:
    se("Brah", c, 13, "historical descent · intermediate stages omitted")
se("Tibt", "Phag", 14)
se("Brah", "Bhks", 14, "historical descent · intermediate stages omitted")
se("Armi", "Khar", 14, status="probable")
se(
    "Armi",
    "Brah",
    14,
    "proposed origin",
    status="probable",
    hypothesis="Semitic / probably Aramaic origin",
)
for c in ["Armi", "Phnx", "Grek"]:
    edge(
        c,
        "Brah",
        "pillai2023",
        "proposed hybrid contribution",
        "hypothesis",
        hypothesis="Hybrid origin: Aramaic + Phoenician + Greek",
    )
for c in ["Sidd", "Dogr", "Mult"]:
    se("Brah", c, 15, "historical descent · intermediate stages omitted")
se("Shrd", "Takr", 15, "historical descent · via Devāśeṣa")
for c in ["Thai", "Laoo", "Mymr", "Khmr"]:
    se("Brah", c, 16, "historical descent · intermediate stages omitted")
se("Brah", "Kawi", 17, "historical descent · intermediate stages omitted")
se("Kawi", "Bali", 17)
se("Rjng", "Maka", 17, status="tentative")
se("Hani", "Hira", 18, "graphic derivation")
se("Hani", "Kana", 18, "graphic derivation")
se("Lana", "Talu", 16, "orthographic simplification")
se("Mymr", "Kali", 16, "graphic influence")
se("Ougr", "Mong", 14)
se("Hani", "Nshu", 18, "graphic derivation")
se("Latn", "Lisu", 18, "graphic adaptation")
# Link proposed Phags-pa influence without replacing the documented design account.
edge(
    "Phag",
    "Hang",
    "ledyard1966",
    "proposed graphic influence",
    "disputed hypothesis",
    hypothesis="Ledyard: influence on selected consonant forms; criticized by Lee (2013)",
    reportedVia="lee2013",
)
note(
    ["Hang"],
    "Design account and proposed influence",
    "Ledyard (1966) proposes a Phags-pa connection for selected consonant forms. Lee (2013), pp. 40–42, criticizes that proposal: the selected basic letters differ from the design account in Hunminjeongeum haerye. Lee favors the documented articulatory design account. The proposed connection is disputed, not established descent of the whole system.",
    ["lee2013", "ledyard1966"],
)
note(
    ["Brah"],
    "Competing origin accounts",
    "Unicode describes an ultimately Semitic, probably Aramaic origin. Pillai (2023) instead proposes a hybrid drawing on Aramaic, Phoenician and Greek. The latter is a published hypothesis, not a settled replacement for other accounts.",
    ["u14", "pillai2023"],
)
N["Hang"]["nativeNames"] = [dict(text="한글", lang="ko", source="lee2013")]
N["Hang"]["aliases"].extend(
    [dict(text="Hangeul", source="lee2013"), dict(text="Hunminjeongeum", source="lee2013")]
)
# Notation systems are not sign-language families.
if "sil:x-hamnosys" not in N:
    matches = [i for i, n in N.items() if "hamnosys" in n["name"].lower()]
    ham = (
        matches[0]
        if matches
        else node(
            "notation:hamnosys", "HamNoSys", "scripts", "transcription system", sources=["hamnosys"]
        )
    )
else:
    ham = "sil:x-hamnosys"
note(
    ["Sgnw", ham],
    "Writing signs is not language ancestry",
    "SignWriting is used to write sign languages; HamNoSys is a transcription system for signs. Sharing a notation does not make two sign languages genealogically related. No universal language-to-notation usage edges are inferred.",
    ["signwriting", "hamnosys"],
)
# Explicit CLDR language/script usage, separate from lineage assertions.
root = ET.parse(P / "cldr-supplemental.xml").getroot()
for r in root.findall("./languageData/language"):
    for script in r.get("scripts", "").split():
        if script in N:
            usage.append(
                dict(
                    language=r.get("type"),
                    script=script,
                    status=r.get("alt", "primary"),
                    territories=r.get("territories", "").split(),
                    source="cldr",
                )
            )
# Glyph samples: actual UCD letters, never claimed as a script's self-name.
letters = {
    int(r[0], 16)
    for row in (P / "UnicodeData.txt").read_text().splitlines()
    if (r := row.split(";"))[2].startswith("L")
}
pva = {n.get("pva"): i for i, n in N.items() if n.get("pva")}
samples = collections.defaultdict(list)
for line in (P / "Scripts.txt").read_text().splitlines():
    m = re.match(r"([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)", line)
    if not m or m[3] not in pva:
        continue
    i = pva[m[3]]
    for cp in range(int(m[1], 16), int(m[2] or m[1], 16) + 1):
        if len(samples[i]) == 6:
            break
        if cp in letters:
            samples[i].append(chr(cp))
for i, chars in samples.items():
    N[i]["glyphSample"] = " ".join(chars)
    N[i]["glyphSource"] = "ucd"
for e in E:
    for i in [e["parent"], e["child"]]:
        if e["source"] not in N[i]["sources"]:
            N[i]["sources"].append(e["source"])
# Evidence remains separate for sources, observations, and illustrative characters.
counts = dict(
    glottologSignRecords=sum(i in B and n["domain"] == "sign" for i, n in N.items()),
    iso15924Rows=len(iso_rows),
    silRows=len(silrows),
    scriptRecords=sum(n["domain"] == "scripts" for n in N.values()),
    manualAlphabetSamples=len(rows),
    consensusTrees=len(studies),
    distinctLexicalSamples=len(set(x for t in studies for x in t["tips"])),
    scriptRelationships=sum(N[e["child"]]["domain"] == "scripts" for e in E),
    usageAssertions=len(usage),
    sourceEntries=len(S),
)
files = []
for f in sorted(P.iterdir()):
    if f.is_file():
        files.append(
            dict(
                path=str(f),
                sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                bytes=f.stat().st_size,
            )
        )
result = dict(
    schemaVersion=1,
    retrieved="2026-10-17",
    nodes=N,
    assertions=E,
    sources=S,
    notes=notes,
    usage=usage,
    studies=studies,
    counts=counts,
    files=files,
    limitations=[
        "Complete imports of the identified catalog snapshots, not a complete inventory of all world languages or scripts.",
        "All 344 Glottolog Sign Language-category records are preserved, including families, dialects and non-genealogical categories.",
        "Script catalog membership is much broader than the manually reviewed historical relationship set. A script with no edge has an unreviewed or unasserted placement, not a certified independent origin.",
        "SIL-local IDs are preserved and never fuzzy-merged with ISO codes. Possible duplicate concepts remain source-specific.",
        "Historical descent, graphic influence, sample identity and script usage are distinct relations. No global common ancestor is asserted.",
        "English and French catalog labels and all Glottolog aliases are retained. Verified native names are sparse; script glyph samples are not autonyms. Sign-language self-names generally need video or sign notation and have not been fabricated.",
        "Only selected source-backed disagreements are reviewed. No claim that every competing publication is incorporated.",
        "Abner consensus branch lengths and posterior annotations are retained in JSON/XML; no time-scaled visual or posterior sample inference. Two European runs are replicates, not independent papers.",
    ],
)
(D / "signs-and-scripts.json").write_text(
    json.dumps(result, ensure_ascii=False, separators=(",", ":"))
)
# Lossless nested XML for every JSON field, with explicit types.
x = ET.Element("visualLanguageAtlas", schemaVersion="1")


def xml(parent, value):
    if isinstance(value, dict):
        parent.set("type", "object")
        for k, v in value.items():
            c = ET.SubElement(parent, "field", name=k)
            xml(c, v)
    elif isinstance(value, list):
        parent.set("type", "array")
        for v in value:
            xml(ET.SubElement(parent, "item"), v)
    else:
        parent.set(
            "type",
            "null"
            if value is None
            else "boolean"
            if isinstance(value, bool)
            else "number"
            if isinstance(value, (int, float))
            else "string",
        )
        parent.text = "" if value is None else str(value)


xml(x, result)
ET.ElementTree(x).write(D / "signs-and-scripts.xml", encoding="utf-8", xml_declaration=True)
# Outline repeats IDs across alternative parents; usage remains in JSON/XML.
o = ET.Element("opml", version="2.0")
ET.SubElement(
    ET.SubElement(o, "head"), "title"
).text = "Sign languages and writing systems — source-conditioned outline"
body = ET.SubElement(o, "body")
out = collections.defaultdict(list)
incoming = set()
for e in E:
    out[e["parent"]].append(e)
    incoming.add(e["child"])


def emit(p, i, path, relation=None):
    attrs = dict(text=N[i]["name"], recordId=i)
    if relation:
        attrs.update(
            source=S[relation["source"]]["url"],
            relation=relation["kind"],
            status=relation["status"],
        )
    q = ET.SubElement(p, "outline", attrs)
    if i in path:
        q.set("reference", "cycle")
        return
    for e in out[i]:
        emit(q, e["child"], path | {i}, e)


for domain in ["sign", "scripts"]:
    q = ET.SubElement(body, "outline", text=domain)
    for i, n in N.items():
        if n["domain"] == domain and i not in incoming:
            emit(q, i, set())
ET.ElementTree(o).write(D / "signs-and-scripts.opml", encoding="utf-8", xml_declaration=True)
print(json.dumps(counts, indent=2))
