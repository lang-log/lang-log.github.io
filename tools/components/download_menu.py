"""The Download menu (dist/components/download-menu/): its button is always the map's
download symbol, never the word (the owner's rule, 2026-11-23)."""

import re
import sys
from html import escape

from components import COMPONENTS


def map_icon(name, cls=""):
    """One of the map buttons' symbols, drawn as icon() in dist/components/map/map.js draws it;
    the path is read from the constant `name` there (ICON_DOWNLOAD, ICON_OPEN ...), so it is
    written once. `cls`: a class for the svg."""
    m = re.search(name + r" = '([^']+)'", (COMPONENTS / "map" / "map.js").read_text())
    if not m:
        sys.exit(f"dist/components/map/map.js has no {name}")
    attrs = f' class="{escape(cls)}"' if cls else ""
    return (
        f'<svg{attrs} viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">'
        f'<path d="{escape(m[1])}" fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def download_icon():
    """The download symbol of the map's PNG button."""
    return map_icon("ICON_DOWNLOAD")


def download_menu(entries):
    """The menu, holding `entries` (HTML: one button or link per format)."""
    summary = f'<summary aria-label="Download" title="Download">{download_icon()}</summary>'
    return f'<details class="menu downloads">{summary}<div class="menu-panel">{entries}</div></details>'
