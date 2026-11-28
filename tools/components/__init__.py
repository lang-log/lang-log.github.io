"""Lang Log's UI components, one directory each (the owner's request, 2026-11-27).

A component's look and behaviour live in dist/components/<name>/: <name>.css, and
<name>.js when it has a script. When the build writes its markup, the function that
writes it is in tools/components/<name>.py. Pages and generators only call them; a
change to a component is made there once and reaches every page
(.claude/rules/ui-design.md, docs/components.md).

Every page loads style.css (colour tokens, fonts, the defaults of plain elements and the
layout of the pages) and then every component's stylesheet, in STYLES order, through
stylesheets(). The order is the cascade order: a later stylesheet wins over an earlier
one at the same specificity. The generators call stylesheets(); the hand-written pages in
dist/*.html carry the same tags, kept equal by tools/check_components.py.
"""

from html import escape

from locations import DIST

COMPONENTS = DIST / "components"

# Every component with a stylesheet, in cascade order.
STYLES = [
    "header",
    "tree",
    "footer",
    "view-switch",
    "download-menu",
    "hf-models",
    "atlas-menu",
    "breadcrumb",
    "big-logo",
    "search-box",
    "theme-toggle",
    "language-menu",
    "random-row",
    "search-results",
    "page-section",
    "family-list",
    "guide-row",
    "figures",
    "release-list",
    "source-credit",
    "map",
    "data-table",
    "conditions-panel",
    "list-view",
]


def asset(name, ext, up=""):
    """The address of a component's file, relative to a page `up` folders below the root
    ("../../"), or "/" for dist/404.html, which is served at any depth."""
    return f"{up}components/{name}/{name}.{ext}"


def stylesheets(up=""):
    """The <link> tags of style.css and of every component's stylesheet, in cascade order."""
    return f'<link rel="stylesheet" href="{escape(up)}style.css">' + "".join(
        f'<link rel="stylesheet" href="{escape(asset(n, "css", up))}">' for n in STYLES
    )


def script(name, up="", attrs=""):
    """The <script> tag of a component's script."""
    return f'<script src="{escape(asset(name, "js", up))}"{attrs}></script>'
