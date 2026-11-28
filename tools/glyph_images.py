"""Script samples as pictures: the letters of a writing system drawn from the Noto fonts at build time.

A record of a writing system shows a few of its letters (glyphSample, tools/build_visual.py). As
text they show as empty boxes ("tofu") on any device without a font for the script, which is most
devices for most scripts (the owner's report of Duployan on Android, 2026-11-27, and the owner's
choice to show them as images). So the build draws each sample from the Noto fonts (SIL Open Font
License 1.1) into one SVG symbol per record, dist/glyphs/<id>.svg, filled with currentColor, and the
pages draw it with <use href="glyphs/<id>.svg#glyphs"> in the text colour, like the logo.

- tools/glyph-fonts.json lists the Noto font files, from one fixed commit of the
  notofonts.github.io repository, then Noto Sans CJK (Han, kana, Hangul and Bopomofo) from one fixed
  commit of noto-cjk, each with its address and SHA-256. It is written by --update, never by hand.
- draw() takes the first listed font that has a letter (Noto Sans first). A sample with a letter no
  listed font has gets no picture (Noto has no font yet for some new scripts), and the pages then
  show no sample rather than empty boxes.

Usage:
  build_visual.py imports draw() and Glyphs
  python3 tools/glyph_images.py --update <notofonts.github.io commit> <noto-cjk commit>
      rewrite tools/glyph-fonts.json from those commits
"""

import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from locations import DIST, ROOT

LOCK = ROOT / "tools" / "glyph-fonts.json"
CACHE = ROOT / "build" / "fonts"
OUT = DIST / "glyphs"
SYMBOL = "glyphs"  # the id of the <symbol> in each file; pages write "#glyphs"
REPOSITORY = "https://github.com/notofonts/notofonts.github.io"
RAW = "https://raw.githubusercontent.com/notofonts/notofonts.github.io/{commit}/{path}"
# One font for Han, kana, Hangul and Bopomofo (not in notofonts.github.io).
CJK = "https://raw.githubusercontent.com/notofonts/noto-cjk/{commit}/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
# The regular weight of every Noto font, without hinting.
FONT_FILE = re.compile(r"^fonts/[^/]+/unhinted/ttf/[^/]+-Regular\.ttf$")
# Units per em of the drawing: every font is scaled to it, so samples from different fonts
# share one size.
EM = 1000
# Space between letters, in EM units (a quarter em, about a word space).
GAP = 250
# Height of a sample above and below the baseline, in EM units: room for the tallest letters
# and the deepest descenders of the scripts, so every sample has the same height on the page.
ASCENT = 1100
DESCENT = 400


def font_order(path):
    """Noto Sans first (Latin, Greek, Cyrillic), then each script's Sans, then the rest."""
    name = path.rsplit("/", 1)[1]
    return (name != "NotoSans-Regular.ttf", not name.startswith("NotoSans"), name)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def download(url):
    with urllib.request.urlopen(url) as answer:
        return answer.read()


def update(commit, cjk_commit):
    """List the Noto fonts at the two commits and write tools/glyph-fonts.json."""
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
    urls = [RAW.format(commit=commit, path=p) for p in paths] + [CJK.format(commit=cjk_commit)]
    lock = {"fonts": [{"url": u, "sha256": sha256(download(u))} for u in urls]}
    LOCK.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"{LOCK.relative_to(ROOT)}: {len(urls)} fonts")


def fetch(entry):
    """The file of a lock entry, from build/fonts/ or downloaded; fails on a wrong SHA-256."""
    local = CACHE / entry["sha256"]
    if local.is_file():
        data = local.read_bytes()
    else:
        data = download(entry["url"])
        CACHE.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
    if sha256(data) != entry["sha256"]:
        local.unlink()
        sys.exit(f"{entry['url']}: SHA-256 differs from {LOCK.relative_to(ROOT)}")
    return data


class Glyphs:
    """The listed fonts, loaded once, and the first that has each letter."""

    def __init__(self):
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.fonts = [TTFont(io.BytesIO(fetch(e))) for e in lock["fonts"]]
        self.cmaps = [f.getBestCmap() for f in self.fonts]

    def font_for(self, char):
        for font, cmap in zip(self.fonts, self.cmaps, strict=True):
            if ord(char) in cmap:
                return font, cmap[ord(char)]
        return None


def draw(glyphs, record_id, letters):
    """Write dist/glyphs/<record_id>.svg; its address and size, or None when a letter has no font."""
    # A right-to-left script's letters run from right to left, as the text did.
    if letters and unicodedata.bidirectional(letters[0]) in ("R", "AL"):
        letters = letters[::-1]
    found = [glyphs.font_for(ch) for ch in letters]
    if not found or not all(found):
        return None
    pen = SVGPathPen(None)
    x = 0
    for n, (font, name) in enumerate(found):
        scale = EM / font["head"].unitsPerEm
        glyph_set = font.getGlyphSet()
        # Composite glyphs are drawn from their parts, which live in their own font.
        outline = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(outline)
        outline.replay(TransformPen(pen, (scale, 0, 0, -scale, x, ASCENT)))
        x += font["hmtx"][name][0] * scale + (GAP if n < len(found) - 1 else 0)
    width, height = round(x), ASCENT + DESCENT
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{record_id}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg"><symbol id="{SYMBOL}" viewBox="0 0 {width} {height}">'
        f'<path d="{pen.getCommands()}" fill="currentColor"/></symbol></svg>\n',
        encoding="utf-8",
    )
    return {"src": f"glyphs/{record_id}.svg", "width": width, "height": height}


def main(argv):
    if argv[:1] == ["--update"] and len(argv) == 3:
        update(argv[1], argv[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
