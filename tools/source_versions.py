"""The versions of the source datasets, read from source-data/sources.json.

Each version is written once, in source-data/sources.json; scripts import these
names instead of typing a version (.claude/rules/readable-code.md). Pages and
scripts in the browser read `glottologVersion` from dist/data.json, which
tools/build_data.py writes from here.
"""

import json

from locations import ROOT

_SOURCES = {
    s["id"]: s
    for s in json.loads((ROOT / "source-data" / "sources.json").read_text(encoding="utf-8"))[
        "sources"
    ]
}
GLOTTOLOG_VERSION = _SOURCES["glottolog"]["version"]
# The name and version as pages and exports show it, such as "Glottolog 5.3".
GLOTTOLOG = f"Glottolog {GLOTTOLOG_VERSION}"
# Unicode CLDR as the record pages credit it, such as "Unicode CLDR 49".
CLDR = f"{_SOURCES['cldr']['title']} {_SOURCES['cldr']['version']}"
# Each source's title, as record pages name it where they cite a value's source.
SOURCE_TITLES = {sid: s["title"] for sid, s in _SOURCES.items()}
