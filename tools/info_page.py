"""The shell of Lang Log's information pages: one place for their <head>, header and footer.

The Stats, Sources and Updates pages (tools/build_home.py, one level below the
root) and the Releases page (tools/build_releases.py, at the root) are written
with page(). `up` is the way from the page's folder back to dist/ ("../" for
dist/stats/index.html, "" for dist/releases.html), so every link stays relative.
"""

from html import escape

from security_policy import HEAD as SECURITY_HEAD
from site_brand import COPYRIGHT, TITLE_SUFFIX, by_yoshi


def page(title, body, up, scripts=()):
    """The whole HTML of an information page. `body` is already escaped HTML; `scripts`
    are extra files from dist/ loaded in <head> after lang.js."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        + SECURITY_HEAD
        + '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}{TITLE_SUFFIX}</title>"
        f'<link rel="icon" href="{up}favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{up}apple-touch-icon.png">'
        f'<link rel="stylesheet" href="{up}style.css">'
        f'<script src="{up}theme.js"></script><script src="{up}i18n.js"></script><script src="{up}lang.js"></script>'
        + "".join(f'<script src="{up}{escape(s)}"></script>' for s in scripts)
        + '</head><body class="info-page">\n'
        f'<header><div class="brand"><a class="home" href="{up or "./"}"><svg class="logo" role="img" aria-label="LANG LOG"><use href="{up}logo.svg#logo"/></svg></a> '
        + by_yoshi()
        + "</div></header>\n"
        f'<main class="info-main"><h1>{escape(title)}</h1>{body}</main>\n'
        f"<footer><span>{COPYRIGHT}</span></footer>\n"
        "</body></html>\n"
    )
