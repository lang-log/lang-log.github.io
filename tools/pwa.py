"""Lang Log as a progressive web app (PWA): one place for its manifest and the tags every page needs.

Lang Log is to be a PWA (the owner's decision, 2026-11-08; CLAUDE.md). Two parts:

- dist/manifest.webmanifest, written here at build time (not committed) from the
  site name in tools/site_brand.py and the icons already in dist/. Its addresses are
  relative to the manifest, so the same file works on the live site and in a pull
  request preview under /preview/pr-<number>/.
- dist/sw.js, the service worker, registered by dist/pwa.js. It keeps the pages and
  files a visitor has opened, so they open again offline (.claude/rules/pwa.md).

Every page links both in its <head> with head_tags(): the page generators
(tools/build_home.py, tools/build_paths.py, tools/info_page.py) call it, and the
hand-written pages in dist/*.html carry the same text.

Usage (tools/build_site.sh):
  python3 tools/pwa.py           write dist/manifest.webmanifest
  python3 tools/pwa.py --check   fail if a page in dist/ lacks the tags, or the
                                 manifest or the service worker is missing
"""

import json
import re
import struct
import sys

from locations import DIST
from site_brand import HOME_TITLE, SITE_NAME

MANIFEST = DIST / "manifest.webmanifest"
REGISTER_SCRIPT = "pwa.js"
SERVICE_WORKER = DIST / "sw.js"
# The icons are the favicon (the asterisk, .claude/rules/logo.md): the SVG for any size,
# and the PNG that iOS uses for the home screen.
ICON_SVG = "favicon.svg"
ICON_PNG = "apple-touch-icon.png"


def head_tags(up):
    """The <head> tags of a page `up` levels below dist/ ("", "../", or "/" for 404.html)."""
    return (
        f'<link rel="manifest" href="{up}{MANIFEST.name}">'
        f'<script src="{up}{REGISTER_SCRIPT}"></script>'
    )


def png_size(path):
    """Width and height of a PNG file, read from its IHDR chunk."""
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG file")
    return struct.unpack(">II", head[16:24])


def manifest():
    width, height = png_size(DIST / ICON_PNG)
    return {
        "name": HOME_TITLE,
        "short_name": SITE_NAME,
        "id": "./",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "icons": [
            {"src": ICON_SVG, "sizes": "any", "type": "image/svg+xml"},
            {"src": ICON_PNG, "sizes": f"{width}x{height}", "type": "image/png"},
        ],
    }


def problems(page, text):
    # dist/404.html is served at any depth, so it links from the root (.claude/rules/security.md).
    if page == DIST / "404.html":
        up = "/"
    else:
        up = "../" * (len(page.relative_to(DIST).parts) - 1)
    out = []
    if f'<link rel="manifest" href="{up}{MANIFEST.name}">' not in text:
        out.append("does not link the manifest")
    # tools/version_assets.py adds ?v=<hash> to the script link after the pages are written.
    script = re.compile(
        rf'<script src="{re.escape(up + REGISTER_SCRIPT)}(\?v=[0-9a-f]+)?"></script>'
    )
    if not script.search(text):
        out.append(f"does not load {REGISTER_SCRIPT}")
    return out


def check():
    bad = 0
    for path in (MANIFEST, SERVICE_WORKER, DIST / REGISTER_SCRIPT):
        if not path.is_file():
            bad += 1
            print(f"missing {path.relative_to(DIST.parent)}")
    count = 0
    for page in DIST.rglob("*.html"):
        count += 1
        for p in problems(page, page.read_text(encoding="utf-8")):
            bad += 1
            if bad <= 20:
                print(f"{page.relative_to(DIST)}: {p}")
    if bad:
        print(f"{bad} problems in {count} pages")
        return 1
    print(f"manifest and service worker linked from all {count} pages")
    return 0


def main(argv):
    if argv[1:] == ["--check"]:
        return check()
    if argv[1:]:
        print("usage: pwa.py [--check]", file=sys.stderr)
        return 2
    MANIFEST.write_text(json.dumps(manifest(), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
