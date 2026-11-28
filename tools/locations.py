"""Where the repository and its folders are: one place for every script in tools/.

Scripts import these instead of working the paths out again, so moving a folder
changes one line. Paths are absolute, so a script works from any directory.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
# The sources as they were published (source-data/sources.json lists them).
SOURCE_DATA = ROOT / "source-data"
# The language menu script: its LANGS table lists the interface languages, and
# tools/version_assets.py writes the dictionary versions into it.
LANG_JS = DIST / "components" / "language-menu" / "language-menu.js"
