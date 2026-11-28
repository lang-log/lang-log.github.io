"""The page header (dist/components/header/): the logo linking to the top page, then
"by yoshi". dist/components/theme-toggle/ and dist/components/language-menu/ add their
controls after it."""

from html import escape

from site_brand import by_yoshi


def header(home, up="", current=False):
    """The header of a page `up` folders below the root ("../"); `home` is the top page's
    address from there, and `current` marks the top page itself."""
    mark = ' aria-current="page"' if current else ""
    return (
        f'<header><div class="brand"><a class="home" href="{escape(home)}"{mark}>'
        f'<svg class="logo" role="img" aria-label="LANG LOG"><use href="{escape(up)}logo.svg#logo"/></svg></a> '
        f"{by_yoshi()}</div></header>"
    )
