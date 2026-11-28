"""Script samples from free-licensed pictures, for the scripts no Noto font can draw yet.

tools/glyph_images.py draws most script samples from the Noto fonts. A few samples have a letter no
Noto font has (new scripts, and recent additions to old ones), so they get no drawing. For those the
owner chose (2026-11-27) a picture under a free license (Creative Commons or public domain) from
Wikimedia Commons, kept in the site and credited where it is shown.

- source-data/signs-and-scripts/pictures/ holds each picture as Commons published it, named after the record (<id>.<ext>), and pictures.json, the
  register: for each record the Commons file and, read from Commons, its author, license, size and
  SHA-256. The register is written by --add, never by hand; which file a record gets is the only
  choice a person makes.
- place() copies a record's picture to dist/glyphs/ (next to the drawn samples) and returns its
  address and size; source() gives the credit entry for the source register of
  tools/build_visual.py. The build never contacts Commons.
- A record that gets a drawing from the fonts never uses its picture.

Usage:
  build_visual.py imports load(), place() and source()
  python3 tools/glyph_pictures.py --add <record id> "File:<Commons file name>" <downloaded file>
      keep the original file (downloaded by hand; Wikimedia refuses many automated downloads)
      after checking it against Commons, and write its entry in the register
  python3 tools/glyph_pictures.py --check
      fail when a picture is missing or differs from its SHA-256 in the register
"""

import datetime
import hashlib
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from glyph_images import OUT
from locations import SOURCE_DATA

FOLDER = SOURCE_DATA / "signs-and-scripts" / "pictures"
REGISTER = FOLDER / "pictures.json"
API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks automated clients to name themselves.
USER_AGENT = "LangLogBuild/1.0 (https://lang-log.com/)"
# Seconds to wait when Wikimedia sends no Retry-After with a 429 answer.
RETRY_SECONDS = 60
TRIES = 10


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    """The body of url, waiting as long as Wikimedia asks when it limits the rate."""
    for _ in range(TRIES):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request) as answer:
                return answer.read()
        except urllib.error.HTTPError as error:
            if error.code != 429:
                raise
            time.sleep(int(error.headers.get("Retry-After") or RETRY_SECONDS))
    sys.exit(f"{url}: still rate-limited after {TRIES} tries")


def plain(html):
    """Text of a Commons metadata value, which may hold HTML."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def load():
    if not REGISTER.is_file():
        return {}
    return json.loads(REGISTER.read_text(encoding="utf-8"))["pictures"]


def add(record_id, title, local):
    """Copy a Commons file (downloaded by a person) into the folder and write its entry from Commons.

    The file must be the original Commons serves: its SHA-1 is checked against the one Commons
    gives, so a wrong or altered file is refused.
    """
    query = urllib.parse.urlencode(
        dict(
            action="query",
            format="json",
            prop="imageinfo",
            iiprop="url|size|sha1|extmetadata",
            titles=title,
        )
    )
    page = next(iter(json.loads(fetch(f"{API}?{query}"))["query"]["pages"].values()))
    info = page["imageinfo"][0]
    data = Path(local).read_bytes()
    if hashlib.sha1(data).hexdigest() != info["sha1"]:
        sys.exit(f"{local}: not the file Commons has for {page['title']} (SHA-1 differs)")
    meta = {k: plain(v["value"]) for k, v in info["extmetadata"].items()}
    path = f"{record_id}.{info['url'].rsplit('.', 1)[1].lower()}"
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER / path).write_bytes(data)
    pictures = load()
    pictures[record_id] = dict(
        file=page["title"],
        page=info["descriptionurl"],
        download=info["url"],
        author=meta.get("Artist", ""),
        credit=meta.get("Credit", ""),
        license=meta["LicenseShortName"],
        licenseUrl=meta.get("LicenseUrl", ""),
        retrieved=datetime.date.today().isoformat(),
        path=path,
        width=info["width"],
        height=info["height"],
        sha256=sha256(data),
    )
    note = (
        "Script sample pictures for records no Noto font can draw (tools/glyph_pictures.py). "
        "Written by --add from Wikimedia Commons; do not edit by hand. Each picture keeps "
        "its own license."
    )
    register = dict(note=note, pictures=dict(sorted(pictures.items())))
    REGISTER.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{record_id}: {page['title']} ({meta['LicenseShortName']})")


def check():
    problems = [
        f"{FOLDER / p['path']}: missing or differs from its SHA-256 in {REGISTER.name}"
        for p in load().values()
        if not (FOLDER / p["path"]).is_file()
        or sha256((FOLDER / p["path"]).read_bytes()) != p["sha256"]
    ]
    if problems:
        sys.exit("\n".join(problems))


def source_id(record_id):
    return f"picture-{record_id}"


def source(record_id, picture):
    """The credit entry for build_visual.py's source register (src())."""
    return dict(
        i=source_id(record_id),
        title=f"{picture['file'].removeprefix('File:')} · {picture['author']} · {picture['license']} · Wikimedia Commons",
        url=picture["page"],
        kind="script sample picture",
        license=picture["license"],
    )


def place(record_id, picture):
    """Copy a record's picture into dist/glyphs/; its address and size for the pages."""
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FOLDER / picture["path"], OUT / picture["path"])
    return {
        "src": f"glyphs/{picture['path']}",
        "width": picture["width"],
        "height": picture["height"],
    }


def main(argv):
    if argv[:1] == ["--add"] and len(argv) == 4:
        add(argv[1], argv[2], argv[3])
    elif argv == ["--check"]:
        check()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
