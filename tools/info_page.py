"""The shell of Lang Log's information pages: one place for their <head>, header and footer.

The Stats and Sources pages (tools/build_home.py, one level below the
root) and the Releases page (tools/build_releases.py, at the root) are written
with page(). `up` is the way from the page's folder back to dist/ ("../" for
dist/stats/index.html, "" for dist/releases.html), so every link stays relative.
"""

from html import escape

from components import script, stylesheets
from components.footer import footer
from components.header import header
from pwa import head_tags as pwa_head
from security_policy import HEAD as SECURITY_HEAD
from site_brand import (
    SITE_NAME_META,
    TITLE_SUFFIX,
    icon_links,
)


def page(title, body, up, scripts=()):
    """The whole HTML of an information page. `body` is already escaped HTML; `scripts`
    are extra files from dist/ loaded in <head> after the language menu's script."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        + SECURITY_HEAD
        + '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}{TITLE_SUFFIX}</title>"
        + icon_links(up)
        + SITE_NAME_META
        + pwa_head(up)
        + stylesheets(up)
        + script("theme-toggle", up)
        + f'<script src="{up}i18n.js"></script>'
        + script("language-menu", up)
        + "".join(f'<script src="{up}{escape(s)}"></script>' for s in scripts)
        + '</head><body class="info-page">\n'
        + header(up or "./", up)
        + "\n"
        f'<main class="info-main"><h1>{escape(title)}</h1>{body}</main>\n' + footer() + "\n"
        "</body></html>\n"
    )
