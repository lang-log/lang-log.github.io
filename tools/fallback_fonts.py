"""Fallback fonts: every character the site shows can be drawn, even when the device has no font for it.

A visitor whose phone or computer has no font for a script (Duployan, Ahom, Cypro-Minoan ...)
would see empty boxes ("tofu") for the script samples and the names written in it. The site
therefore serves its own copies of the Noto fonts (SIL Open Font License 1.1), cut down to the
characters the site uses:

- tools/fallback-fonts.json lists the Noto font files, from one fixed commit of the
  notofonts.github.io repository, each with its SHA-256. It is written by --update, never by hand.
- The build downloads them into build/fonts/ (checked against the SHA-256), reads every
  character in the built pages and data in dist/, gives each character to the first listed font
  that has it, and writes one cut-down font per Noto font, dist/fonts/<hash>.woff2, with
  dist/fonts.css: one @font-face of the fallback family per file, with its unicode-range, so a
  browser downloads a file only when a page needs one of its characters and no font before it
  in the stack has that character. dist/fonts/LICENSE is the fonts' license.
- dist/style.css imports dist/fonts.css and puts the family last in --font (and in .v-glyphs), so
  a device's own fonts are used whenever they have the character. The family name is written once,
  as --font-fallback in dist/style.css; family() reads it.

Characters no listed font has (Han, Hangul and kana, which every system has, and scripts
Noto does not cover yet) are counted in the output, by script.

Usage:
  python3 tools/fallback_fonts.py                   write dist/fonts/ and dist/fonts.css (after the pages)
  python3 tools/fallback_fonts.py --update <commit> rewrite tools/fallback-fonts.json from that commit
"""

import hashlib
import io
import json
import logging
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from collections import Counter

from fontTools import subset
from fontTools.ttLib import TTFont

from locations import DIST, ROOT, SOURCE_DATA

LOCK = ROOT / "tools" / "fallback-fonts.json"
CACHE = ROOT / "build" / "fonts"
OUT = DIST / "fonts"
CSS = DIST / "fonts.css"
REPOSITORY = "https://github.com/notofonts/notofonts.github.io"
RAW = "https://raw.githubusercontent.com/notofonts/notofonts.github.io/{commit}/{path}"
# The regular weight of every Noto font, without hinting (smaller; browsers hint themselves).
FONT_FILE = re.compile(r"^fonts/[^/]+/unhinted/ttf/[^/]+-Regular\.ttf$")
LICENSE_PATH = "fonts/LICENSE"
# Built files whose characters the site shows.
TEXT_SUFFIXES = {".html", ".json", ".js", ".xml", ".opml"}
# Hex digits of the content hash in a font's file name.
HASH_CHARS = 10


def family():
    """The fallback family's name, from --font-fallback in dist/style.css."""
    m = re.search(r"--font-fallback:\s*'([^']+)'", (DIST / "style.css").read_text(encoding="utf-8"))
    if not m:
        sys.exit("dist/style.css: no --font-fallback")
    return m[1]


def font_order(path):
    """Noto Sans first (Latin, Greek, Cyrillic), then each script's Sans, then the rest."""
    name = path.rsplit("/", 1)[1]
    return (name != "NotoSans-Regular.ttf", not name.startswith("NotoSans"), name)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def download(commit, path):
    with urllib.request.urlopen(RAW.format(commit=commit, path=path)) as answer:
        return answer.read()


def update(commit):
    """List the Noto fonts at `commit` and write tools/fallback-fonts.json."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, tmp], check=True
        )
        names = subprocess.run(
            ["git", "-C", tmp, "ls-tree", "-r", "--name-only", commit],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
    paths = sorted((p for p in names if FONT_FILE.match(p)), key=font_order)
    lock = {
        "repository": REPOSITORY,
        "commit": commit,
        "license": {"path": LICENSE_PATH, "sha256": sha256(download(commit, LICENSE_PATH))},
        "fonts": [{"path": p, "sha256": sha256(download(commit, p))} for p in paths],
    }
    LOCK.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"{LOCK.relative_to(ROOT)}: {len(paths)} fonts from {commit}")


def fetch(commit, entry):
    """The file of a lock entry, from build/fonts/ or downloaded; fails on a wrong SHA-256."""
    local = CACHE / entry["sha256"]
    if local.is_file():
        data = local.read_bytes()
    else:
        data = download(commit, entry["path"])
        CACHE.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
    if sha256(data) != entry["sha256"]:
        local.unlink()
        sys.exit(f"{entry['path']}: SHA-256 differs from {LOCK.relative_to(ROOT)}")
    return data


def site_characters():
    chars = set()
    for path in DIST.rglob("*"):
        if path.suffix in TEXT_SUFFIXES and path.is_file():
            chars |= set(path.read_text(encoding="utf-8"))
    # Control characters and spaces need no glyph. (Not str.isprintable(): Python's own Unicode
    # tables can be older than the scripts the site shows, and call their letters unassigned.)
    return {ord(c) for c in chars if unicodedata.category(c) != "Cc" and not c.isspace()}


def unicode_range(codepoints):
    """CSS unicode-range for a set of code points, as runs of neighbours."""
    runs, start, prev = [], None, None
    for cp in sorted(codepoints):
        if start is None or cp != prev + 1:
            if start is not None:
                runs.append((start, prev))
            start = cp
        prev = cp
    runs.append((start, prev))
    return ", ".join(f"U+{a:X}" if a == b else f"U+{a:X}-{b:X}" for a, b in runs)


def script_names():
    """Unicode script of each code point (source-data/signs-and-scripts/Scripts.txt)."""
    names = {}
    for line in (SOURCE_DATA / "signs-and-scripts" / "Scripts.txt").read_text().splitlines():
        m = re.match(r"([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*(\w+)", line)
        if m:
            for cp in range(int(m[1], 16), int(m[2] or m[1], 16) + 1):
                names[cp] = m[3]
    return names


def cut(data, codepoints):
    """A WOFF2 file of `data` with only `codepoints` (and what shaping them needs)."""
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]  # joining and reordering, for scripts that need them
    options.name_IDs = ["*"]  # keeps the copyright and license entries
    options.notdef_outline = True
    # The subsetter reports each table it drops (such as "meta"); only errors matter here.
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    font = TTFont(io.BytesIO(data))
    sub = subset.Subsetter(options)
    sub.populate(unicodes=codepoints)
    sub.subset(font)
    out = io.BytesIO()
    font.flavor = "woff2"
    font.save(out)
    return out.getvalue()


def build():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    commit = lock["commit"]
    name_of_family = family()
    left = site_characters()
    chosen = []
    for entry in lock["fonts"]:
        data = fetch(commit, entry)
        has = left & set(TTFont(io.BytesIO(data)).getBestCmap())
        if has:
            chosen.append((entry, data, has))
            left -= has
    for old in OUT.glob("*.woff2") if OUT.is_dir() else []:
        old.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "LICENSE").write_bytes(fetch(commit, lock["license"]))
    rules = []
    for entry, data, has in chosen:
        woff2 = cut(data, has)
        name = sha256(woff2)[:HASH_CHARS] + ".woff2"
        (OUT / name).write_bytes(woff2)
        rules.append(
            f"/* {entry['path'].rsplit('/', 1)[1]} */\n"
            f'@font-face {{\n  font-family: "{name_of_family}";\n  src: url("fonts/{name}") format("woff2");\n'
            f"  unicode-range: {unicode_range(has)};\n  font-display: swap;\n}}\n"
        )
    CSS.write_text(
        "/* Written by tools/fallback_fonts.py: Noto fonts (SIL Open Font License 1.1, fonts/LICENSE)\n"
        "   cut down to the characters the site uses, for devices without a font for them. */\n"
        + "".join(rules),
        encoding="utf-8",
    )
    scripts = script_names()
    missing = Counter(scripts.get(cp, "Unknown") for cp in left)
    size = sum(p.stat().st_size for p in OUT.glob("*.woff2"))
    print(
        f"dist/fonts/: {len(chosen)} fonts, {size // 1024} KiB; "
        f"characters without a fallback font: {len(left)}"
        + (" (" + ", ".join(f"{s} {n}" for s, n in missing.most_common()) + ")" if left else "")
    )


def main(argv):
    if argv[:1] == ["--update"] and len(argv) == 2:
        update(argv[1])
    elif not argv:
        build()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
