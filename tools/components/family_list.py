"""The List view of the top page (dist/components/family-list/): the top-level records
under their continents. dist/components/explorer/explorer.js opens a row into its members
and hides the rows no matching language belongs to (data-root)."""

from html import escape


def family_row(root, href, name, native="", meta=""):
    """One top-level record: its name linked to its page, then its native names and its
    notes (`native`, `meta`: plain text, left out when empty)."""
    return (
        f'<li data-root="{escape(root)}"><a href="{escape(href)}">{escape(name)}</a>'
        + (f' <span class="native-inline" dir="auto">{escape(native)}</span>' if native else "")
        + (f' <span class="rowmeta">{escape(meta)}</span>' if meta else "")
        + "</li>"
    )


def continent_group(continent, rows):
    """A continent's heading and its rows (family_row()). A continent is a heading only."""
    return f'<div class="continent"><h3>{escape(continent)}</h3><ul class="record-links">{rows}</ul></div>'
